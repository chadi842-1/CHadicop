"""
02_build_datamart.py
====================
Croise les 4 sources brutes et construit la table de faits du parcours
Commande -> Livraison, prete pour la BI (Power BI / Looker Studio) et le scoring.

Mission fiche de poste : "croiser plusieurs sources de donnees",
"enrichir les analyses et rapports deja en place".

Entrees  : data/raw/*.csv
Sortie   : data/mart/faits_parcours.csv   (1 ligne = 1 commande, enrichie)
           data/mart/dim_temps.csv         (dimension calendrier)
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
MART = ROOT / "data" / "mart"
SLA_JOURS = 15


def load() -> dict[str, pd.DataFrame]:
    d = {}
    for name in ("commandes", "evenements", "interventions", "satisfaction"):
        df = pd.read_csv(RAW / f"{name}.csv")
        for col in df.columns:
            if "date" in col or col == "horodatage":
                df[col] = pd.to_datetime(df[col], errors="coerce")
        d[name] = df
    return d


def build_faits(d: dict[str, pd.DataFrame]) -> pd.DataFrame:
    cmd = d["commandes"].copy()
    ev = d["evenements"]
    it = d["interventions"]
    sa = d["satisfaction"]

    # --- Jalons cles extraits du journal d'evenements (pivot) ------------- #
    def premiere_date(etape):
        s = (ev[ev["etape"] == etape]
             .groupby("id_commande")["horodatage"].min())
        return s

    dt_cmd = premiere_date("Commande enregistree")
    dt_mes = premiere_date("Mise en service")
    dt_echec = premiere_date("Echec raccordement")
    dt_annul = premiere_date("Annulation client")

    cmd = cmd.set_index("id_commande")
    cmd["dt_commande"] = dt_cmd
    cmd["dt_mise_en_service"] = dt_mes
    cmd["dt_echec"] = dt_echec
    cmd["dt_annulation"] = dt_annul

    # --- Statut final du parcours ---------------------------------------- #
    def statut(row):
        if pd.notna(row["dt_mise_en_service"]):
            return "Livree"
        if pd.notna(row["dt_echec"]):
            return "Echec raccordement"
        if pd.notna(row["dt_annulation"]):
            return "Annulee"
        return "En cours"

    cmd["statut_parcours"] = cmd.apply(statut, axis=1)

    # --- Delai de livraison (jours) et respect du SLA --------------------- #
    cmd["delai_livraison_j"] = (
        (cmd["dt_mise_en_service"] - cmd["dt_commande"]).dt.total_seconds()
        / 86400
    ).round(2)
    cmd["livree_dans_delai"] = np.where(
        cmd["statut_parcours"] == "Livree",
        (cmd["delai_livraison_j"] <= SLA_JOURS).astype("Int64"),
        pd.NA,
    )

    # --- Enrichissement interventions (dernier resultat + motif) ---------- #
    it_last = (it.sort_values("date_realisee")
                 .groupby("id_commande")
                 .agg(resultat_intervention=("resultat", "last"),
                      motif_echec=("motif_echec", "last"),
                      nb_interventions=("id_intervention", "count")))
    cmd = cmd.join(it_last)

    # --- Enrichissement satisfaction ------------------------------------- #
    sa_last = (sa.groupby("id_commande")
                 .agg(nps=("nps", "mean"), reclamation=("reclamation", "max")))
    cmd = cmd.join(sa_last)

    # --- Dimensions temps ------------------------------------------------- #
    cmd["annee_mois"] = cmd["dt_commande"].dt.to_period("M").astype(str)
    cmd["trimestre"] = cmd["dt_commande"].dt.to_period("Q").astype(str)
    cmd["semaine"] = cmd["dt_commande"].dt.isocalendar().week.astype("Int64")

    # --- Indicateur d'alerte (commande en cours a risque de depassement) -- #
    today = pd.Timestamp("2026-11-01")
    age = (today - cmd["dt_commande"]).dt.total_seconds() / 86400
    cmd["age_jours"] = age.round(1)
    cmd["alerte_sla"] = (
        (cmd["statut_parcours"] == "En cours") & (age > SLA_JOURS)
    )

    return cmd.reset_index()


def build_dim_temps(faits: pd.DataFrame) -> pd.DataFrame:
    rng = pd.date_range(faits["dt_commande"].min().normalize(),
                        faits["dt_commande"].max().normalize(), freq="D")
    dim = pd.DataFrame({"date": rng})
    dim["annee"] = dim["date"].dt.year
    dim["mois"] = dim["date"].dt.month
    dim["annee_mois"] = dim["date"].dt.to_period("M").astype(str)
    dim["trimestre"] = dim["date"].dt.to_period("Q").astype(str)
    dim["jour_semaine"] = dim["date"].dt.day_name()
    dim["est_weekend"] = dim["date"].dt.dayofweek >= 5
    return dim


def controle_qualite(faits: pd.DataFrame) -> None:
    """Quelques controles de coherence (data quality)."""
    print("\n--- Controles qualite ---")
    n = len(faits)
    print(f"  Lignes                          : {n:,}")
    print(f"  Repartition statut              : "
          + ", ".join(f"{k}={v}" for k, v in
                      faits['statut_parcours'].value_counts().items()))
    neg = (faits["delai_livraison_j"] < 0).sum()
    print(f"  Delais negatifs (anomalie)      : {neg}")
    liv = faits[faits["statut_parcours"] == "Livree"]
    print(f"  Delai moyen livraison (j)       : {liv['delai_livraison_j'].mean():.1f}")
    print(f"  Taux livraison dans les delais  : "
          f"{liv['livree_dans_delai'].mean()*100:.1f}%")


def main():
    MART.mkdir(parents=True, exist_ok=True)
    d = load()
    faits = build_faits(d)
    dim = build_dim_temps(faits)

    faits.to_csv(MART / "faits_parcours.csv", index=False)
    dim.to_csv(MART / "dim_temps.csv", index=False)
    controle_qualite(faits)
    print(f"\nOK : datamart ecrit dans {MART}")
    print(f"  faits_parcours.csv -> {len(faits):,} lignes, {faits.shape[1]} colonnes")


if __name__ == "__main__":
    main()
