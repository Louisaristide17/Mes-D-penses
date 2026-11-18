# Mes Dépenses - API

API REST commune au site web, à l'application mobile et à l'application desktop.
Elle porte toute la logique métier : comptes, dépenses, budgets, tableau de bord, exports et proposition automatique de catégorie.

## Installation

Python 3.11 ou plus récent.

```bash
python -m venv .venv
source .venv/bin/activate          # Windows : .venv\Scripts\activate
pip install -r requirements-dev.txt
cp .env.example .env               # puis renseigner JWT_SECRET
alembic upgrade head               # crée les tables
python -m scripts.seed_demo        # facultatif : compte et données de démonstration
uvicorn app.main:app --reload
```

- Documentation interactive : http://localhost:8000/docs
- Schéma OpenAPI : http://localhost:8000/openapi.json
- Compte de démonstration : `awa.kone@example.com` / `demonstration-2026` (à ne pas créer en production)

## Configuration

Toutes les valeurs se règlent par variables d'environnement ou dans le fichier `.env`.

| Variable | Rôle | Valeur par défaut |
|---|---|---|
| `DATABASE_URL` | Base de données. SQLite en local, PostgreSQL en production | `sqlite:///./mes_depenses.db` |
| `JWT_SECRET` | Clé de signature des jetons, 32 caractères au minimum | obligatoire |
| `ACCESS_TOKEN_MINUTES` | Durée de vie du jeton d'accès | 30 |
| `REFRESH_TOKEN_DAYS` | Durée de vie du jeton de rafraîchissement | 30 |
| `CORS_ORIGINS` | Origines autorisées pour le site web, séparées par des virgules | `http://localhost:5173` |
| `MODEL_PATH` | Fichier du modèle de catégorisation | `models/categorizer.joblib` |
| `GROQ_API_KEY` | Clé du fournisseur du modèle de langage. Sans clé, l'assistant est désactivé | vide |
| `GROQ_MODEL` | Modèle de langage utilisé par l'assistant | `openai/gpt-oss-120b` |

## Architecture

```
app/
  main.py            Application FastAPI, CORS, enregistrement des routes
  config.py          Lecture de la configuration
  database.py        Moteur SQLAlchemy et session
  models.py          Tables
  schemas.py         Schémas d'entrée et de sortie (validation)
  security.py        Hachage des mots de passe, jetons JWT
  deps.py            Dépendances partagées (session, utilisateur connecté)
  routers/           Une route par domaine : auth, users, categories, expenses, budgets, dashboard, exports
  services/          Logique métier, indépendante de HTTP (dont agent.py et llm.py pour l'assistant)
migrations/          Migrations Alembic
scripts/seed_demo.py Données de démonstration
ml/                  Jeu de données, entraînement et notebook du modèle (voir ml/README.md)
tests/               Tests pytest
```

Les routes restent fines : elles valident, appellent un service et renvoient un schéma. La logique réutilisable (création d'une dépense, calcul des budgets, exports) vit dans `services/`, ce qui permettra à l'agent IA d'appeler les mêmes fonctions.

## Routes

Toutes les routes sont préfixées par `/api/v1` et, hors authentification, exigent l'en-tête `Authorization: Bearer <jeton d'accès>`.

| Méthode | Route | Rôle |
|---|---|---|
| POST | `/auth/register`, `/auth/login`, `/auth/refresh` | Inscription, connexion, renouvellement du jeton |
| GET, PATCH | `/users/me` | Lecture et modification du profil |
| POST | `/users/me/password` | Changement de mot de passe |
| GET, POST | `/categories` | Catégories par défaut et personnelles |
| PATCH, DELETE | `/categories/{id}` | Modification d'une catégorie personnelle |
| GET, POST | `/expenses` | Liste filtrée et paginée, ajout |
| GET, PATCH, DELETE | `/expenses/{id}` | Lecture, modification, suppression |
| POST | `/expenses/suggest-category` | Catégorie proposée pour un libellé |
| POST | `/expenses/import` | Import d'un fichier CSV |
| GET, PUT | `/budgets` | Budgets du mois, création ou remplacement |
| GET | `/budgets/status` | Consommation de chaque budget et niveau d'alerte |
| DELETE | `/budgets/{id}` | Suppression d'un budget |
| GET | `/dashboard/summary` | Total du mois, répartition, évolution, alertes |
| GET | `/exports/expenses.csv`, `/exports/expenses.pdf` | Exports |
| GET | `/model` | Moteur de catégorisation en service et mesures du dernier entraînement |
| POST | `/assistant/messages` | Question à l'assistant, dans une conversation nouvelle ou existante |
| GET | `/assistant/conversations` | Conversations de l'utilisateur |
| GET, DELETE | `/assistant/conversations/{id}` | Lecture et suppression d'une conversation |

## Choix techniques

- **Montants entiers.** Les montants sont stockés en francs CFA, sans décimales, pour éviter toute erreur d'arrondi.
- **Deux jetons.** Le jeton d'accès est court (30 minutes), le jeton de rafraîchissement long (30 jours). Chacun porte son type : un jeton de rafraîchissement est refusé sur une route protégée.
- **Cloisonnement.** Chaque requête filtre sur l'utilisateur connecté. Une ressource appartenant à un autre compte répond 404, comme si elle n'existait pas.
- **Catégorisation.** `services/categorizer.py` charge le modèle scikit-learn s'il est présent et retient sa proposition quand sa confiance atteint 0,35. Sinon, des règles par mots-clés prennent le relais. Le modèle se construit avec `python -m ml.train` ; la démarche et les résultats sont dans `ml/README.md`.
- **Table `predictions`.** Chaque proposition est enregistrée avec la catégorie finalement retenue. L'écart entre les deux mesure la qualité du modèle en conditions réelles et fournit des exemples pour le réentraîner.
- **Assistant.** `services/agent.py` fait dialoguer un modèle de langage et cinq outils. L'assistant traite deux sortes de demandes : celles qui portent sur les données de l'utilisateur, pour lesquelles tout chiffre doit venir d'un outil, et les questions générales, auxquelles il répond à partir de ses connaissances, sans accès à internet. Les cinq outils : total, répartition par catégorie, liste des dépenses, état des budgets, ajout d'une dépense. Le modèle ne voit jamais la base : il demande l'appel d'un outil, l'API valide les arguments avec Pydantic puis exécute la fonction pour l'utilisateur connecté. Quatre garde-fous :
  - l'identité de l'utilisateur vient de sa session, jamais des arguments fournis par le modèle ;
  - l'agent peut lire et ajouter, mais ni modifier ni supprimer ;
  - le nombre d'allers-retours avec le modèle est limité à six par question ;
  - si le fournisseur tombe en panne en cours de route, rien n'est enregistré, pas même une dépense déjà créée par l'agent.
- **Fournisseur du modèle de langage.** `services/llm.py` appelle l'interface « chat completions » de Groq, compatible OpenAI. Le modèle se change par la variable `GROQ_MODEL`, sans toucher au code : Groq retire régulièrement des modèles de son catalogue.
- **Niveaux de budget.** `ok` en dessous de 80 % du plafond, `attention` de 80 à 100 %, `depasse` au-delà.

## Import CSV

Colonnes `date` et `montant` obligatoires, `note` et `categorie` facultatives. Séparateur virgule ou point-virgule, dates au format `AAAA-MM-JJ` ou `JJ/MM/AAAA`, 2 Mo et 5 000 lignes au maximum. Les lignes invalides sont ignorées et signalées dans la réponse avec leur numéro.

```
date;montant;note;categorie
2026-11-02;15000;Marché de Treichville;Alimentation
03/11/2026;1000;Recharge MTN;
```

## Tests

```bash
pytest
```

Les tests utilisent une base SQLite en mémoire, recréée à chaque test.

## Déploiement

L'API en ligne tourne sur Render, avec une base PostgreSQL hébergée chez Neon.

**Base de données (Neon).** Créer un projet dans la région Francfort, puis copier la chaîne de connexion directe (option « Connection pooling » désactivée, format « Connection string »).

**Service web (Render).**

| Réglage | Valeur |
|---|---|
| Root Directory | `api` |
| Build Command | `pip install -r requirements.txt && python -m ml.train` |
| Start Command | `alembic upgrade head && python -m scripts.seed_demo && uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
| Health Check Path | `/health` |

Le modèle est entraîné pendant la construction, avec la version de scikit-learn qui le servira ensuite.

**Variables d'environnement.** `PYTHON_VERSION` (`3.13.5`), `DATABASE_URL`, `JWT_SECRET`, `GROQ_API_KEY`, `GROQ_MODEL` et `CORS_ORIGINS` (adresse du site web). La configuration tolère les erreurs de copier-coller courantes (espaces, guillemets, commande `psql` devant l'adresse) et, en cas de valeur invalide, affiche un message explicite sans jamais recopier de secret dans les journaux.

**À savoir.** Une variable modifiée n'est prise en compte qu'au déploiement suivant. Si un déploiement échoue, Render continue de servir la version précédente, avec ses anciennes variables.

## Activer l'assistant

1. Créer une clé gratuite sur https://console.groq.com, rubrique API Keys.
2. L'ajouter dans `.env` : `GROQ_API_KEY=gsk_...`
3. Redémarrer l'API.

Sans clé, la route de l'assistant répond 503 avec un message explicite et le reste de l'application fonctionne normalement. Les questions posées à l'assistant et les résultats des outils sont envoyés à Groq pour produire la réponse : c'est le seul endroit où des données de dépenses quittent le serveur.
