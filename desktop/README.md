# Mes Dépenses - Application desktop

Application de bureau en Python et PySide6 (Qt 6). Elle consomme l'API du dossier `api`.

## Installation

Python 3.11 ou plus récent, et l'API lancée sur `http://localhost:8000`.

```powershell
cd desktop
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements-dev.txt
.venv\Scripts\python main.py
```

Sous Linux ou macOS, remplacez `.venv\Scripts\python` par `.venv/bin/python`.

Compte de démonstration : `awa.kone@example.com` / `demonstration-2026`.

## Configuration

| Variable d'environnement | Rôle | Valeur par défaut |
|---|---|---|
| `MES_DEPENSES_API_URL` | Adresse de l'API, sans `/api/v1` | `http://localhost:8000` |

Exemple avec une API déployée, dans PowerShell :

```powershell
$env:MES_DEPENSES_API_URL = "https://votre-api.onrender.com"
.venv\Scripts\python main.py
```

## Tests

```powershell
.venv\Scripts\python -m pytest
```

Les tests couvrent la mise en forme des montants et des dates, les calculs des graphiques et le client HTTP (connexion, renouvellement des jetons, messages d'erreur), sans réseau ni fenêtre.

## Architecture

```
main.py              Point d'entrée
app/
  config.py          Adresse de l'API, constantes
  api.py             Client HTTP : jetons, renouvellement automatique, messages d'erreur
  tasks.py           Exécution des appels réseau hors du fil de l'interface
  theme.py           Design system : couleurs, police, icônes, feuille de style Qt
  format.py          Montants, dates et mois
  widgets.py         Composants partagés : carte, message, sélecteur de mois, fenêtre de formulaire
  charts.py          Histogramme mensuel et anneau de répartition (QPainter)
  dialogs.py         Formulaires de dépense et de budget
  main_window.py     Fenêtre principale : barre latérale, navigation, session
  pages/             Connexion, tableau de bord, dépenses, budgets, assistant, profil
  assets/            Police Inter et icônes Lucide, avec leurs licences
tests/
```

## Écrans

- **Connexion et création de compte.**
- **Tableau de bord** : total du mois et variation, alertes de budget, évolution sur six mois, répartition par catégorie, dernières dépenses.
- **Dépenses** : recherche, filtres par période et par catégorie, ajout, modification (bouton ou double-clic), suppression, import CSV, exports CSV et PDF.
- **Budgets** : plafond par catégorie et par mois, avec niveau de consommation.
- **Assistant** : questions sur les dépenses et les budgets, ajout d'une dépense par une phrase, questions générales. Chaque réponse indique les données dont elle est tirée.
- **Profil** : nom, e-mail, mot de passe, déconnexion.

La gestion des catégories personnelles se fait sur le site web. Les catégories créées y apparaissent ici.

## Choix techniques

- **Interface jamais figée.** Un appel réseau dans le fil principal bloquerait la fenêtre. `tasks.py` envoie chaque appel dans le pool de fils de Qt et renvoie le résultat par un signal, délivré dans le fil de l'interface.
- **Réponses périmées ignorées.** Quand l'utilisateur tape vite ou change de mois, plusieurs requêtes se croisent. Chaque écran numérote ses requêtes et n'affiche que la réponse à la plus récente.
- **Session dans le coffre du système.** Les jetons sont confiés à `keyring`, c'est-à-dire au Gestionnaire d'identification de Windows, et non écrits dans un fichier. Si le coffre est indisponible, l'application fonctionne mais redemande la connexion au lancement suivant.
- **Renouvellement protégé par un verrou.** Plusieurs fils peuvent recevoir un 401 en même temps : un seul renouvelle la session, les autres réutilisent le nouveau jeton.
- **Même design system que le web.** `theme.py` reprend la palette, le rayon de 8 px, la police Inter et les icônes Lucide, embarquées dans `assets/` pour fonctionner sans connexion.
- **Graphiques dessinés avec QPainter.** Deux graphiques simples ne justifient pas une bibliothèque. Une infobulle donne le montant au survol.

## Créer un exécutable Windows

```powershell
.venv\Scripts\python -m pip install pyinstaller
.venv\Scripts\python -m PyInstaller --noconsole --name MesDepenses --add-data "app\assets;app\assets" main.py
```

L'application se trouve ensuite dans `dist\MesDepenses\MesDepenses.exe`. Pour qu'elle pointe vers l'API déployée, définissez `MES_DEPENSES_API_URL` sur le poste, ou modifiez la valeur par défaut dans `app/config.py` avant de construire l'exécutable.

## Licences des ressources embarquées

- Police Inter : SIL Open Font License, voir `app/assets/fonts/LICENSE-Inter.txt`.
- Icônes Lucide : licence ISC, voir `app/assets/icons/LICENSE-Lucide.txt`.
