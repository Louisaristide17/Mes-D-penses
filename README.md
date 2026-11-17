# Mes Dépenses

Application de suivi des dépenses personnelles, pensée pour la Côte d'Ivoire : montants en francs CFA, catégories et libellés locaux. Elle existe en trois versions, site web, application Android et application de bureau, qui partagent une même API, une même base de données et un même design system.

Projet réalisé pour la soutenance de la formation Développeur Data IA (Simplon Côte d'Ivoire).

## Architecture

```
 Site web            Application mobile       Application desktop
 React + Vite        Flutter (Android)        Python + PySide6
      \                     |                        /
       \____________ HTTPS / JSON (JWT) ____________/
                            |
                    API REST FastAPI
        ┌───────────────┬───────────────┬───────────────┐
        Routes métier    Modèle de        Agent IA
        (dépenses,       catégorisation   (modèle de langage
        budgets,         (scikit-learn)   + outils)
        exports)
        └───────────────┴───────┬───────┴───────────────┘
                                |
                     PostgreSQL (SQLite en local)
```

| Dossier | Contenu | Documentation |
|---|---|---|
| `api/` | API, base de données, modèle, agent | `api/README.md`, `api/ml/README.md` |
| `web/` | Site web | `web/README.md` |
| `mobile/` | Application Android | `mobile/README.md` |
| `desktop/` | Application de bureau | `desktop/README.md` |

## Lancement en local

Chaque composant se lance dans son propre terminal. L'API doit tourner en premier.

```powershell
# Terminal 1 : API
cd api
.venv\Scripts\python -m uvicorn app.main:app --reload --host 0.0.0.0

# Terminal 2 : site web, sur http://localhost:5173
cd web
npm.cmd run dev

# Terminal 3 : application de bureau
cd desktop
.venv\Scripts\python main.py

# Terminal 4 : application mobile
cd mobile
flutter run --dart-define=API_URL=http://<adresse IP du PC>:8000
```

Compte de démonstration : `awa.kone@example.com` / `demonstration-2026`.

## Correspondance avec la grille d'évaluation

| Bloc | Points | Ce qui le couvre | Où le montrer |
|---|---|---|---|
| Données | 25 | Constitution d'un jeu de 9 855 libellés à partir de 657 libellés de base ; nettoyage en quatre étapes ; exploration ; modèle relationnel à sept tables avec migrations ; import CSV avec rapport des lignes rejetées | `api/ml/vocabulary.py`, `build_dataset.py`, `prepare.py` ; sections 1 à 3 du notebook ; `api/app/models.py` ; `api/migrations/` |
| Entraînement de modèle | 25 | Cinq modèles comparés par validation croisée par groupes ; trois mesures d'évaluation ; matrice de confusion ; analyse des erreurs ; choix du seuil de confiance ; réentraînement à partir des corrections | `api/ml/train.py` ; sections 4 à 9 du notebook ; `api/ml/reports/` |
| Développement web, mobile et desktop | 30 | API REST documentée (OpenAPI), authentification par jetons, 65 tests ; trois clients partageant le même design system ; tableau de bord, budgets avec alertes, exports CSV et PDF | `http://localhost:8000/docs` ; démonstration des trois applications ; `api/tests/` |
| Création d'un agent IA | 25 | Agent à cinq outils avec appel de fonctions ; validation des arguments ; cloisonnement par utilisateur ; limite d'allers-retours ; historique des conversations | `api/app/services/agent.py`, `llm.py` ; `api/tests/test_assistant.py` |
| Intégration de l'IA dans une application | 25 | Catégorie suggérée à la saisie, avec niveau de confiance, dans les trois clients ; onglet Assistant dans les trois clients, avec indication des données utilisées ; enregistrement des corrections pour améliorer le modèle | Formulaire « Nouvelle dépense » ; onglet Assistant ; table `predictions` |

Ce tableau s'appuie sur les intitulés des cinq blocs. Il est à affiner critère par critère avec la grille détaillée.

## Limites connues

- **Données d'entraînement synthétiques.** Les libellés ont été rédigés puis déclinés automatiquement, faute d'historique réel. Les mesures du modèle (90 % sur un jeu de 120 libellés rédigés à la main, score légèrement favorable car ce jeu recoupe en partie le vocabulaire) devront être confirmées sur des données d'usage.
- **Vocabulaire inconnu.** Le modèle ne reconnaît pas un libellé dont le mot principal est absent de son vocabulaire (52 % sur des libellés de base jamais vus).
- **Réponses générales non vérifiées.** Pour les questions qui ne portent pas sur les données de l'utilisateur, l'assistant répond à partir des connaissances du modèle de langage, sans accès à internet : il peut se tromper ou donner une information dépassée.
- **Assistant dépendant d'un service externe.** Les réponses sont produites par un modèle hébergé chez Groq : elles demandent une connexion, et les questions ainsi que les chiffres utilisés quittent le serveur.
- **Fonctions absentes sur mobile et desktop.** L'import CSV et les exports ne sont pas disponibles sur mobile ; les catégories personnelles se gèrent sur le site web.
- **Déploiement.** Le projet a été testé en local. La procédure de déploiement sur Render est décrite dans `api/README.md` mais n'a pas été exécutée.
