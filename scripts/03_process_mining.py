"""
03_process_mining.py
=====================
Analyse de PROCESS MINING du parcours Commande -> Livraison a partir du
journal d'evenements (equivalent de ce que l'on ferait avec Celonis / UiPath
Process Mining, mais en Python pour la maitrise et la reproductibilite).

Mission fiche de poste : "differents outils d'analyse de processus
(UI Path, Celonis)" + "enrichir la connaissance des parcours".

Produit :
  - data/exports/pm_variantes.csv       : variantes du parcours + frequence + delai
  - data/exports/pm_transitions.csv     : matrice des transitions (flux)
  - data/exports/pm_goulots.csv         : temps moyen par transition (goulots)
  - data/exports/pm_rework.csv          : taux de retour / boucles
  - affichage console : happy path, conformite, goulots principaux
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
EXPORTS = ROOT / "data" / "exports"

# Chemin "ideal" attendu (happy path de reference pour le controle de conformite)
HAPPY_PATH = (
    "Commande enregistree -> Etude eligibilite -> Prise de RDV -> "
    "Intervention technicien -> Mise en service"
)


def charger_event_log() -> pd.DataFrame:
    ev = pd.read_csv(RAW / "evenements.csv", parse_dates=["horodatage"])
    ev = ev.sort_values(["id_commande", "horodatage"])
    return ev


def variantes(ev: pd.DataFrame) -> pd.DataFrame:
    """Chaque commande = une sequence d'activites -> on compte les variantes."""
    seq = (ev.groupby("id_commande")["etape"]
             .apply(lambda s: " -> ".join(s))
             .rename("variante"))
    delai = (ev.groupby("id_commande")["horodatage"]
               .apply(lambda s: (s.max() - s.min()).total_seconds() / 86400)
               .rename("delai_j"))
    df = pd.concat([seq, delai], axis=1)
    out = (df.groupby("variante")
             .agg(nb_cas=("delai_j", "size"),
                  delai_moyen_j=("delai_j", "mean"))
             .sort_values("nb_cas", ascending=False)
             .reset_index())
    out["part_pct"] = (out["nb_cas"] / out["nb_cas"].sum() * 100).round(1)
    out["delai_moyen_j"] = out["delai_moyen_j"].round(1)
    return out


def transitions(ev: pd.DataFrame) -> pd.DataFrame:
    """Matrice des flux : de l'activite A vers l'activite B."""
    ev = ev.copy()
    ev["etape_suivante"] = ev.groupby("id_commande")["etape"].shift(-1)
    ev["t_suivant"] = ev.groupby("id_commande")["horodatage"].shift(-1)
    trans = ev.dropna(subset=["etape_suivante"]).copy()
    trans["duree_j"] = (
        (trans["t_suivant"] - trans["horodatage"]).dt.total_seconds() / 86400)
    agg = (trans.groupby(["etape", "etape_suivante"])
                .agg(nb=("duree_j", "size"), duree_moyenne_j=("duree_j", "mean"))
                .reset_index()
                .sort_values("nb", ascending=False))
    agg["duree_moyenne_j"] = agg["duree_moyenne_j"].round(2)
    return agg


def goulots(trans: pd.DataFrame) -> pd.DataFrame:
    """Transitions les plus lentes ponderees par volume = goulots d'etranglement."""
    g = trans.copy()
    g["impact_j"] = (g["duree_moyenne_j"] * g["nb"]).round(0)
    g["transition"] = g["etape"] + " -> " + g["etape_suivante"]
    return (g[["transition", "nb", "duree_moyenne_j", "impact_j"]]
            .sort_values("duree_moyenne_j", ascending=False)
            .reset_index(drop=True))


def rework(ev: pd.DataFrame) -> pd.DataFrame:
    """Detecte les retours en arriere / repetitions d'activite (rework)."""
    rep = (ev.groupby(["id_commande", "etape"]).size()
             .reset_index(name="occurrences"))
    rep = rep[rep["occurrences"] > 1]
    if rep.empty:
        return pd.DataFrame(columns=["etape", "cas_avec_repetition"])
    return (rep.groupby("etape")["id_commande"].nunique()
               .reset_index(name="cas_avec_repetition")
               .sort_values("cas_avec_repetition", ascending=False))


def main():
    EXPORTS.mkdir(parents=True, exist_ok=True)
    ev = charger_event_log()

    var = variantes(ev)
    trans = transitions(ev)
    gl = goulots(trans)
    rw = rework(ev)

    var.to_csv(EXPORTS / "pm_variantes.csv", index=False)
    trans.to_csv(EXPORTS / "pm_transitions.csv", index=False)
    gl.to_csv(EXPORTS / "pm_goulots.csv", index=False)
    rw.to_csv(EXPORTS / "pm_rework.csv", index=False)

    n_cas = ev["id_commande"].nunique()
    conformes = var[var["variante"] == HAPPY_PATH]["nb_cas"].sum()

    print("=" * 70)
    print("PROCESS MINING - Parcours Commande -> Livraison Fibre")
    print("=" * 70)
    print(f"Cas analyses              : {n_cas:,}")
    print(f"Nombre de variantes       : {len(var)}")
    print(f"Happy path de reference   : {HAPPY_PATH}")
    print(f"Taux de conformite        : {conformes / n_cas * 100:.1f}% "
          f"({conformes:,} cas)")
    print("\n--- Top 5 variantes ---")
    for r in var.head(5).itertuples(index=False):
        print(f"  {r.part_pct:>5.1f}%  ({r.nb_cas:>5,} cas, {r.delai_moyen_j:>4.1f} j)"
              f"  {r.variante[:70]}")
    print("\n--- Principaux goulots (transitions les plus lentes) ---")
    for r in gl.head(5).itertuples(index=False):
        print(f"  {r.duree_moyenne_j:>5.2f} j/cas  (vol {int(r.nb):>5,})  {r.transition}")
    print(f"\nOK : exports process mining ecrits dans {EXPORTS}")


if __name__ == "__main__":
    main()
