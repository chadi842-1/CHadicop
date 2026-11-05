# Fibre 360 - orchestration de la plateforme
PY   ?= python3
N    ?= 60000
SEED ?= 42

.PHONY: help install all generate quality datamart analytics report test clean

help:        ## Affiche cette aide
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
	 awk 'BEGIN{FS=":.*?## "}{printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

install:     ## Installe les dependances
	$(PY) -m pip install -r requirements.txt

all:         ## Pipeline complet (generation -> datamart -> analytics/ML -> reporting)
	$(PY) -m fibre360.cli all --n $(N) --seed $(SEED)

generate:    ## Genere uniquement les donnees
	$(PY) -m fibre360.cli generate --n $(N) --seed $(SEED)

quality:     ## Controle qualite des donnees
	$(PY) -m fibre360.cli quality

datamart:    ## Construit le datamart
	$(PY) -m fibre360.cli datamart

analytics:   ## Analytics + ML (sans reecrire les livrables)
	$(PY) -m fibre360.cli analytics

report:      ## Exports Excel/CSV + dashboard + note IA
	$(PY) -m fibre360.cli report

test:        ## Lance la suite de tests
	$(PY) -m pytest -q

clean:       ## Supprime les donnees generees (garde exports/dashboard/docs)
	rm -rf data/raw/*.csv data/mart/*.csv models/*.joblib
