import os

# Adresse de l'API, sans le suffixe /api/v1. Se règle par variable d'environnement.
API_URL = os.environ.get("MES_DEPENSES_API_URL", "https://mes-d-penses-api.onrender.com").rstrip("/")

APP_NAME = "Mes Dépenses"
PAGE_SIZE = 20
