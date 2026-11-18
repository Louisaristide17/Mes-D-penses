from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DATABASE_URL_HELP = (
    "DATABASE_URL invalide. Elle doit commencer par postgresql:// (ou sqlite:// en local), "
    "sans espace, sans guillemets et sans la commande psql devant. Exemple : "
    "postgresql://utilisateur:motdepasse@hote/base?sslmode=require"
)


def _unwrap(value: str) -> str:
    """Retire ce qu'un copier-coller ajoute souvent autour d'une valeur : espaces, guillemets."""
    text = value.strip()
    while len(text) >= 2 and text[0] == text[-1] and text[0] in "'\"":
        text = text[1:-1].strip()
    return text


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        str_strip_whitespace=True,
        # Une erreur de configuration ne doit jamais recopier un mot de passe ou une clé dans les journaux.
        hide_input_in_errors=True,
    )

    database_url: str = "sqlite:///./mes_depenses.db"
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 30
    refresh_token_days: int = 30
    cors_origins: str = "http://localhost:5173"
    model_path: str = "models/categorizer.joblib"
    groq_api_key: str = ""
    groq_model: str = "openai/gpt-oss-120b"
    groq_base_url: str = "https://api.groq.com/openai/v1"

    @field_validator("database_url", mode="before")
    @classmethod
    def normalize_database_url(cls, value: object) -> str:
        text = _unwrap(str(value))
        # Neon propose aussi la commande complète : psql 'postgresql://...'
        if text.lower().startswith("psql "):
            text = _unwrap(text[5:])
        if text.startswith("sqlite"):
            return text
        # Render et Heroku fournissent une URL "postgres://" que SQLAlchemy ne reconnaît pas,
        # et "postgresql://" désignerait le pilote psycopg2, qui n'est pas installé.
        for prefix in ("postgres://", "postgresql://", "postgresql+psycopg://"):
            if text.startswith(prefix) and "@" in text:
                return "postgresql+psycopg://" + text[len(prefix):]
        raise ValueError(DATABASE_URL_HELP)

    @field_validator("jwt_secret", "groq_api_key", mode="before")
    @classmethod
    def strip_quotes(cls, value: object) -> str:
        return _unwrap(str(value))

    @field_validator("jwt_secret")
    @classmethod
    def check_secret_length(cls, value: str) -> str:
        if len(value) < 32 or " " in value:
            raise ValueError(
                "JWT_SECRET doit être une clé d'au moins 32 caractères, sans espace. "
                "Générez-la avec : python -c \"import secrets; print(secrets.token_urlsafe(48))\""
            )
        return value

    @property
    def cors_origin_list(self) -> list[str]:
        """Origines autorisées, au format exact qu'envoie le navigateur : schéma, hôte, sans barre finale."""
        origins = []
        for raw in self.cors_origins.split(","):
            origin = _unwrap(raw).rstrip("/")
            if not origin:
                continue
            if "://" not in origin:
                origin = "https://" + origin
            origins.append(origin)
        return origins


@lru_cache
def get_settings() -> Settings:
    return Settings()
