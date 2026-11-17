import os

# Adresse de l'API, sans le suffixe /api/v1. Se règle par variable d'environnement.
API_URL = os.environ.get("MES_DEPENSES_API_URL", "http://localhost:8000").rstrip("/")

APP_NAME = "Mes Dépenses"
PAGE_SIZE = 20
