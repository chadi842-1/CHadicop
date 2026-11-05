"""
fibre360.analytics.process_mining
=================================
Analyse de process mining du parcours Commande -> Livraison :
variantes, matrice de transitions, goulots, rework, conformite au happy path,
et performance SLA par variante.
"""
from __future__ import annotations

import pandas as pd

from fibre360 import config as C
from fibre360.config import Config, get_logger

log = get_logger("fibre360.pm")


def event_log(cfg: Config) -> pd.DataFrame:
    ev = pd.read_csv(cfg.paths.raw / "evenements.csv", parse_dates=["horodatage"])
    return ev.sort_values(["id_commande", "horodatage"])


def variantes(ev: pd.DataFrame) -> pd.DataFrame:
    seq = ev.groupby("id_commande").etape.apply(lambda s: " -> ".join(s)).rename("variante")
    delai = ev.groupby("id_commande").horodatage.apply(
        lambda s: (s.max() - s.min()).total_seconds() / 86400).rename("delai_j")
    df = pd.concat([seq, delai], axis=1)
    out = (df.groupby("variante").agg(nb_cas=("delai_j", "size"),
                                      delai_moyen_j=("delai_j", "mean"))
           .sort_values("nb_cas", ascending=False).reset_index())
    out["part_pct"] = (out.nb_cas / out.nb_cas.sum() * 100).round(1)
    out["delai_moyen_j"] = out.delai_moyen_j.round(1)
    return out


def transitions(ev: pd.DataFrame) -> pd.DataFrame:
    ev = ev.copy()
    ev["etape_suivante"] = ev.groupby("id_commande").etape.shift(-1)
    ev["t_suivant"] = ev.groupby("id_commande").horodatage.shift(-1)
    tr = ev.dropna(subset=["etape_suivante"]).copy()
    tr["duree_j"] = (tr.t_suivant - tr.horodatage).dt.total_seconds() / 86400
    agg = (tr.groupby(["etape", "etape_suivante"])
           .agg(nb=("duree_j", "size"), duree_moyenne_j=("duree_j", "mean"),
                duree_mediane_j=("duree_j", "median"))
           .reset_index().sort_values("nb", ascending=False))
    for c in ("duree_moyenne_j", "duree_mediane_j"):
        agg[c] = agg[c].round(2)
    return agg


def goulots(tr: pd.DataFrame) -> pd.DataFrame:
    g = tr.copy()
    g["transition"] = g.etape + " -> " + g.etape_suivante
    g["impact_j_total"] = (g.duree_moyenne_j * g.nb).round(0)
    return (g[["transition", "nb", "duree_moyenne_j", "duree_mediane_j", "impact_j_total"]]
            .sort_values("duree_moyenne_j", ascending=False).reset_index(drop=True))


def rework(ev: pd.DataFrame) -> pd.DataFrame:
    rep = ev.groupby(["id_commande", "etape"]).size().reset_index(name="occ")
    rep = rep[rep.occ > 1]
    if rep.empty:
        return pd.DataFrame(columns=["etape", "cas_avec_repetition"])
    return (rep.groupby("etape").id_commande.nunique()
            .reset_index(name="cas_avec_repetition")
            .sort_values("cas_avec_repetition", ascending=False))


def analyser(cfg: Config) -> dict[str, pd.DataFrame]:
    ev = event_log(cfg)
    var, tr = variantes(ev), transitions(ev)
    gl, rw = goulots(tr), rework(ev)
    n = ev.id_commande.nunique()
    conformes = var[var.variante == C.HAPPY_PATH].nb_cas.sum()
    resume = pd.DataFrame([
        ("Cas analyses", n),
        ("Nombre de variantes", len(var)),
        ("Cas conformes (happy path)", int(conformes)),
        ("Taux de conformite %", round(conformes / n * 100, 1)),
    ], columns=["Indicateur", "Valeur"])
    log.info("Process mining : %d variantes, conformite %.1f%%",
             len(var), conformes / n * 100)
    return {"pm_variantes": var, "pm_transitions": tr, "pm_goulots": gl,
            "pm_rework": rw, "pm_resume": resume}
