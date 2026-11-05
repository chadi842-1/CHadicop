"""
fibre360.reporting.powerbi_export
=================================
Exporte un MODELE EN ETOILE prêt pour Power BI à partir du datamart :
- 1 table de faits (grain = commande) avec les mesures additives
- des tables de dimensions (date, canal, offre, region, sous-traitant,
  portefeuille, segment)

Sortie : powerbi/dataset/*.csv  (à charger dans Power BI via "Obtenir les
données > Dossier", les relations se créent automatiquement sur les clés).

Usage : python -m fibre360.reporting.powerbi_export
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from fibre360.config import Config, get_logger

log = get_logger("fibre360.powerbi")


def _dim_date(faits: pd.DataFrame) -> pd.DataFrame:
    d0 = pd.to_datetime(faits.dt_commande).min().normalize()
    d1 = pd.to_datetime(faits.dt_commande).max().normalize()
    rng = pd.date_range(d0, d1, freq="D")
    df = pd.DataFrame({"Date": rng})
    df["Annee"] = df.Date.dt.year
    df["Mois"] = df.Date.dt.month
    df["NomMois"] = df.Date.dt.strftime("%Y-%m")
    df["Trimestre"] = "T" + df.Date.dt.quarter.astype(str) + " " + df.Annee.astype(str)
    df["JourSemaine"] = df.Date.dt.day_name()
    df["EstWeekend"] = df.Date.dt.dayofweek >= 5
    return df


def exporter(cfg: Config, faits: pd.DataFrame | None = None) -> Path:
    if faits is None:
        faits = pd.read_csv(cfg.paths.mart / "faits_parcours.csv",
                            parse_dates=["dt_commande", "dt_mise_en_service"])
    out = cfg.paths.root / "powerbi" / "dataset"
    out.mkdir(parents=True, exist_ok=True)

    # -- Table de faits (grain = commande), colonnes utiles au reporting --
    f = faits.copy()
    f["DateCommande"] = pd.to_datetime(f.dt_commande).dt.normalize()
    fact = pd.DataFrame({
        "IdCommande": f.id_commande,
        "DateCommande": f.DateCommande,
        "Canal": f.canal,
        "Offre": f.offre,
        "Segment": f.segment,
        "Region": f.region,
        "Departement": f.departement.astype(str),
        "Portefeuille": f.gestionnaire_portefeuille,
        "SousTraitant": f.sous_traitant,
        "Statut": f.statut_parcours,
        "ZoneAConstruire": f.zone_a_construire.astype(int),
        "DebitGbps": f.debit_gbps,
        "MontantMensuel": f.montant_mensuel,
        "DelaiLivraisonJ": f.delai_livraison_j,
        "LivreeDansDelai": pd.to_numeric(f.livree_dans_delai, errors="coerce"),
        "EstLivree": (f.statut_parcours == "Livree").astype(int),
        "EstEchec": (f.statut_parcours == "Echec raccordement").astype(int),
        "EstAnnulee": (f.statut_parcours == "Annulee").astype(int),
        "EnCours": (f.statut_parcours == "En cours").astype(int),
        "NbInterventions": f.nb_interventions,
        "NPS": f.nps,
        "NbReclamations": f.nb_reclamations,
        "Reclamation": f.reclamation.astype(int),
        "CAFacture": f.ca_facture,
        "Churn": f.churn.astype("Int64"),
        "AgeJours": f.age_jours,
        "AlerteSLA": f.alerte_sla.astype(int),
    })
    fact.to_csv(out / "fact_parcours.csv", index=False)

    # -- Dimensions --
    _dim_date(faits).to_csv(out / "dim_date.csv", index=False)

    # dimension sous-traitant enrichie (perf de reference)
    dim_st = (faits.groupby("sous_traitant")
              .agg(TauxReussiteRef=("taux_reussite_ref", "mean"))
              .reset_index().rename(columns={"sous_traitant": "SousTraitant"}))
    dim_st["TauxReussiteRef"] = dim_st.TauxReussiteRef.round(3)
    dim_st.to_csv(out / "dim_sous_traitant.csv", index=False)

    for col, nom, fichier in [
        ("canal", "Canal", "dim_canal.csv"),
        ("offre", "Offre", "dim_offre.csv"),
        ("region", "Region", "dim_region.csv"),
        ("gestionnaire_portefeuille", "Portefeuille", "dim_portefeuille.csv"),
        ("segment", "Segment", "dim_segment.csv"),
    ]:
        pd.DataFrame({nom: sorted(faits[col].dropna().unique())}).to_csv(
            out / fichier, index=False)

    log.info("Modele en etoile Power BI exporte -> %s (%d lignes de faits)",
             out, len(fact))
    return out


def main():
    cfg = Config()
    exporter(cfg)


if __name__ == "__main__":
    main()
