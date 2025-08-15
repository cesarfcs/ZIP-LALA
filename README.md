# Lalaleads – Outil de reporting avancé

Ce dépôt fournit un tableau de bord interactif pour analyser vos
campagnes de prospection à partir d’un export CSV HubSpot/Lemlist/Aircall.
L’interface est construite avec [Streamlit](https://streamlit.io) et
offre des filtres avancés, des graphiques et des tableaux pour suivre les
KPI clés de vos actions téléphoniques et e‑mailing.

## Installation

1. Clonez ou téléchargez ce dépôt, puis installez les dépendances :
   ```bash
   pip install -r requirements.txt
   ```

2. Lancez l’application :
   ```bash
   streamlit run app.py
   ```

## Fonctionnalités

- **Téléversement CSV** : chargez un export CRM HubSpot/Lemlist/Aircall au format CSV.
- **Sélection de l’offre et contexte** : renseignez le nom du client,
  choisissez l’offre souscrite (Multi 2J/3J/4J/5J, Full Digital ou
  Offre personnalisée) et sélectionnez les canaux utilisés pour la
  mission. Ces informations sont affichées pour le contexte mais
  n’affectent pas les calculs.
- **Filtres avancés** : filtrez les données par période, campagne,
  intitulé de poste, secteur, taille d’entreprise et localisation.
- **KPI détaillés** : le tableau de bord calcule automatiquement :
  - Nombre d’appels total (contacts ayant un **Last Aircall call timestamp**).
  - Nombre d’appels connectés (tags `Meeting`, `Pitch`, `Sans Suite` ou `Standard`).
  - Nombre d’appels pitchés (tags `Meeting` ou `Pitch`).
  - Rendez‑vous par téléphone (tag `Meeting`).
  - Taux de connexion, taux de pitch et taux de RDV téléphone.
  - Contacts e‑mailés, ouvertures et réponses (selon **lemlist lead status**).
  - Taux d’ouverture, taux de réponse.
  - Rendez‑vous par e‑mail (phase `RDV - Bon contact` + statut `Email replied`, excluant les contacts déjà `Meeting`).
  - Taux de conversion e‑mail et taux de conversion global.
- **Graphiques clairs** : barres et camemberts pour visualiser
  l’évolution des appels, la distribution des tags d’appels, les KPI
  e‑mail et les RDV par canal. Les valeurs sont affichées sur les barres.
- **Tableaux détaillés** : consultez la répartition des tags d’appels et
  exportez les données filtrées au format CSV.

## Personnalisation

Ce dépôt sert de base pour un outil de reporting plus complet. Vous
pouvez :

- Ajouter d’autres indicateurs (par exemple les tentatives de contact
  par prospect, la segmentation par secteur, etc.).
- Générer un rapport PowerPoint en réutilisant la fonction
  `compute_metrics()` et un module d’export comme `python-pptx`.
- Déployer l’application sur [Streamlit Cloud](https://streamlit.io/cloud)
  en poussant le dépôt sur GitHub et en choisissant `app.py` comme
  fichier principal.

N’hésitez pas à adapter l’esthétique du tableau de bord via les options
de Streamlit ou à intégrer d’autres bibliothèques de visualisation si
souhaité.
