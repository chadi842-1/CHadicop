"""
run_all.py
==========
Orchestre l'ensemble du pipeline Fibre 360 de bout en bout :
  1. generation des donnees        (01_generate_data.py)
  2. construction du datamart       (02_build_datamart.py)
  3. process mining                 (03_process_mining.py)
  4. modele de scoring              (04_scoring_model.py)
  5. export KPI (Excel/CSV)         (05_kpi_export.py)
  6. agent IA (note + plan)         (ai_agent/agent_insights.py)

Usage : python scripts/run_all.py [--n 12000] [--seed 42]
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

ETAPES = [
    ("Generation des donnees", ["scripts/01_generate_data.py"], True),
    ("Construction du datamart", ["scripts/02_build_datamart.py"], False),
    ("Process mining", ["scripts/03_process_mining.py"], False),
    ("Modele de scoring", ["scripts/04_scoring_model.py"], False),
    ("Export KPI Excel/CSV", ["scripts/05_kpi_export.py"], False),
    ("Agent IA - note d'analyse", ["ai_agent/agent_insights.py"], False),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=12000)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    for i, (titre, cmd, prend_args) in enumerate(ETAPES, 1):
        print("\n" + "#" * 72)
        print(f"# ETAPE {i}/{len(ETAPES)} : {titre}")
        print("#" * 72)
        full = [sys.executable] + cmd
        if prend_args:
            full += ["--n", str(args.n), "--seed", str(args.seed)]
        res = subprocess.run(full, cwd=ROOT)
        if res.returncode != 0:
            print(f"\n!! Echec a l'etape '{titre}' (code {res.returncode})")
            sys.exit(res.returncode)

    print("\n" + "=" * 72)
    print("PIPELINE FIBRE 360 TERMINE AVEC SUCCES")
    print("  - Datamart        : data/mart/faits_parcours.csv")
    print("  - Exports KPI     : data/exports/KPI_pilotage_fibre.xlsx")
    print("  - Note d'analyse  : docs/note_analyse_auto.md")
    print("=" * 72)


if __name__ == "__main__":
    main()
