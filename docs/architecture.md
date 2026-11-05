# Architecture technique — Plateforme Fibre 360

## Vue d'ensemble

```
                         ┌───────────────────────────────┐
   8 sources             │   COUCHE DONNEES (data/)       │
   synthetiques  ──────> │   raw/  ->  mart/  ->  exports/│
   (data_generation)     └───────────────┬───────────────┘
                                          │
        ┌─────────────────────────────────┼─────────────────────────────────┐
        │                                 │                                 │
  ┌─────▼──────┐               ┌──────────▼──────────┐             ┌────────▼────────┐
  │ QUALITE    │               │ ANALYTICS           │             │ ML              │
  │ (data_     │               │ kpis / process_     │             │ train (risque)  │
  │  quality)  │               │ mining / cohorts /  │             │ churn           │
  │            │               │ forecasting /       │             │ features /      │
  │            │               │ anomaly / segment.  │             │ explain         │
  └────────────┘               └──────────┬──────────┘             └────────┬────────┘
                                          │                                 │
                               ┌──────────▼─────────────────────────────────▼────────┐
                               │   REPORTING (reporting/)                             │
                               │   excel_report · dashboard HTML · insights (IA)      │
                               └──────────────────────────────────────────────────────┘
                                          │
                        orchestration : fibre360/cli.py  (make all)
```

## Modules du package `fibre360/`

| Module | Role |
|--------|------|
| `config.py` | Configuration centralisee (chemins, parametres metier, referentiels, hyper-params), chargeable depuis `config/config.yaml`. Logger commun. |
| `data_generation/generators.py` | Genere 8 sources relationnelles coherentes sur 2 ans. |
| `pipeline/data_quality.py` | Framework de controles qualite (unicite, non-null, plage, domaine, integrite referentielle, fraicheur). |
| `pipeline/datamart.py` | Croise les 8 sources en table de faits (1 ligne/commande). |
| `analytics/kpis.py` | KPI multi-axes + synthese. |
| `analytics/process_mining.py` | Variantes, transitions, goulots, rework, conformite. |
| `analytics/cohorts.py` | Retention par cohorte mensuelle et par canal. |
| `analytics/forecasting.py` | Prevision Holt-Winters (repli moyenne mobile). |
| `analytics/anomaly.py` | Detection d'anomalies (z-score glissant robuste / MAD). |
| `analytics/segmentation.py` | Segmentation clients K-Means. |
| `ml/features.py` | Datasets d'apprentissage + pre-processeur. |
| `ml/train.py` | Scoring risque livraison : 3 modeles, CV, selection, explicabilite, persistance. |
| `ml/churn.py` | Modele de churn client. |
| `reporting/excel_report.py` | Classeur Excel multi-onglets + CSV. |
| `reporting/dashboard.py` | Dashboard HTML autonome (Chart.js local). |
| `reporting/insights.py` | Agent IA : note d'analyse + plan d'actions. |
| `cli.py` | Orchestration (sous-commandes). |

## Flux de bout en bout (`make all`)

1. **generate** → `data/raw/*.csv` (8 sources)
2. **quality** → `data/exports/data_quality_report.{csv,md}`
3. **datamart** → `data/mart/faits_parcours.csv`
4. **analytics & ML** → KPI, PM, cohortes, prevision, anomalies, segmentation, scoring, churn ; modeles dans `models/`
5. **report** → `KPI_pilotage_fibre.xlsx`, `dashboard/index.html`, `docs/note_analyse_auto.md`

## Equivalence GCP (production cible)

Le pipeline Python a son equivalent SQL dans `sql/bigquery/` :
staging → datamart (partitionne/clustere) → vues KPI → features & modeles
BigQuery ML (risque, churn) → cohortes/retention. En production, Python orchestre
et BigQuery execute les transformations lourdes ; Power BI / Looker Studio se
connectent au dataset `fibre_mart`.

## Qualite logicielle

- Tests `pytest` (generation, qualite, datamart, analytics, ML).
- Intégration continue GitHub Actions (`.github/workflows/ci.yml`) : tests + smoke test du pipeline sur 2 versions de Python.
- Configuration par fichier, exécution reproductible (seed), logs horodatés.
