
# ANATEM
Anatem est la Nouvelle Plateforme pour faire Tourner et Expertiser les Modèles

## Note on langage
The langage used for this project and the following of this Readme is French.
It's because Anatem is for a specific use by french flood forecasting services.
If an english-speaking user is interested in this work, please let me know. I'd be happy to help.

## Introduction
Anatem est une interface de pilotage d'outils de prévision hydrologique. 
Il permet de lancer les outils en temps réel ou rejeu aux stations choisies et de visualiser, sauvegarder et exporter les résultats.
Les outils suportés sont :
- modèle hydrologique GRP (IRSTEA),
- modèle hydrologique Phoeniks,
- Analog : sélection et affichage d'événements analogues en base.
<Insérer capture d'écran>

Anatem est construit pour répondre aux besoins du service de prévision des crues SACN en particulier, 
mais peut être adapté à des pratiques et outils différents.

## Version
Version 1.0 du 6/05/2019

Évolutions majeures en construction pour les prochaines versions :
- Export des sorties de Phoeniks et Analog avec incertitude
- Prolongation des données de débit d'entrée
- Choix de la source des données d'entrée
- Archivage des prévisions de GRP en PHyC

## Technologies

Outil créé avec avec et pour Windows, Python v2.7 - Miniconda

- Bibliothèques publiques :
	- lxml            		v4.2.5
	- matplotlib    		v1.5.1
	- numpy           	v1.11.3
	- pandas          	v0.23.4
	- pendulum        	v2.0.4
	- pyodbc          	v4.0.25
	- pyqt            		v4.10.4
	- scipy           		v1.1.0

- Bibliothèques métier : 
	- libbdimage  v1.0.0 (Schapi)
	- libhydro    v0.5.3 (Schapi)

## Sources des données
### Bases locales
- Base Sacha :
    	- Pluie observée
    	- Débit observé
    	- Niveaux de vigilance (hauteur et débit)
- Base Barème :
    	- Courbes de tarage

### Bases distantes
- BDImage (Schapi) : 
    Prévisions de pluie RR3 symposium
- BD APBP (Schapi) : 
    Prévisions de pluie BP
(Pour l'interrogation des BDImage et BD APBP, les postes doivent être autorisés par le Schapi.)

## Interfaçage

Pilotage de GRP (modèle hydrologique de l'IRSTEA) v2016, avec incercitudes
Export des prévisions brutes de GRP au format XML pour expertise avec EAO

## Scénarios de pluie
Les scénarios de pluie prévue sont les suivants :
- RR3 symposium (Météo France)
- BP RR24 (Météo France)
    - haut, milieu et bas de la fourchette moyenne
    - haut et bas de la fourchette de maximum local le cas échéant
- 2 scénarios de pluie manuels optionnels (RR24)

Les RR24 sont ramenés au pas de temps 3h proportionnellement au RR3 symposium.
En cas d'échec de l'acquisition des RR3 symposium, les RR24 sont répartis uniformément sur 24h.
En cas d'échec de l'acquisition des RR3 symposium et des BP, les modèles tournent en pluie nulle ou avec les scénarios de pluie manuel seulement.

## Installation
- télécharger :
    - ANATEM
    - Miniconda
    - libbdimage
    - libhydro
- installer Miniconda
- créer environnement virtuel : 
    - compléter create_env_Anatem.bat (infos proxy, chemins libbdimage et libhydro)
    - placer create_env_Anatem.bat à la racine de la libbdimage
    - exécuter create_env_Anatem.bat
- copier le cossier Config_Template dans un dossier Config
- Remplacer les champs entre < > dans les fichiers suivants du dossier Config :
    - config.ini
    - stations.csv
    - phoeniks.csv
    - zones_BP_noms.csv
    - zones_BP_ponderation.csv
    - dossier Analog_base : un fichier par station
    
- lancement avec ANATEM.bat

## Crédits
Réalisé par M. Tastu
Icône : réalisé par mavadee sur flaticon.com
Merci aux collègues qui m'ont aidé à démarrer et aux consœurs et confrères pour leur réponses à mes questions et toutes les discussions passionnantes.
