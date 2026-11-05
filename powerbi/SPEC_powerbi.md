# Spécification du rapport Power BI — « Fibre 360° »

Rapport de pilotage du parcours **Commande → Livraison** des offres Fibre.
Source de données : `data/mart/faits_parcours.csv` (ou connexion directe à
BigQuery `fibre_mart` via le connecteur Google BigQuery).

> Les données sont **fictives** (générées par le pipeline). En production, la
> connexion pointerait sur le dataset BigQuery `fibre_mart`.

---

## 1. Modèle de données (schéma en étoile)

- **Table de faits** : `faits_parcours` (1 ligne / commande).
- **Dimensions** : `dim_temps` (reliée par `date_commande`), plus les colonnes
  dimensionnelles de la table de faits (canal, offre, segment, region,
  gestionnaire_portefeuille, sous_traitant) utilisables en segments.
- Relation : `faits_parcours[date_commande]` → `dim_temps[date]` (1 → *).

## 2. Mesures DAX

```DAX
Nb commandes            = COUNTROWS ( faits_parcours )

Nb livrées              = CALCULATE ( [Nb commandes],
                              faits_parcours[statut_parcours] = "Livree" )

Taux livraison délai %  =
VAR _liv = CALCULATE ( [Nb commandes], faits_parcours[statut_parcours] = "Livree" )
VAR _ok  = CALCULATE ( [Nb commandes],
               faits_parcours[statut_parcours] = "Livree",
               faits_parcours[livree_dans_delai] = 1 )
RETURN DIVIDE ( _ok, _liv )

Délai moyen (j)         =
CALCULATE ( AVERAGE ( faits_parcours[delai_livraison_j] ),
            faits_parcours[statut_parcours] = "Livree" )

Taux d'échec %          =
DIVIDE (
    CALCULATE ( [Nb commandes],
        faits_parcours[statut_parcours] = "Echec raccordement" ),
    [Nb commandes] )

NPS moyen               =
CALCULATE ( AVERAGE ( faits_parcours[nps] ),
            faits_parcours[statut_parcours] = "Livree" )

Alertes SLA             =
CALCULATE ( [Nb commandes], faits_parcours[alerte_sla] = TRUE )

-- Écart au SLA cible (15 j) pour le visuel de type jauge
Écart SLA (j)           = [Délai moyen (j)] - 15
```

## 3. Pages du rapport

| Page | Visuels | Objet |
|------|---------|-------|
| **1. Vue Direction** | Cartes KPI ([Taux livraison délai %], [Délai moyen (j)], [Taux d'échec %], [NPS moyen], [Alertes SLA]) ; courbe mensuelle du taux SLA ; jauge Écart SLA | Vision business synthétique |
| **2. Multi-canalité** | Barres empilées par `canal` (statut), barres [Taux livraison délai %] par canal, [NPS moyen] par canal | Comparer les canaux |
| **3. Portefeuille** | Matrice `gestionnaire_portefeuille` × KPI, carte régionale (`departement`) | Piloter les portefeuilles |
| **4. Sous-traitance & process** | [Taux d'échec %] par `sous_traitant`, top motifs d'échec, tornade des goulots (import `pm_goulots.csv`) | Qualité de production |
| **5. Commandes à risque** | Table des commandes en cours (import `scoring_en_cours.csv`) triée par `score_risque`, filtre `niveau_risque` | Action opérationnelle |
| **6. Rétention & churn** | Rétention à 12 mois par canal (`retention_canal.csv`), courbes de cohortes (`retention_cohortes.csv`), top clients à risque de churn (`churn_a_risque.csv`) | Fidélisation / rétention |

> Le modèle s'appuie désormais sur 8 sources (clients, techniciens,
> réclamations, factures en plus). Un **dashboard HTML autonome** (`dashboard/`)
> fournit une alternative sans licence, directement partageable.

## 4. Segments (slicers) communs

`dim_temps[annee_mois]`, `canal`, `offre`, `segment`, `region`,
`gestionnaire_portefeuille`, `niveau_risque`.

## 5. Mise en forme conditionnelle

- [Taux livraison délai %] : rouge < 60 %, orange 60–75 %, vert ≥ 75 %.
- [Écart SLA (j)] : vert si ≤ 0, rouge si > 0.
- Palette accessible (contraste suffisant, lisible en vidéoprojection).
