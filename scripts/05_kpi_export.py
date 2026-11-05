"""
05_kpi_export.py
================
Construit les tables d'indicateurs (KPI) du pilotage Commande -> Livraison et
les exporte dans un classeur Excel multi-onglets, directement exploitable
(Excel / TCD) et comme source "propre" pour Power BI / Looker Studio.

Mission fiche de poste : "enrichir des analyses et rapports deja en place",
"outils de requetage et de Data Visualisation (Power BI ... Excel/VBA)".

Sortie : data/exports/KPI_pilotage_fibre.xlsx (onglets) + CSV par vue.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
MART = ROOT / "data" / "mart"
EXPORTS = ROOT / "data" / "exports"
SLA = 15


def charger():
    f = pd.read_csv(MART / "faits_parcours.csv")
    return f


def kpi_par(df: pd.DataFrame, dim) -> pd.DataFrame:
    """Agrege les KPI cles selon une (ou plusieurs) dimension(s)."""
    livrees = df[df["statut_parcours"] == "Livree"]
    g = df.groupby(dim)
    gl = livrees.groupby(dim)
    out = pd.DataFrame({
        "nb_commandes": g.size(),
        "nb_livrees": gl.size(),
        "delai_moyen_j": gl["delai_livraison_j"].mean().round(1),
        "taux_livraison_delai_%": (gl["livree_dans_delai"].mean() * 100).round(1),
        "taux_echec_%": (g["statut_parcours"].apply(
            lambda s: (s == "Echec raccordement").mean() * 100)).round(1),
        "taux_annulation_%": (g["statut_parcours"].apply(
            lambda s: (s == "Annulee").mean() * 100)).round(1),
        "nps_moyen": gl["nps"].mean().round(0),
        "taux_reclamation_%": (gl["reclamation"].mean() * 100).round(1),
    })
    return out.reset_index().sort_values("nb_commandes", ascending=False)


def synthese(df: pd.DataFrame) -> pd.DataFrame:
    livrees = df[df["statut_parcours"] == "Livree"]
    lignes = [
        ("Commandes totales", f"{len(df):,}"),
        ("Commandes livrees", f"{len(livrees):,}"),
        ("Commandes en cours", f"{(df['statut_parcours']=='En cours').sum():,}"),
        ("Taux de livraison dans les delais",
         f"{livrees['livree_dans_delai'].mean()*100:.1f}%"),
        ("Delai moyen commande -> mise en service",
         f"{livrees['delai_livraison_j'].mean():.1f} j"),
        ("Objectif SLA", f"{SLA} j"),
        ("Taux d'echec de raccordement",
         f"{(df['statut_parcours']=='Echec raccordement').mean()*100:.1f}%"),
        ("Taux d'annulation",
         f"{(df['statut_parcours']=='Annulee').mean()*100:.1f}%"),
        ("NPS moyen (livrees)", f"{livrees['nps'].mean():.0f}"),
        ("Taux de reclamation", f"{livrees['reclamation'].mean()*100:.1f}%"),
        ("Alertes SLA en cours", f"{df['alerte_sla'].sum():,}"),
    ]
    return pd.DataFrame(lignes, columns=["Indicateur", "Valeur"])


def main():
    EXPORTS.mkdir(parents=True, exist_ok=True)
    df = charger()

    vues = {
        "Synthese": synthese(df),
        "Par_canal": kpi_par(df, "canal"),
        "Par_offre": kpi_par(df, "offre"),
        "Par_region": kpi_par(df, "region"),
        "Par_portefeuille": kpi_par(df, "gestionnaire_portefeuille"),
        "Par_sous_traitant": kpi_par(df, "sous_traitant"),
        "Par_mois": kpi_par(df, "annee_mois").sort_values("annee_mois"),
    }

    xlsx = EXPORTS / "KPI_pilotage_fibre.xlsx"
    with pd.ExcelWriter(xlsx, engine="openpyxl") as writer:
        for onglet, data in vues.items():
            data.to_excel(writer, sheet_name=onglet[:31], index=False)
            # export CSV parallele pour la BI
            data.to_csv(EXPORTS / f"kpi_{onglet.lower()}.csv", index=False)

    print("=" * 60)
    print("EXPORT KPI - Pilotage Commande -> Livraison Fibre")
    print("=" * 60)
    print(synthese(df).to_string(index=False))
    print("\n--- Multi-canalite : performance par canal ---")
    print(vues["Par_canal"][["canal", "nb_commandes",
          "taux_livraison_delai_%", "taux_echec_%", "nps_moyen"]]
          .to_string(index=False))
    print(f"\nOK : classeur Excel ecrit -> {xlsx}")


if __name__ == "__main__":
    main()
