"""
fibre360.analytics.cohorts
==========================
Analyse de cohortes / retention : pour chaque mois de mise en service,
suit la part de clients encore actifs (non resilies) a M+1, M+3, M+6, M+12.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from fibre360.config import Config, get_logger

log = get_logger("fibre360.cohorts")


def retention(cfg: Config, faits: pd.DataFrame) -> pd.DataFrame:
    liv = faits[faits.statut_parcours == "Livree"].copy()
    liv["cohorte"] = pd.to_datetime(liv.dt_mise_en_service).dt.to_period("M")
    liv["dt_resil"] = pd.to_datetime(liv.date_resiliation)
    ref = pd.Timestamp(cfg.business.date_reference)

    horizons = [0, 1, 3, 6, 12]
    lignes = []
    for cohorte, grp in liv.groupby("cohorte"):
        base_date = cohorte.to_timestamp()
        n = len(grp)
        if n < 30:   # on ignore les cohortes trop petites (bruit)
            continue
        row = {"cohorte": str(cohorte), "taille": n}
        for h in horizons:
            cible = base_date + pd.DateOffset(months=h)
            if cible > ref:
                row[f"M+{h}"] = np.nan   # horizon non encore observable
                continue
            # actif a l'horizon = pas de resiliation avant 'cible'
            resilie = grp.dt_resil.notna() & (grp.dt_resil <= cible)
            row[f"M+{h}"] = round((1 - resilie.mean()) * 100, 1)
        lignes.append(row)

    out = pd.DataFrame(lignes).sort_values("cohorte")
    log.info("Cohortes : %d cohortes mensuelles analysees", len(out))
    return out


def retention_par_canal(cfg: Config, faits: pd.DataFrame) -> pd.DataFrame:
    """Retention a 12 mois par canal d'acquisition (qualite du recrutement)."""
    liv = faits[faits.statut_parcours == "Livree"].copy()
    liv["dt_resil"] = pd.to_datetime(liv.date_resiliation)
    liv["dt_mes"] = pd.to_datetime(liv.dt_mise_en_service)
    ref = pd.Timestamp(cfg.business.date_reference)
    # on ne garde que les clients observables a 12 mois
    obs = liv[liv.dt_mes + pd.DateOffset(months=12) <= ref]
    if obs.empty:
        return pd.DataFrame(columns=["canal", "clients_observables", "retention_12m_pct"])
    g = obs.groupby("canal")
    out = pd.DataFrame({
        "clients_observables": g.size(),
        "retention_12m_pct": g.apply(
            lambda d: (1 - (d.dt_resil.notna()
                            & (d.dt_resil <= d.dt_mes + pd.DateOffset(months=12)))
                       .mean()) * 100, include_groups=False).round(1),
    }).reset_index().sort_values("retention_12m_pct", ascending=False)
    return out
