# Mes Dépenses - Site web

Client web de l'application Mes Dépenses, en React et Vite. Il consomme l'API du dossier `api`.

## Installation

Node.js 20 ou plus récent, et l'API lancée sur `http://localhost:8000`.

```bash
npm install
cp .env.example .env      # Windows : copy .env.example .env
npm run dev
```

Le site s'ouvre sur http://localhost:5173. Avec les données de démonstration de l'API, connectez-vous avec `awa.kone@example.com` / `demonstration-2026`.

| Commande | Rôle |
|---|---|
| `npm run dev` | Serveur de développement |
| `npm run build` | Version de production dans `dist/` |
| `npm run preview` | Sert la version de production en local |
| `npm test` | Tests unitaires (Vitest) |

## Configuration

| Variable | Rôle | Valeur par défaut |
|---|---|---|
| `VITE_API_URL` | Adresse de l'API, sans `/api/v1` | `http://localhost:8000` |

L'origine du site doit figurer dans la variable `CORS_ORIGINS` de l'API.

## Architecture

```
src/
  main.jsx             Point d'entrée
  App.jsx              Routes, selon que l'utilisateur est connecté ou non
  styles.css           Design system : couleurs, typographie, espacements, composants
  auth/AuthContext.jsx Session de l'utilisateur
  lib/
    api.js             Client HTTP : jetons, renouvellement automatique, messages d'erreur
    format.js          Montants, dates et mois
    useAsync.js        Chargement d'une ressource avec états de chargement et d'erreur
  components/          Composants partagés (boutons, champs, fenêtre modale, formulaire de dépense)
  pages/               Connexion, inscription, tableau de bord, dépenses, budgets, profil
```

## Écrans

- **Connexion et inscription.**
- **Tableau de bord** : total du mois et variation, alertes de budget, évolution sur six mois, répartition par catégorie, dernières dépenses.
- **Dépenses** : recherche, filtres par période et par catégorie, ajout, modification, suppression, import CSV, exports CSV et PDF.
- **Budgets** : plafond par catégorie et par mois, avec niveau de consommation.
- **Assistant** : questions sur les dépenses et les budgets, ajout d'une dépense par une phrase, questions générales. Chaque réponse indique les données dont elle est tirée.
- **Profil** : nom, e-mail, mot de passe, catégories personnelles.

## Choix techniques

- **Design system en CSS natif.** Les couleurs, rayons et ombres sont des variables CSS déclarées en tête de `styles.css`. Les mêmes valeurs sont reprises dans les applications mobile et desktop.
- **Session.** Les jetons sont conservés dans le stockage local du navigateur. Quand le jeton d'accès expire, `api.js` le renouvelle une seule fois, même si plusieurs requêtes échouent en même temps, puis rejoue la requête. Si le renouvellement échoue, l'utilisateur revient à l'écran de connexion.
- **Catégorie suggérée.** Dans le formulaire de dépense, la note est envoyée à l'API une fois la frappe interrompue. La catégorie proposée s'affiche avec son niveau de confiance et l'utilisateur reste libre de la changer.
- **Montants.** Toujours des entiers en francs CFA, affichés avec des chiffres tabulaires pour rester alignés dans les colonnes.
- **Petits écrans.** Sous 900 px, la barre latérale devient une barre de navigation en bas d'écran et le tableau des dépenses se réduit à l'essentiel.

## Déploiement

`npm run build` produit un site statique dans `dist/`. Sur Render, Netlify ou Vercel, il faut rediriger toutes les routes vers `index.html`, car la navigation est gérée côté navigateur. Sur Render : règle de réécriture `/*` vers `/index.html`.
