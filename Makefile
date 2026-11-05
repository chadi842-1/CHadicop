# Fibre 360 - orchestration du pipeline d'analyse
PY ?= python3
N  ?= 12000
SEED ?= 42

.PHONY: all install data mart mining scoring kpi agent clean

all:        ## Lance tout le pipeline
	$(PY) scripts/run_all.py --n $(N) --seed $(SEED)

install:    ## Installe les dependances Python
	$(PY) -m pip install -r requirements.txt

data:       ## Genere les donnees brutes
	$(PY) scripts/01_generate_data.py --n $(N) --seed $(SEED)

mart:       ## Construit le datamart
	$(PY) scripts/02_build_datamart.py

mining:     ## Process mining
	$(PY) scripts/03_process_mining.py

scoring:    ## Modele de scoring
	$(PY) scripts/04_scoring_model.py

kpi:        ## Export KPI Excel/CSV
	$(PY) scripts/05_kpi_export.py

agent:      ## Agent IA (note d'analyse + plan d'actions)
	$(PY) ai_agent/agent_insights.py

clean:      ## Supprime les donnees generees (garde les exports)
	rm -rf data/raw/*.csv data/mart/*.csv
