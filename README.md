# Fibre 360° — Pilotage du parcours Commande → Livraison

Projet de **Data Analyse** de bout en bout, conçu pour illustrer les missions et
les outils d'un stage d'analyste de données sur les **parcours Commande →
Livraison des offres Fibre** (contexte opérateur télécom).

> ⚠️ **Données 100 % fictives.** Toutes les données sont générées par le
> pipeline (`scripts/01_generate_data.py`). Aucune donnée réelle ni
> confidentielle n'est utilisée. Projet **original**, construit from scratch.

---

## Pourquoi ce projet ?

L'offre demande d'**enrichir des analyses existantes**, de **croiser plusieurs
sources**, de **réfléchir à des modèles de scoring**, de **proposer des plans
d'actions** (portefeuille, multi-canalité) et d'**aider à la décision**, en
mobilisant **Power BI, GCP (SQL), Looker Studio, Excel, Power Automate /
process mining et des agents IA**.

Ce dépôt matérialise une **chaîne décisionnelle complète** qui répond à chacun
de ces points sur un cas concret : mesurer et améliorer la performance de
livraison de la Fibre.

## Correspondance offre ↔ projet

| Mission de l'offre | Dans ce projet |
|--------------------|----------------|
| Croiser plusieurs sources de données | 4 sources (commandes, événements, interventions, satisfaction) croisées en un datamart — `scripts/02_build_datamart.py`, `sql/bigquery/02_datamart_parcours.sql` |
| Enrichir analyses et rapports | KPI multi-axes + classeur Excel — `scripts/05_kpi_export.py` |
| Réfléchir à des modèles de scoring | Scoring du risque de non-livraison (AUC ≈ 0,88, explicable) — `scripts/04_scoring_model.py` + BigQuery ML |
| Analyse de processus (Celonis/UiPath) | Process mining du parcours (variantes, goulots, conformité) — `scripts/03_process_mining.py` |
| Plans d'actions (portefeuille, multi-canalité) | `docs/plan_actions.md` + note auto `docs/note_analyse_auto.md` |
| Vision business / aide à la décision | Rapports Power BI & Looker Studio — `powerbi/`, `looker_studio/` |
| Améliorer les outils / automatiser | Flux Power Automate (alertes + reporting) — `power_automate/` |
| Analyses par IA / agents IA | Agent IA qui rédige note + plan — `ai_agent/agent_insights.py` |

| Outil de l'offre | Où il est mobilisé |
|------------------|--------------------|
| **GCP / BigQuery (SQL)** | `sql/bigquery/` (staging, datamart, KPI, scoring + BigQuery ML) |
| **Power BI** | `powerbi/SPEC_powerbi.md` (modèle, mesures DAX, 5 pages) |
| **Looker Studio** (ex-Data Studio) | `looker_studio/SPEC_looker_studio.md` |
| **Excel** | `data/exports/KPI_pilotage_fibre.xlsx` (7 onglets) |
| **Power Automate / process mining** | `power_automate/`, `scripts/03_process_mining.py` |
| **Agents IA** | `ai_agent/agent_insights.py` (mode LLM Claude ou fallback hors-ligne) |

## Architecture

```
Sources (CSV / BigQuery)                 Restitution
  commandes ─┐                            ┌─ Power BI (DAX, 5 pages)
  evenements ─┤   ┌───────────────┐       ├─ Looker Studio
  interventions ──┤  DATAMART      ├──────┤─ Excel (KPI)
  satisfaction ─┘  │ faits_parcours│      └─ Power Automate (alertes/reporting)
                   └──────┬────────┘
                          ├─ Process mining (variantes, goulots)
                          ├─ Scoring risque (sklearn / BigQuery ML)
                          └─ Agent IA → note d'analyse + plan d'actions
```

## Démarrage rapide

```bash
pip install -r requirements.txt
python scripts/run_all.py            # lance tout le pipeline (ou : make all)
```

Étapes individuelles :

```bash
make data      # 1. génère les données fictives
make mart      # 2. construit le datamart (croisement des sources)
make mining    # 3. process mining du parcours
make scoring   # 4. modèle de scoring du risque
make kpi       # 5. export KPI Excel/CSV
make agent     # 6. agent IA : note d'analyse + plan d'actions
```

L'agent IA fonctionne **hors-ligne** par défaut (moteur de règles). Pour le
brancher sur un vrai LLM : `export ANTHROPIC_API_KEY=...` puis `make agent`.

## Principaux résultats (données de démonstration, seed 42)

- **64 %** des livraisons dans les délais (SLA 15 j), délai moyen **13,9 j**.
- Multi-canalité : **Boutique** 69,7 % (NPS 45) vs **Distributeur** 56,8 % (NPS 14).
- Process mining : goulot principal **« Prise de RDV → Construction ligne »** (12,5 j/cas).
- Scoring : **AUC 0,88** ; facteurs de risque = zone à construire, sous-traitant OptiReseau, canal Distributeur.
- **422** commandes en cours scorées, dont **149** à risque élevé et **44** en alerte SLA.

## Structure du dépôt

```
scripts/        pipeline Python (génération, datamart, mining, scoring, KPI, orchestration)
sql/bigquery/   équivalent GCP/BigQuery (SQL + BigQuery ML)
powerbi/        spécification du rapport Power BI (mesures DAX)
looker_studio/  spécification du tableau de bord Looker Studio
power_automate/ flux d'automatisation (alertes, reporting)
ai_agent/       agent IA d'aide à la décision
data/exports/   résultats versionnés (KPI, process mining, scoring)
docs/           cadrage, dictionnaire de données, plan d'actions, note auto
```

## Technologies

Python (pandas, scikit-learn, openpyxl) · SQL BigQuery / BigQuery ML ·
Power BI (DAX) · Looker Studio · Excel · Power Automate · Agent IA (Claude).
