"""Libellés de base du jeu de données, par catégorie.

Ces libellés ont été rédigés à la main pour refléter des dépenses courantes à
Abidjan. Le générateur (build_dataset.py) en dérive des variantes : lieux,
précisions, abréviations, casse, accents et fautes de frappe.
"""

BASE_LABELS: dict[str, list[str]] = {
  "Alimentation": [
    "Garba", "Attiéké poisson", "Alloco poulet", "Marché", "Courses au marché", "Riz et huile",
    "Sac de riz", "Poisson frais", "Poulet braisé", "Déjeuner au maquis", "Restaurant", "Dîner au restaurant",
    "Petit déjeuner", "Pain et lait", "Baguettes de pain", "Courses supermarché", "Carrefour Market",
    "Légumes et condiments", "Viande de bœuf", "Bouteille d'huile", "Eau minérale", "Pack d'eau",
    "Jus de bissap", "Placali", "Foutou banane", "Sauce graine", "Kédjénou", "Chawarma", "Pizza",
    "Bananes plantains", "Ignames", "Tomates et oignons", "Sucre et lait en poudre", "Café et thé",
    "Yaourts", "Œufs", "Boissons pour la maison", "Goûter des enfants", "Glaces", "Provisions du mois",
    "Boulangerie", "Poissonnerie", "Boucherie", "Fruits", "Pâtes et sardines", "Cube et épices",
    "Livraison Glovo", "Livraison repas", "Tchep", "Foutou igname", "Kaba-tô", "Gbofloto",
    "Galettes", "Croissants", "Crème glacée", "Soda / Sucrerie", "Jus naturel", "Gingembre",
    "Fromage et beurre", "Conserves", "Farine", "Charcuterie", "Dîner en famille", "Repas de midi",
    "Achat au kiosque", "Café au kiosque"
  ],
  "Transport": [
    "Gbaka", "Woro-woro", "Taxi compteur", "Taxi", "Yango", "Heetch", "inDrive", "Uber", "Bus Sotra",
    "Bateau-bus", "Carburant", "Plein d'essence", "Gasoil", "Péage", "Péage pont HKB",
    "Péage autoroute du Nord", "Parking", "Lavage voiture", "Vidange", "Changement d'huile",
    "Filtre à huile", "Réparation moto", "Pneu neuf", "Garagiste", "Mécanicien", "Électricien auto",
    "Pièces détachées", "Billet de car", "Car UTB", "Car CTE", "Compagnie de transport",
    "Voyage Yamoussoukro", "Déplacement Bouaké", "Moto-taxi", "Transport pour le travail",
    "Transport retour", "Aller-retour bureau", "Course en taxi", "Ticket de bus", "Carte Sotra",
    "Assurance auto", "Visite technique", "Contrôle technique", "Vignette auto", "Crevaison",
    "Batterie voiture", "Plaquettes de frein", "Climatisation voiture", "Location de voiture",
    "Billet d'avion", "Billet de train", "Bagages gare routière", "Gare routière",
    "Transport des enfants", "Covoiturage", "Trajet aéroport", "Huile moteur", "Essence moto",
    "Casque moto", "Chauffeur", "Stationnement", "Frais de fourrière", "Frais de livraison", "Course express"
  ],
  "Logement": [
    "Loyer", "Loyer du mois", "Caution appartement", "Avance de loyer", "Frais d'agence", "Gardien",
    "Femme de ménage", "Plombier", "Électricien", "Peintre", "Maçon", "Vitrier", "Peinture de la maison",
    "Bouteille de gaz", "Recharge gaz", "Tuyau de gaz", "Détendeur gaz", "Matelas", "Meuble de salon",
    "Rideaux", "Ventilateur", "Ventilateur sur pied", "Climatiseur neuf", "Réparation climatiseur",
    "Serrurier", "Serrure et clés", "Double de clé", "Ampoules", "Rallonge électrique", "Multiprise",
    "Produits d'entretien", "Balai et serpillière", "Savon et javel", "Draps", "Vaisselle",
    "Casseroles", "Réfrigérateur", "Réparation frigo", "Télévision", "Machine à laver", "Cuisinière",
    "Menuisier", "Carrelage", "Ciment", "Quincaillerie", "Charges de l'immeuble", "Syndic",
    "Déménagement", "Canapé", "Table et chaises", "Moustiquaire", "Insecticide",
    "Dératisation / Désinsectisation", "Jardinier", "Entretien de la cour", "Réparation toiture",
    "Fosse septique", "Micro-ondes", "Fer à repasser", "Lit", "Armoire", "Ramassage d'ordures",
    "Taxe d'enlèvement des ordures", "Achat d'eau en bidon", "Livraison d'eau"
  ],
  "Factures": [
    "Facture CIE", "Facture électricité", "Facture SODECI", "Facture d'eau", "Facture eau SODECI",
    "Compteur prépayé CIE", "Recharge compteur électricité", "Abonnement Canal+", "Réabonnement Canal",
    "Abonnement StarTimes", "Abonnement IPTV", "Facture internet", "Abonnement fibre",
    "Facture fibre optique", "Facture Moov Fiber", "Facture Orange Fiber", "Facture MTN Fiber",
    "Impôts", "Impôt foncier", "Impôt sur le revenu", "Patente", "Taxe d'habitation", "Taxe municipale",
    "Assurance habitation", "Assurance maladie", "Assurance scolaire", "Assurance voyage", "Mutuelle",
    "Cotisation CNPS", "Frais de tenue de compte", "Frais de carte bancaire", "Cotisation annuelle carte",
    "Agios bancaires", "Abonnement Netflix", "Abonnement Spotify", "Abonnement YouTube Premium",
    "Abonnement salle de sport", "Facture téléphone fixe", "Redevance télé", "Renouvellement passeport",
    "Carte d'identité", "Permis de conduire", "Abonnement journal", "Facture eau et électricité",
    "Régularisation CIE", "Pénalité de retard", "Abonnement cloud", "Abonnement iCloud",
    "Abonnement Google One", "Nom de domaine", "Hébergement site web", "Cotisation syndic",
    "Assurance vie", "Frais de virement", "Abonnement antivirus", "Licence logiciel",
    "Abonnement ChatGPT", "Abonnement Claude", "Abonnement IA"
  ],
  "Communication": [
    "Recharge Orange", "Recharge MTN", "Recharge Moov", "Recharge Wave", "Crédit téléphone", "Unités",
    "Forfait internet", "Pass internet", "Pass semaine", "Pass mensuel", "Forfait appels",
    "Transfert de crédit", "Box wifi", "Recharge box", "Abonnement Box 4G", "Routeur wifi",
    "Câble réseau", "Carte SIM", "Puce Orange", "Forfait data", "Mégas", "Giga internet",
    "Pass WhatsApp", "Pass Facebook", "Pass TikTok", "Pass YouTube", "Pass réseaux sociaux",
    "Appels internationaux", "Crédit de communication", "Forfait illimité", "Recharge 4G",
    "Clé internet", "Cybercafé", "Connexion internet", "Renouvellement forfait", "Forfait mobile",
    "Recharge téléphone", "Pass jour", "Pass nuit", "Pass nuit Orange", "Pass nuit MTN",
    "Bonus appels", "Roaming", "Duplicata SIM", "Forfait Orange", "Forfait MTN", "Forfait Moov",
    "Crédit d'appel", "SMS", "Recharge crédit", "Pack internet", "Souscription pass", "Data mobile",
    "Achat pass via Orange Money", "Achat pass via MTN Moov", "Déblocage téléphone",
    "Réparation téléphone", "Écran cassé", "Chargeur téléphone", "Écouteurs", "Powerbank", "Carte mémoire"
  ],
  "Santé": [
    "Pharmacie", "Médicaments", "Consultation médecin", "Consultation clinique", "Clinique privée",
    "Polyclinique", "Hôpital", "CHU", "Analyses médicales", "Frais de laboratoire", "Prise de sang",
    "Radio", "Radiographie", "Scanner / IRM", "Échographie", "Échographie grossesse", "Dentiste",
    "Soins dentaires", "Ophtalmologue", "Lunettes de vue", "Ordonnance", "Paracétamol",
    "Antipaludéen", "Traitement palu", "Vaccin", "Vaccination des enfants", "Pédiatre",
    "Gynécologue", "Consultation gynécologue", "Consultation cardiologue", "Consultation ORL",
    "Kinésithérapie", "Séance de kiné", "Pansements", "Sirop pour la toux", "Vitamines",
    "Compléments alimentaires", "Vermifuge", "Test paludisme", "Bilan de santé", "Urgences",
    "Hospitalisation", "Infirmier à domicile", "Soins infirmiers", "Moustiquaire imprégnée",
    "Tensiomètre", "Thermomètre", "Antibiotiques", "Collyre", "Pommade", "Crème solaire",
    "Consultation dermatologue", "Carnet de santé", "Dépistage", "Injection", "Perfusion",
    "Accouchement clinique", "Frais d'accouchement", "Visite prénatale", "Opticien",
    "Sérum physiologique", "Lait infantile", "Couches bébé", "Gel hydroalcoolique", "Masques chirurgicaux"
  ],
  "Éducation": [
    "Scolarité", "Frais de scolarité", "Inscription école", "Frais d'inscription école",
    "Inscription maternelle", "Fournitures scolaires", "Cahiers et stylos", "Livres scolaires",
    "Manuels", "Achat de romans scolaires", "Uniforme scolaire", "Tenue d'école", "Tenue de sport école",
    "Cantine scolaire", "Transport scolaire", "Car scolaire", "Cours du soir", "Répétiteur",
    "Cours particuliers", "Cours de vacances", "Frais d'examen", "Inscription BAC", "Inscription BEPC",
    "Inscription CEPE", "Frais de concours", "Test de langue", "TCF / TEF", "Formation en ligne",
    "Formation professionnelle", "Frais de formation", "Cours d'anglais", "Photocopies de cours",
    "Impression mémoire", "Frais de soutenance", "Reliure mémoire", "Sac d'école", "Calculatrice",
    "Clé USB", "Ordinateur portable", "Tablette éducative", "Cotisation COGES", "Frais de stage",
    "Université", "Frais d'inscription université", "Bibliothèque", "Frais de bibliothèque",
    "Livre de programmation", "Cours d'informatique", "Certification", "Abonnement plateforme de cours",
    "Abonnement Coursera", "Abonnement Udemy", "Garderie", "Crèche", "Sortie scolaire",
    "Frais de dossier école", "Dictionnaire", "Trousse et crayons", "Mensualité école",
    "Soutien scolaire", "Atelier de formation", "Séminaire", "Kit scolaire", "Rame de papier", "Frais de diplôme"
  ],
  "Loisirs": [
    "Cinéma", "Concert", "Sortie entre amis", "Plage à Bassam", "Sortie à Grand-Bassam",
    "Week-end à Assinie", "Hôtel à Assinie", "Week-end à Jacqueville", "Maquis entre amis",
    "Espace plein air", "Chicha", "Boîte de nuit", "Bar", "Match de foot", "Match des Éléphants",
    "Billet de stade", "Salle de jeux", "Jeu vidéo", "Jeux PlayStation", "Achat console",
    "Abonnement jeux", "Piscine", "Parc d'attractions", "Zoo", "Anniversaire", "Karaoké",
    "Bowling", "Livre roman", "Musée", "Festival", "Théâtre", "Spectacle d'humour",
    "Dîner spectacle", "Location de film", "Excursion", "Randonnée", "Pique-nique",
    "Sortie en famille", "Glacier en famille", "Pâtisserie / Salon de thé", "Fête de fin d'année",
    "Réveillon", "Voyage de vacances", "Hôtel week-end", "Soirée dansante", "Billet de concert",
    "Paintball", "Jet-ski", "Balade en pirogue", "Tournoi de maracana", "Location terrain maracana",
    "Ballon de foot", "Equipement de sport", "Maillot de foot", "Crampons",
    "Abonnement salle de fitness", "Séance de sport", "Jeux de société", "Sortie au Plateau",
    "Sortie au mall", "Playce Marcory", "Cosmos Yopougon", "Cap Sud", "Brunch", "Lounge"
  ],
   "Habillement": [
    "Pagne", "Couturier", "Tailleur", "Couture tenue traditionnelle", "Frais de broderie",
    "Tissu Kita", "Tissu Woodin", "Uniwax", "Tissu super wax", "Chaussures", "Baskets",
    "Sandales", "Talons", "Mocassins", "Claquettes", "Bottes", "Chaussures de ville",
    "Cordonnier", "Réparation chaussures", "Cirage chaussures", "Chemise", "Polo", "Pantalon",
    "Robe", "Robe de soirée", "Jupe", "Jean", "T-shirt", "Costume", "Veste", "Pull / Gilet",
    "Ensemble homme", "Ensemble femme", "Tenue de sport", "Tenue de travail", "Maillot de bain",
    "Sous-vêtements", "Chaussettes", "Pyjama", "Sac à main", "Sac à dos", "Valise",
    "Portefeuille", "Pochette", "Ceinture", "Montre", "Bijoux", "Cravate", "Boutons de manchette",
    "Coiffure", "Tresses", "Coiffeur", "Barbier", "Rasage", "Mèches", "Perruque", "Tissage",
    "Lissage / Défrisage", "Huile pour cheveux", "Vêtements des enfants", "Habits de fête",
    "Tenue de mariage", "Bazin", "Wax", "Friperie", "Lunettes de soleil", "Parfum",
    "Crème de corps", "Lotion corporelle", "Lait de toilette", "Savon de toilette", "Déodorant",
    "Maquillage", "Manucure", "Pédicure", "Pose d'ongles", "Soin du visage", "Pressing",
    "Blanchisserie", "Retouche couture", "Foulard", "Casquette", "Chapeau", "Boubou",
    "Complet pagne"
    ],
    "Autres": [
    "Cotisation tontine", "Tontine", "Don à l'église", "Dîme", "Offrande", "Zakat", "Aumône",
    "Cadeau de mariage", "Cadeau d'anniversaire", "Cotisation funérailles", "Funérailles au village",
    "Envoi d'argent à la famille", "Argent pour maman", "Aide à un ami", "Dépannage",
    "Prêt à un collègue", "Remboursement de dette", "Frais de retrait", "Frais de transfert",
    "Frais Mobile Money", "Frais bancaires", "Cotisation association", "Cotisation du quartier",
    "Épargne", "Dépôt d'épargne", "Investissement", "Divers", "Dépense imprévue", "Pourboire",
    "Gardien parking", "Geste au vigile", "Commission", "Cadeau de naissance", "Baptême",
    "Contribution mariage", "Argent de poche des enfants", "Dot", "Fête de famille",
    "Soutien au village", "Don association", "Don orphelinat", "Collecte au bureau",
    "Cadeau collègue", "Pot de départ", "Frais divers", "Achat divers", "Perte d'argent",
    "Erreur de transfert", "Vol", "Sacrifice Tabaski", "Mouton Tabaski", "Rupture Ramadan",
    "Cadeau Noël", "Étrennes", "Cotisation mutuelle du village", "Participation deuil",
    "Autre dépense", "Mendiant", "Timbre fiscal", "Frais administratifs", "Amende"
    ],
}

PLACES = [
    "Cocody", "Yopougon", "Plateau", "Adjamé", "Marcory", "Treichville", "Abobo", "Koumassi",
    "Angré", "Riviera", "Bingerville", "Port-Bouët", "Deux-Plateaux", "Attécoubé", "Anyama",
]

# Précisions ajoutées après le libellé, communes à toutes les catégories.
DETAILS = [
    "du mois", "ce matin", "ce soir", "hier", "de la semaine", "novembre", "octobre", "décembre",
    "pour maman", "pour les enfants", "pour la maison", "urgent", "x2", "2e fois", "fin du mois",
    "payé par Orange Money", "via Wave", "en espèces", "payé par MTN MoMo", "avec la carte",
]

PREFIXES = ["Achat", "Paiement", "Frais", "Dépense", "Règlement"]

# Catégories dont les libellés se précisent naturellement par un lieu.
PLACE_CATEGORIES = {"Alimentation", "Transport", "Santé", "Loisirs", "Habillement", "Logement", "Éducation"}

ABBREVIATIONS = {
    "pour": "pr",
    "facture": "fact",
    "transport": "transp",
    "pharmacie": "pharma",
    "restaurant": "resto",
    "abonnement": "abo",
    "consultation": "consult",
    "recharge": "rech",
    "internet": "net",
    "scolarité": "scol",
    "inscription": "inscr",
    "téléphone": "tel",
    "cotisation": "cotis",
    "supermarché": "super marché",
    "médicaments": "médocs",
    "appartement": "appart",

    # Mots courants & liaisons
    "avec": "avc",
    "dans": "ds",
    "chez": "chz",
    "bouteille": "btl",
    "achat": "ach",
    "paiement": "paie",
    "remboursement": "remb",
    "participation": "partic",
    "contribution": "contrib",
    "anniversaire": "anniv",
    "association": "asso",
    "argent": "arg",
    "enfants": "enfts",
    "famille": "fam",
    "collègue": "coll",

    # Transport & Villes CI
    "carburant": "carb",
    "essence": "ess",
    "assurance": "assur",
    "réparation": "répar",
    "mécanicien": "mécano",
    "climatiseur": "clim",
    "climatisation": "clim",
    "aller-retour": "a/r",
    "voyage": "voy",
    "aéroport": "aérop",
    "yamoussoukro": "yakro",
    "bouaké": "bké",
    "grand-bassam": "bassam",

    # Alimentation & Logement
    "petit déjeuner": "ptit déj",
    "déjeuner": "déj",
    "boulangerie": "boul",
    "électricité": "élec",
    "réfrigérateur": "frigo",
    "produits": "prod",
    "entretien": "entret",

    # Communication & Finance
    "forfait": "forf",
    "communication": "comm",
    "télévision": "télé",
    "ordinateur": "ordi",
    "orange money": "om",
    "mobile money": "momo",
    "transfert": "transf",
    "virement": "vir",
    "administratifs": "admin",

    # Santé, Éducation & Habillement
    "hôpital": "hop",
    "ordonnance": "ordo",
    "analyses": "analy",
    "ophtalmologue": "ophtalmo",
    "gynécologue": "gynéco",
    "pédiatre": "pédia",
    "université": "univ",
    "fournitures": "fournit",
    "formation": "form",
    "chaussures": "chauss",
    "pantalon": "pantal",
    "vêtements": "vêt",
    "coiffeur": "coiff",
}
