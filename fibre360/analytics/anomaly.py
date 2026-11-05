"""
fibre360.analytics.anomaly
=========================
Detection d'anomalies sur les series quotidiennes de KPI
(volume de commandes, taux d'echec) via un z-score glissant robuste.
Permet d'alerter sur des ruptures (ex : panne SI, probleme sous-traitant).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from fibre360.config import Config, get_logger

log = get_logger("fibre360.anomaly")


def _zscore_glissant(s: pd.Series, fenetre: int = 28, seuil: float = 3.0):
    med = s.rolling(fenetre, min_periods=fenetre // 2).median()
    mad = (s - med).abs().rolling(fenetre, min_periods=fenetre // 2).median()
    # MAD -> ecart-type robuste (facteur 1.4826)
    sigma = 1.4826 * mad.replace(0, np.nan)
    z = (s - med) / sigma
    return z, z.abs() > seuil


def detecter(cfg: Config, faits: pd.DataFrame, seuil: float = 3.0) -> pd.DataFrame:
    f = faits.copy()
    f["jour"] = pd.to_datetime(f.dt_commande).dt.normalize()
    quotidien = f.groupby("jour").agg(
        nb_commandes=("id_commande", "count"),
        taux_echec=("statut_parcours",
                    lambda s: (s == "Echec raccordement").mean()),
    ).sort_index()

    res = quotidien.copy()
    for col in ("nb_commandes", "taux_echec"):
        z, flag = _zscore_glissant(quotidien[col], seuil=seuil)
        res[f"z_{col}"] = z.round(2)
        res[f"anomalie_{col}"] = flag.fillna(False)

    anomalies = res[res.anomalie_nb_commandes | res.anomalie_taux_echec].copy()
    anomalies = anomalies.reset_index()
    log.info("Anomalies : %d jours signales sur %d", len(anomalies), len(res))
    return anomalies[["jour", "nb_commandes", "z_nb_commandes",
                      "taux_echec", "z_taux_echec",
                      "anomalie_nb_commandes", "anomalie_taux_echec"]]
