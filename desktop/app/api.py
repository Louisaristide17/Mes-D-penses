"""Client HTTP de l'API Mes Dépenses.

Les appels sont bloquants : l'interface les lance dans des fils d'exécution
séparés (voir tasks.py), d'où le verrou autour du renouvellement des jetons.
"""

import json
import logging
import re
import threading

import requests

logger = logging.getLogger(__name__)

TIMEOUT = 20
# L'assistant enchaîne plusieurs appels au modèle de langage : sa réponse peut prendre plus longtemps.
ASSISTANT_TIMEOUT = 60
KEYRING_SERVICE = "mes-depenses"
KEYRING_USER = "session"


class ApiError(Exception):
    def __init__(self, message: str, status: int = 0):
        super().__init__(message)
        self.message = message
        self.status = status


class TokenStore:
    """Conserve les jetons dans le coffre du système (Gestionnaire d'identification sous Windows)."""

    def load(self) -> dict | None:
        try:
            import keyring

            raw = keyring.get_password(KEYRING_SERVICE, KEYRING_USER)
            return json.loads(raw) if raw else None
        except Exception:
            logger.warning("Coffre du système indisponible : la session ne sera pas conservée")
            return None

    def save(self, tokens: dict) -> None:
        try:
            import keyring

            keyring.set_password(KEYRING_SERVICE, KEYRING_USER, json.dumps(tokens))
        except Exception:
            logger.warning("Coffre du système indisponible : la session ne sera pas conservée")

    def clear(self) -> None:
        try:
            import keyring

            keyring.delete_password(KEYRING_SERVICE, KEYRING_USER)
        except Exception:
            pass


class MemoryTokenStore(TokenStore):
    """Variante sans persistance, utilisée par les tests."""

    def __init__(self):
        self.tokens = None

    def load(self):
        return self.tokens

    def save(self, tokens):
        self.tokens = tokens

    def clear(self):
        self.tokens = None


class ApiClient:
    def __init__(self, base_url: str, store: TokenStore | None = None, http: requests.Session | None = None):
        self.base_url = f"{base_url}/api/v1"
        self.store = store or TokenStore()
        self.http = http or requests.Session()
        self.on_session_expired = lambda: None
        self._access: str | None = None
        self._refresh: str | None = None
        self._lock = threading.Lock()

    # Session

    @property
    def has_session(self) -> bool:
        return self._access is not None

    def restore_session(self) -> None:
        tokens = self.store.load()
        if tokens:
            self._access, self._refresh = tokens.get("access"), tokens.get("refresh")

    def _set_tokens(self, data: dict) -> None:
        self._access, self._refresh = data["access_token"], data["refresh_token"]
        self.store.save({"access": self._access, "refresh": self._refresh})

    def clear_session(self) -> None:
        self._access = self._refresh = None
        self.store.clear()

    # Transport

    def _send(self, method: str, path: str, token: str | None, **kwargs) -> requests.Response:
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        try:
            timeout = ASSISTANT_TIMEOUT if path.startswith("/assistant/") else TIMEOUT
            return self.http.request(method, self.base_url + path, headers=headers, timeout=timeout, **kwargs)
        except requests.RequestException as exc:
            raise ApiError("Connexion au serveur impossible. Vérifiez que l'API est démarrée.") from exc

    def _renew(self, stale_token: str) -> bool:
        with self._lock:
            # Un autre fil a peut-être déjà renouvelé la session pendant l'attente du verrou.
            if self._access and self._access != stale_token:
                return True
            if not self._refresh:
                return False
            try:
                response = self.http.post(
                    f"{self.base_url}/auth/refresh", json={"refresh_token": self._refresh}, timeout=TIMEOUT
                )
            except requests.RequestException:
                return False
            if response.status_code != 200:
                return False
            self._set_tokens(response.json())
            return True

    @staticmethod
    def _error(response: requests.Response) -> ApiError:
        message = "Une erreur est survenue. Réessayez dans un instant."
        if response.status_code == 422:
            message = "Certaines informations sont invalides. Vérifiez le formulaire."
        else:
            try:
                detail = response.json().get("detail")
                if isinstance(detail, str):
                    message = detail
            except (ValueError, AttributeError):
                pass
        return ApiError(message, response.status_code)

    def _request(self, method: str, path: str, **kwargs) -> requests.Response:
        token = self._access
        response = self._send(method, path, token, **kwargs)
        if response.status_code == 401 and token and not path.startswith("/auth/"):
            if not self._renew(token):
                self.clear_session()
                self.on_session_expired()
                raise ApiError("Votre session a expiré. Veuillez vous reconnecter.", 401)
            response = self._send(method, path, self._access, **kwargs)
        if not response.ok:
            raise self._error(response)
        return response

    def _json(self, method: str, path: str, **kwargs):
        response = self._request(method, path, **kwargs)
        return response.json() if response.content else None

    @staticmethod
    def _clean(params: dict) -> dict:
        return {key: value for key, value in params.items() if value not in (None, "")}

    # Comptes

    def login(self, email: str, password: str) -> dict:
        data = self._json("POST", "/auth/login", json={"email": email, "password": password})
        self._set_tokens(data)
        return data["user"]

    def register(self, name: str, email: str, password: str) -> dict:
        data = self._json("POST", "/auth/register", json={"name": name, "email": email, "password": password})
        self._set_tokens(data)
        return data["user"]

    def profile(self) -> dict:
        return self._json("GET", "/users/me")

    def update_profile(self, name: str, email: str) -> dict:
        return self._json("PATCH", "/users/me", json={"name": name, "email": email})

    def change_password(self, current: str, new: str) -> None:
        self._json("POST", "/users/me/password", json={"current_password": current, "new_password": new})

    # Catégories et dépenses

    def categories(self) -> list[dict]:
        return self._json("GET", "/categories")

    def expenses(self, **filters) -> dict:
        return self._json("GET", "/expenses", params=self._clean(filters))

    def create_expense(self, payload: dict) -> dict:
        return self._json("POST", "/expenses", json=payload)

    def update_expense(self, expense_id: int, payload: dict) -> dict:
        return self._json("PATCH", f"/expenses/{expense_id}", json=payload)

    def delete_expense(self, expense_id: int) -> None:
        self._json("DELETE", f"/expenses/{expense_id}")

    def suggest_category(self, note: str) -> dict:
        return self._json("POST", "/expenses/suggest-category", json={"note": note})

    def import_expenses(self, path: str) -> dict:
        with open(path, "rb") as handle:
            return self._json("POST", "/expenses/import", files={"file": ("depenses.csv", handle, "text/csv")})

    def export_expenses(self, file_format: str, **filters) -> tuple[str, bytes]:
        """Renvoie le nom de fichier proposé par l'API et le contenu de l'export."""
        response = self._request("GET", f"/exports/expenses.{file_format}", params=self._clean(filters))
        match = re.search(r'filename="([^"]+)"', response.headers.get("Content-Disposition", ""))
        return (match.group(1) if match else f"mes-depenses.{file_format}"), response.content

    # Budgets et tableau de bord

    def budget_statuses(self, month: str) -> list[dict]:
        return self._json("GET", "/budgets/status", params={"month": month})

    def set_budget(self, category_id: int, month: str, ceiling: int) -> dict:
        return self._json("PUT", "/budgets", json={"category_id": category_id, "month": month, "ceiling": ceiling})

    def delete_budget(self, budget_id: int) -> None:
        self._json("DELETE", f"/budgets/{budget_id}")

    def dashboard(self, month: str) -> dict:
        return self._json("GET", "/dashboard/summary", params={"month": month})

    # Assistant

    def ask_assistant(self, message: str, conversation_id: int | None = None) -> dict:
        payload = {"message": message}
        if conversation_id is not None:
            payload["conversation_id"] = conversation_id
        return self._json("POST", "/assistant/messages", json=payload)
