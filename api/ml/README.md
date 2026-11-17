# Modèle de catégorisation

Ce dossier contient tout ce qui produit le modèle qui propose une catégorie à partir du libellé d'une dépense.

## Reproduire l'entraînement

Depuis le dossier `api`, avec l'environnement virtuel :

```powershell
.venv\Scripts\python -m pip install -r requirements-ml.txt
.venv\Scripts\python -m ml.build_dataset
.venv\Scripts\python -m ml.prepare
.venv\Scripts\python -m ml.train
```

La dernière commande dure une quinzaine de secondes. Elle écrit le modèle dans `models/categorizer.joblib` et le rapport dans `ml/reports/metrics.json`. **Redémarrez ensuite l'API** : le modèle est chargé une seule fois, au premier appel.

Le modèle n'est pas versionné dans Git : un fichier joblib n'est fiable qu'avec la version de scikit-learn qui l'a produit. Il se reconstruit à l'identique avec les commandes ci-dessus, les tirages aléatoires étant fixés.

Pour ouvrir le notebook :

```powershell
.venv\Scripts\python -m jupyter notebook ml/notebooks/entrainement.ipynb
```

## Contenu

| Fichier | Rôle |
|---|---|
| `vocabulary.py` | 657 libellés de base, de 59 à 85 par catégorie, rédigés à la main |
| `build_dataset.py` | Génère 14 variantes par libellé : lieu, précision, abréviation, casse, accents, faute de frappe |
| `prepare.py` | Nettoyage : normalisation, libellés trop courts, doublons, contradictions |
| `train.py` | Comparaison de cinq modèles, évaluation, enregistrement |
| `export_corrections.py` | Exporte les corrections des utilisateurs pour réentraîner |
| `data/libelles_bruts.csv` | 9 855 libellés générés |
| `data/libelles_propres.csv` | 6 761 libellés après nettoyage |
| `data/test_manuel.csv` | 120 libellés rédigés à la main, réservés à l'évaluation |
| `notebooks/entrainement.ipynb` | Démarche complète, commentée, avec les graphiques |
| `reports/` | Métriques et figures du dernier entraînement |

## Données

Le jeu de données est **synthétique** : aucun historique réel de dépenses n'était disponible. Les libellés de base ont été rédigés à la main à partir de dépenses courantes à Abidjan, puis déclinés automatiquement. Les mesures ci-dessous décrivent donc le comportement du modèle sur ce vocabulaire et devront être confirmées sur des libellés réels.

## Résultats

Modèle retenu : régression logistique sur TF-IDF de mots et de n-grammes de caractères.

| Mesure | Modèle | Règles par mots-clés |
|---|---|---|
| Découpage aléatoire (optimiste : variantes vues à l'entraînement) | 98,5 % | |
| Libellés de base jamais vus (pessimiste) | 52,0 % | 30,0 % |
| Jeu rédigé à la main (120 libellés) | 90,0 % | 55,8 % |

Les trois chiffres répondent à trois questions différentes : le modèle a-t-il appris son vocabulaire, que fait-il face à des mots inconnus, et que donne-t-il sur des formulations nouvelles. Le vocabulaire a été enrichi de 450 à 657 libellés de base : la mesure sur libellés jamais vus est passée de 46 % à 52 %. Sept des libellés ajoutés recoupent le jeu manuel, dont le score de 90 % est donc légèrement favorable.

Le notebook détaille le protocole, la matrice de confusion, l'analyse des erreurs et le choix du seuil de confiance.

## Fonctionnement dans l'API

`app/services/categorizer.py` applique la décision suivante à chaque libellé :

1. si le modèle est présent et que sa confiance atteint 0,35, sa proposition est retenue ;
2. sinon, les règles par mots-clés prennent le relais ;
3. sinon, aucune proposition : la dépense va dans « Autres » si l'utilisateur ne choisit pas.

La route `GET /api/v1/model` indique quel moteur est en service et rappelle les mesures du dernier entraînement.

## Réentraîner avec les corrections

Chaque proposition est enregistrée avec la catégorie finalement retenue (table `predictions`). Pour apprendre des corrections :

```powershell
.venv\Scripts\python -m ml.export_corrections
.venv\Scripts\python -m ml.train --corrections ml/data/corrections.csv
```

Le fichier `corrections.csv` contient des notes saisies par les utilisateurs : il est exclu de Git et ne doit pas être publié.
