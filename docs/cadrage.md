# Note de cadrage — Projet « Fibre 360° »

## Contexte

Le pilotage du parcours **Commande → Livraison** des offres Fibre repose sur
plusieurs systèmes (CRM/ventes, planification, interventions techniques,
enquêtes de satisfaction) et sur des rapports existants à enrichir. L'enjeu est
d'**améliorer la connaissance et la maîtrise de ces parcours**, d'objectiver la
performance (délais, échecs, satisfaction) et d'outiller la décision.

> Les données utilisées ici sont **entièrement fictives** et générées par le
> pipeline du projet : aucune donnée réelle ni confidentielle n'est manipulée.

## Objectifs

1. **Croiser** les sources dispersées en un modèle unique du parcours.
2. **Enrichir** les rapports existants (délais, SLA, multi-canalité, portefeuille).
3. **Analyser le processus** (process mining) pour identifier variantes et goulots.
4. **Scorer** le risque de non-livraison pour prioriser l'action.
5. **Automatiser** les alertes et le reporting (Power Automate).
6. **Aider à la décision** via un agent IA qui rédige note + plan d'actions.

## Périmètre & indicateurs clés

- Taux de livraison dans les délais (SLA = 15 j), délai moyen commande → mise en service.
- Taux d'échec de raccordement, taux d'annulation.
- NPS et taux de réclamation.
- Performance par **canal**, **offre**, **région**, **portefeuille**, **sous-traitant**.

## Chaîne de valeur / outils (alignée sur la fiche de poste)

| Étape | Outil | Livrable |
|-------|-------|----------|
| Collecte & modélisation | **GCP / BigQuery (SQL)** | `sql/bigquery/*.sql`, datamart |
| Qualité & préparation | **Python / Excel** | `fibre360/pipeline/`, `KPI_pilotage_fibre.xlsx` |
| Analyse de processus | **Process mining** (Celonis/UiPath en prod) | `fibre360/analytics/process_mining.py` |
| Analytics avancée | **Python** | cohortes, prévision, anomalies, segmentation (`fibre360/analytics/`) |
| Scoring & churn | **IA / BigQuery ML** | `fibre360/ml/` + `sql/bigquery/` |
| Restitution | **Power BI, Looker Studio, dashboard HTML** | `powerbi/`, `looker_studio/`, `dashboard/` |
| Automatisation | **Power Automate** | `power_automate/flow_alertes.md` |
| Aide à la décision | **Agent IA** | `fibre360/reporting/insights.py` |

## Méthode & posture

Approche itérative, à l'écoute des utilisateurs (reformulation des besoins,
restitution à tous les niveaux). Respect de la **confidentialité des données**.
Les modèles et analyses sont **explicables** et validés avec le métier avant
tout déploiement.
