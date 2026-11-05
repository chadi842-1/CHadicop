"""
fibre360.cli
===========
Point d'entree en ligne de commande de la plateforme Fibre 360.

Exemples :
  python -m fibre360.cli all               # pipeline complet
  python -m fibre360.cli generate --n 20000
  python -m fibre360.cli report
  python -m fibre360.cli --help
"""
from __future__ import annotations

import argparse
import time

import pandas as pd

from fibre360.config import Config, get_logger

log = get_logger("fibre360.cli")


def _etape(nom):
    def deco(fn):
        def wrap(*a, **k):
            t = time.perf_counter()
            log.info("=> %s", nom)
            r = fn(*a, **k)
            log.info("   %s termine en %.1fs", nom, time.perf_counter() - t)
            return r
        return wrap
    return deco


@_etape("Generation des donnees")
def step_generate(cfg):
    from fibre360.data_generation.generators import generer_et_ecrire
    return generer_et_ecrire(cfg)


@_etape("Controle qualite")
def step_quality(cfg, tables):
    from fibre360.pipeline.data_quality import ControleQualite
    return ControleQualite(cfg).rapport(tables)


@_etape("Construction du datamart")
def step_datamart(cfg, tables):
    from fibre360.pipeline.datamart import construire_et_ecrire
    return construire_et_ecrire(cfg, tables)


@_etape("Analytics & ML")
def step_analytics(cfg, faits):
    from fibre360.analytics import (anomaly, cohorts, forecasting, kpis,
                                    process_mining, segmentation)
    from fibre360.ml import churn, train

    res = {}
    res.update({k.lower(): v for k, v in kpis.tous_les_kpis(faits, cfg).items()})
    res["synthese"] = kpis.synthese(faits, cfg)
    res.update(process_mining.analyser(cfg))
    res["retention_cohortes"] = cohorts.retention(cfg, faits)
    res["retention_canal"] = cohorts.retention_par_canal(cfg, faits)
    res["forecast"] = forecasting.prevoir(cfg, faits, horizon=3)
    res["anomalies"] = anomaly.detecter(cfg, faits)
    res.update(segmentation.segmenter(cfg, faits))

    r = train.entrainer(cfg, faits)
    res["comparaison_modeles"] = r["comparaison"]
    res["importances"] = r["importances"]
    res["scores_en_cours"] = r["scores_en_cours"]
    res["risque_auc"] = round(float(r["auc"]), 4)

    c = churn.entrainer(cfg, faits)
    res["churn_clients_a_risque"] = c["clients_a_risque"]
    res["churn_auc"] = c["auc"]
    return res


@_etape("Exports & reporting")
def step_report(cfg, res):
    from fibre360.reporting.excel_report import construire_classeur
    from fibre360.reporting.dashboard import generer as gen_dash
    from fibre360.reporting.insights import rediger

    vues = {
        "Synthese": res["synthese"],
        "Par_canal": res["par_canal"], "Par_offre": res["par_offre"],
        "Par_region": res["par_region"], "Par_portefeuille": res["par_portefeuille"],
        "Par_sous_traitant": res["par_sous_traitant"], "Par_segment": res["par_segment"],
        "Par_mois": res["par_mois"],
        "PM_variantes": res["pm_variantes"], "PM_goulots": res["pm_goulots"],
        "PM_resume": res["pm_resume"],
        "Comparaison_modeles": res["comparaison_modeles"],
        "Importances": res["importances"],
        "Scoring_en_cours": res["scores_en_cours"],
        "Churn_a_risque": res["churn_clients_a_risque"],
        "Retention_cohortes": res["retention_cohortes"],
        "Retention_canal": res["retention_canal"],
        "Prevision": res["forecast"],
        "Anomalies": res["anomalies"],
        "Segments": res["segmentation_profils"],
    }
    xlsx = construire_classeur(cfg, vues)
    dash = gen_dash(cfg, res)
    note = rediger(cfg, res)
    return xlsx, dash, note


def run_all(cfg: Config):
    t0 = time.perf_counter()
    tables = step_generate(cfg)
    step_quality(cfg, tables)
    faits = step_datamart(cfg, tables)
    res = step_analytics(cfg, faits)
    xlsx, dash, note = step_report(cfg, res)
    log.info("=" * 60)
    log.info("PIPELINE COMPLET en %.1fs", time.perf_counter() - t0)
    log.info("  Datamart   : %s", cfg.paths.mart / "faits_parcours.csv")
    log.info("  Excel      : %s", xlsx)
    log.info("  Dashboard  : %s", dash)
    log.info("  Note IA    : %s", note)
    log.info("=" * 60)
    return res


def main(argv=None):
    ap = argparse.ArgumentParser(prog="fibre360", description="Plateforme Fibre 360")
    ap.add_argument("commande", nargs="?", default="all",
                    choices=["all", "generate", "quality", "datamart",
                             "analytics", "report"],
                    help="etape a executer (defaut: all)")
    ap.add_argument("--n", type=int, help="nombre de commandes a generer")
    ap.add_argument("--seed", type=int, help="graine aleatoire")
    ap.add_argument("--config", help="chemin d'un config.yaml")
    args = ap.parse_args(argv)

    cfg = Config.load(args.config)
    if args.n:
        cfg.n_commandes = args.n
    if args.seed:
        cfg.seed = args.seed
    cfg.paths.ensure()

    if args.commande == "all":
        run_all(cfg)
    elif args.commande == "generate":
        step_generate(cfg)
    else:
        # les etapes intermediaires rechargent ce dont elles ont besoin du disque
        from fibre360.pipeline.datamart import charger_raw, construire_et_ecrire
        if args.commande == "quality":
            step_quality(cfg, charger_raw(cfg))
        elif args.commande == "datamart":
            step_datamart(cfg, charger_raw(cfg))
        elif args.commande == "analytics":
            faits = pd.read_csv(cfg.paths.mart / "faits_parcours.csv")
            step_analytics(cfg, faits)
        elif args.commande == "report":
            faits = pd.read_csv(cfg.paths.mart / "faits_parcours.csv")
            res = step_analytics(cfg, faits)
            step_report(cfg, res)


if __name__ == "__main__":
    main()
