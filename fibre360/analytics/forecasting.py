"""
fibre360.analytics.forecasting
=============================
Prevision des series temporelles mensuelles (volume de commandes et delai
moyen de livraison). Utilise statsmodels (lissage exponentiel de Holt-Winters)
si disponible, sinon un repli deterministe (moyenne mobile + tendance).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from fibre360.config import Config, get_logger

log = get_logger("fibre360.forecast")

try:
    from statsmodels.tsa.holtwinters import ExponentialSmoothing  # type: ignore
    _HAS_SM = True
except Exception:  # pragma: no cover
    _HAS_SM = False


def _series_mensuelles(faits: pd.DataFrame) -> pd.DataFrame:
    f = faits.copy()
    f["mois"] = pd.to_datetime(f.dt_commande).dt.to_period("M").dt.to_timestamp()
    vol = f.groupby("mois").size().rename("nb_commandes")
    liv = f[f.statut_parcours == "Livree"]
    delai = liv.groupby(pd.to_datetime(liv.dt_commande).dt.to_period("M")
                        .dt.to_timestamp()).delai_livraison_j.mean().rename("delai_moyen_j")
    df = pd.concat([vol, delai], axis=1).sort_index()
    # on ecarte le dernier mois (souvent incomplet)
    return df.iloc[:-1]


def _prevoir_serie(y: pd.Series, horizon: int, saison: int = 12) -> np.ndarray:
    y = y.dropna()
    if _HAS_SM and len(y) >= 2 * saison:
        try:
            model = ExponentialSmoothing(
                y, trend="add", seasonal="add", seasonal_periods=saison,
                initialization_method="estimated").fit()
            return np.asarray(model.forecast(horizon))
        except Exception as e:  # pragma: no cover
            log.warning("Holt-Winters indisponible (%s) -> repli", e)
    # repli : moyenne mobile 3 mois + tendance lineaire
    tail = y.tail(6)
    pente = np.polyfit(range(len(tail)), tail.values, 1)[0]
    base = tail.mean()
    return np.array([base + pente * (i + 1) for i in range(horizon)])


def prevoir(cfg: Config, faits: pd.DataFrame, horizon: int = 3) -> pd.DataFrame:
    df = _series_mensuelles(faits)
    futur_index = pd.date_range(df.index[-1] + pd.DateOffset(months=1),
                                periods=horizon, freq="MS")
    out = []
    for mois, v in zip(df.index, df.nb_commandes):
        out.append({"mois": mois.strftime("%Y-%m"), "type": "historique",
                    "nb_commandes": round(v, 0),
                    "delai_moyen_j": round(df.loc[mois, "delai_moyen_j"], 1)})
    f_vol = _prevoir_serie(df.nb_commandes, horizon)
    f_del = _prevoir_serie(df.delai_moyen_j, horizon)
    for i, mois in enumerate(futur_index):
        out.append({"mois": mois.strftime("%Y-%m"), "type": "prevision",
                    "nb_commandes": round(max(0, f_vol[i]), 0),
                    "delai_moyen_j": round(f_del[i], 1)})
    res = pd.DataFrame(out)
    moteur = "Holt-Winters" if _HAS_SM else "moyenne mobile + tendance"
    log.info("Prevision %d mois (%s)", horizon, moteur)
    return res
