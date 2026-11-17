# Mes Dépenses - Application mobile

Application Android en Flutter. Elle consomme l'API du dossier `api`.

## Première installation

Flutter 3.35 ou plus récent, et l'API lancée sur votre ordinateur.

Ce dossier contient le code Dart (`lib/`, `test/`, `pubspec.yaml`). Le dossier `android/` est généré par Flutter, une seule fois :

```bash
cd mobile
flutter create --platforms=android --project-name mes_depenses .
flutter pub get
```

`flutter create` ajoute les fichiers de plateforme sans toucher à `lib/` ni à `pubspec.yaml`. Il crée aussi un fichier `test/widget_test.dart` d'exemple, à supprimer car il teste l'application de démonstration de Flutter :

```bash
del test\widget_test.dart
```

### Autoriser l'accès au réseau

Ouvrez `android/app/src/main/AndroidManifest.xml` et faites deux ajouts.

1. Juste avant la balise `<application`, la permission d'accès à internet :

```xml
<uses-permission android:name="android.permission.INTERNET" />
```

2. Dans la balise `<application`, l'attribut qui autorise le HTTP non chiffré, nécessaire tant que l'API tourne en local sans HTTPS :

```xml
<application
    android:usesCleartextTraffic="true"
    ...
```

Dans la même balise, remplacez la valeur de `android:label` par `Mes Dépenses` pour que ce nom apparaisse sous l'icône.

Une fois l'API déployée en HTTPS, retirez `android:usesCleartextTraffic`.

## Lancement

Sur l'émulateur Android, l'adresse `10.0.2.2` désigne votre ordinateur : c'est la valeur par défaut.

```bash
flutter run
```

Sur un téléphone réel, branché au même réseau Wi-Fi que l'ordinateur, indiquez l'adresse IP de l'ordinateur et lancez l'API avec `--host 0.0.0.0` :

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
flutter run --dart-define=API_URL=http://192.168.1.20:8000
```

Avec l'API déployée :

```bash
flutter build apk --release --dart-define=API_URL=https://votre-api.onrender.com
```

Compte de démonstration : `awa.kone@example.com` / `demonstration-2026`.

| Commande | Rôle |
|---|---|
| `flutter run` | Lance l'application en mode développement |
| `flutter test` | Tests unitaires |
| `flutter analyze` | Analyse statique du code |
| `flutter build apk --release` | Produit l'APK dans `build/app/outputs/flutter-apk/` |

## Architecture

```
lib/
  main.dart        Point d'entrée, thème, choix entre connexion et application
  theme.dart       Design system : couleurs, styles de texte, champs et boutons
  format.dart      Montants, dates et mois
  models.dart      Objets renvoyés par l'API
  api.dart         Client HTTP : jetons, renouvellement automatique, messages d'erreur
  session.dart     État de connexion partagé (ChangeNotifier)
  widgets.dart     Composants partagés : carte, message, icône de catégorie, sélecteur de mois
  charts.dart      Histogramme mensuel et anneau de répartition
  screens/         Connexion, structure à onglets, tableau de bord, dépenses, budgets, assistant, profil
```

## Écrans

- **Connexion et création de compte.**
- **Accueil** : total du mois et variation, alertes de budget, évolution sur six mois, répartition par catégorie, dernières dépenses.
- **Dépenses** : liste du mois, recherche, ajout, modification et suppression en touchant une ligne.
- **Budgets** : plafond par catégorie, barre de consommation, trois niveaux.
- **Assistant** : questions sur les dépenses et les budgets, ajout d'une dépense par une phrase, questions générales.
- **Profil** : nom, e-mail, mot de passe, déconnexion.

L'import CSV, les exports CSV et PDF et la gestion des catégories personnelles sont disponibles sur le site web. Les catégories créées sur le web apparaissent dans l'application mobile.

## Choix techniques

- **Même design system que le web.** `theme.dart` reprend les couleurs, le rayon de 8 px et la police Inter. Les icônes sont celles de Material, fournies avec Flutter.
- **Jetons chiffrés.** Les jetons sont conservés avec `flutter_secure_storage`, qui s'appuie sur le Keystore d'Android, et non dans des préférences en clair.
- **Renouvellement de session.** Quand le jeton d'accès expire, `api.dart` le renouvelle une seule fois, même si plusieurs requêtes échouent en même temps, puis rejoue la requête.
- **Graphiques dessinés à la main.** `charts.dart` utilise `CustomPainter` plutôt qu'une bibliothèque : deux graphiques simples ne justifient pas une dépendance, et le rendu reste identique au web.
- **État simple.** `provider` partage le client HTTP et la session. Chaque écran charge ses propres données avec un `FutureBuilder`, et se recharge par un geste de tirage vers le bas.
- **Catégorie suggérée.** Dans le formulaire, la note est envoyée à l'API une fois la frappe interrompue. La proposition s'affiche avec son niveau de confiance.

## Dépendances

| Paquet | Rôle |
|---|---|
| `http` | Requêtes vers l'API |
| `provider` | Partage de l'état |
| `flutter_secure_storage` | Stockage chiffré des jetons |
| `google_fonts` | Police Inter, téléchargée au premier lancement puis mise en cache |
| `flutter_localizations` | Sélecteur de date et libellés système en français |
