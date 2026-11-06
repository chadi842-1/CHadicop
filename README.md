# Fibre 360° — Plateforme décisionnelle du parcours Commande → Livraison

Plateforme de **data analyse de bout en bout** pour piloter et améliorer les
**parcours Commande → Livraison des offres Fibre** (contexte opérateur télécom).
Du jeu de données jusqu'au dashboard et au plan d'actions, en passant par la
qualité de données, le process mining, la prévision et le machine learning.

> ⚠️ **Données 100 % fictives**, générées par le pipeline. Aucune donnée réelle
> ni confidentielle. Projet **original** (ne reprend aucun projet existant).

<p align="center"><em>Pipeline reproductible · 8 sources · ~60 000 commandes ·
2 ans d'historique · 2 modèles ML · dashboard interactif · tests + CI</em></p>

---

## 1. Ce que fait la plateforme

```
8 sources  ──► Qualité ──► Datamart ──►  Analytics            ──►  Reporting
(générées)     (checks)    (croise­    ├─ KPI multi-axes           ├─ Excel (20 onglets)
                           ment)       ├─ Process mining           ├─ Dashboard HTML
                                       ├─ Cohortes / rétention     ├─ Note IA + plan
                                       ├─ Prévision (Holt-Winters)      d'actions
                                       ├─ Détection d'anomalies
                                       ├─ Segmentation clients
                                       ├─ Scoring risque livraison (AUC ≈ 0,88)
                                       └─ Modèle de churn
```

Orchestration : `make all` (ou `python -m fibre360.cli all`).


## 2.3. Démarrage rapide

```bash
pip install -r requirements.txt       # ou : pip install -e ".[dev]"
make all                              # pipeline complet (~1 min)
```

Puis ouvrir **`dashboard/index.html`** dans un navigateur.

Étapes à la carte :

```bash
make generate     # 1. génère les 8 sources fictives
make quality      # 2. contrôles qualité de données
make datamart     # 3. croise les sources -> table de faits
make analytics    # 4. KPI, process mining, cohortes, prévision, anomalies, ML
make report       # 5. Excel + dashboard HTML + note IA
make test         # lance la suite de tests (pytest)
```

Configuration dans `config/config.yaml` (volume, seed, SLA).
L'agent IA tourne **hors-ligne** par défaut ; `export ANTHROPIC_API_KEY=...` pour
le brancher sur un LLM.

## 4. Aperçu du dashboard

Tableau de bord HTML **autonome** (Chart.js embarqué, thème clair/sombre,
responsive) : tuiles KPI, performance multi-canalité, répartition du risque,
volume historique **+ prévision**, délai mensuel, goulots du process, rétention
par canal, et table des commandes en cours à traiter en priorité.

## 5. Résultats (données de démonstration, seed 42)

- Taux de livraison dans les délais ≈ **64 %** (SLA 15 j), délai moyen ≈ **14 j**.
- Multi-canalité : **Boutique** la plus performante, **Distributeur** la plus faible.
- Process mining : goulot principal **« Prise de RDV → Construction ligne »**.
- Scoring risque : **AUC ≈ 0,88** (régression logistique retenue sur 3 modèles).
- Churn : **AUC ≈ 0,61** (problème volontairement difficile, résultat assumé).
- Facteurs de risque : zone à construire, sous-traitant, canal (explicabilité).

## 6. Structure du dépôt

```
fibre360/              package Python
  config.py            configuration centralisée
  data_generation/     génération des 8 sources
  pipeline/            qualité de données + datamart
  analytics/           kpis, process_mining, cohorts, forecasting, anomaly, segmentation
  ml/                  features, train (risque), churn, explicabilité
  reporting/           excel_report, dashboard HTML, insights (agent IA)
  cli.py               orchestration (sous-commandes)
sql/bigquery/          équivalent GCP (staging, datamart, KPI, ML, cohortes)
powerbi/ looker_studio/ power_automate/   spécifications de restitution/automatisation
dashboard/             dashboard HTML généré (+ Chart.js embarqué)
data/exports/          résultats versionnés (KPI, PM, scoring, qualité)
models/                cartes de modèle (model cards)
tests/                 suite pytest
docs/                  cadrage, architecture, dictionnaire, gouvernance, plan d'actions
.github/workflows/     intégration continue
```

## 7. Qualité logicielle

- **Tests** : `pytest` (génération, qualité, datamart, analytics, ML) — 22 tests.
- **CI** : GitHub Actions (tests + smoke test du pipeline, Python 3.11 & 3.12).
- **Reproductibilité** : graine fixée, configuration par fichier, logs horodatés.
- **Packaging** : `pyproject.toml`, commande `fibre360`.

## 8. Technologies

Python (pandas, scikit-learn, statsmodels, joblib) · SQL BigQuery / BigQuery ML ·
Power BI (DAX) · Looker Studio · Excel · Power Automate · Chart.js · Agent IA (Claude).

Voir `docs/architecture.md` pour le détail des modules et des flux.
