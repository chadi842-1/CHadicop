# Guide de construction du rapport Power BI (.pbix)

Ce guide permet de construire le rapport **Fibre 360** dans Power BI Desktop en
~15 minutes à partir du modèle en étoile fourni dans `powerbi/dataset/`.

> Le `.pbix` est un format binaire propriétaire : il se crée dans Power BI
> Desktop. Ce dépôt fournit tout le nécessaire (données en étoile + mesures DAX
> + ce guide) pour l'assembler de façon fiable. Visuel cible : voir
> `dashboard/index.html` (même histoire de données).

## 0. Prérequis

- **Power BI Desktop** (gratuit, Windows / Microsoft Store).
- Les fichiers de `powerbi/dataset/` (générés par
  `python -m fibre360.reporting.powerbi_export`).

## 1. Charger les données

**Accueil ▸ Obtenir les données ▸ Dossier** → sélectionner `powerbi/dataset`.
Dans l'aperçu : **Combiner et transformer**. Power Query liste les 8 CSV.
(Variante plus simple : **Obtenir les données ▸ Texte/CSV** et charger chaque
fichier un par un.)

Charger ces 8 tables :
`fact_parcours`, `dim_date`, `dim_canal`, `dim_offre`, `dim_region`,
`dim_portefeuille`, `dim_sous_traitant`, `dim_segment`.

Dans Power Query, vérifier les **types** : `DateCommande` et `Date` en *Date*,
les colonnes de mesures (`DelaiLivraisonJ`, `MontantMensuel`, `NPS`,
`CAFacture`…) en *Nombre décimal*, les indicateurs 0/1 en *Nombre entier*.
Puis **Fermer et appliquer**.

## 2. Modèle (relations)

Vue **Modèle**. Créer les relations (plusieurs-à-un, sens unique) :

| Table (côté *) | Colonne | → Dimension (côté 1) | Colonne |
|----------------|---------|----------------------|---------|
| fact_parcours | DateCommande | dim_date | Date |
| fact_parcours | Canal | dim_canal | Canal |
| fact_parcours | Offre | dim_offre | Offre |
| fact_parcours | Region | dim_region | Region |
| fact_parcours | Portefeuille | dim_portefeuille | Portefeuille |
| fact_parcours | SousTraitant | dim_sous_traitant | SousTraitant |
| fact_parcours | Segment | dim_segment | Segment |

Sélectionner `dim_date` ▸ **Marquer comme table de dates** (colonne `Date`).

## 3. Mesures

Clic droit sur `fact_parcours` ▸ **Nouvelle mesure**, puis coller chaque bloc du
fichier `powerbi/DAX_measures.dax`. Formater en **Pourcentage** les mesures
annotées `// format %`, et en **monétaire (€)** le CA.

## 4. Pages du rapport

### Page 1 — Vue Direction
- 5 **cartes** : `[Taux livraison dans les delais]`, `[Delai moyen (j)]`,
  `[Taux d'echec]`, `[NPS moyen]`, `[Alertes SLA]`.
- **Graphique en courbes** : axe `dim_date[NomMois]`, valeur
  `[Taux livraison dans les delais]` (+ `[Delai moyen (j)]` sur une 2ᵉ visuel,
  jamais deux axes Y sur le même graphe).
- **Jauge** : `[Delai moyen (j)]`, cible `[SLA cible (j)]`.

### Page 2 — Multi-canalité
- **Histogramme empilé** : axe `dim_canal[Canal]`, valeur `[Nb commandes]`,
  légende `fact_parcours[Statut]`.
- **Histogramme groupé** : `[Taux livraison dans les delais]` et `[Taux d'echec]`
  par `Canal`.
- **Carte / barres** : `[NPS moyen]` par `Canal`.

### Page 3 — Portefeuille & géographie
- **Matrice** : lignes `Portefeuille`, mesures `[Nb commandes]`,
  `[Taux livraison dans les delais]`, `[NPS moyen]`, `[Taux de churn]`.
- **Carte** : `dim_region[Region]` (ou `Departement`), taille `[Nb commandes]`.

### Page 4 — Sous-traitance & process
- **Barres** : `[Taux d'echec]` par `SousTraitant`.
- **Table** : `dim_sous_traitant[TauxReussiteRef]` vs `[Taux d'echec]`.
- Importer `data/exports/pm_goulots.csv` pour la tornade des goulots.

### Page 5 — Commandes à risque
- Importer `data/exports/scoring_en_cours.csv`.
- **Table** triée par `score_risque`, segment `niveau_risque`.

### Page 6 — Rétention & churn
- Importer `data/exports/retention_canal.csv` et `churn_a_risque.csv`.
- **Barres** rétention à 12 mois par canal + **table** des clients à risque.

## 5. Segments (slicers) communs

`dim_date[NomMois]`, `dim_canal[Canal]`, `dim_offre[Offre]`,
`dim_segment[Segment]`, `dim_region[Region]`, `dim_portefeuille[Portefeuille]`.

## 6. Mise en forme conditionnelle

Sur les visuels affichant `[Taux livraison dans les delais]` : règle couleur par
champ via la mesure `[Couleur SLA]` (rouge < 60 %, orange 60–75 %, vert ≥ 75 %).

## 7. Publication

**Accueil ▸ Publier** vers le service Power BI pour le partage et la
planification de l'actualisation (rejoint le flux Power Automate, cf.
`power_automate/`).
