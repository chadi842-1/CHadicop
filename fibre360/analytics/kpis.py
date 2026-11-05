"""
fibre360.analytics.kpis
======================
Calcul des indicateurs de pilotage selon differents axes d'analyse.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from fibre360.config import Config, get_logger

log = get_logger("fibre360.kpis")


def kpi_par(faits: pd.DataFrame, dim) -> pd.DataFrame:
    livrees = faits[faits.statut_parcours == "Livree"]
    g, gl = faits.groupby(dim), livrees.groupby(dim)
    out = pd.DataFrame({
        "nb_commandes": g.size(),
        "nb_livrees": gl.size(),
        "delai_moyen_j": gl.delai_livraison_j.mean().round(1),
        "taux_livraison_delai_pct": (gl.livree_dans_delai.mean() * 100).round(1),
        "taux_echec_pct": g.statut_parcours.apply(
            lambda s: (s == "Echec raccordement").mean() * 100).round(1),
        "taux_annulation_pct": g.statut_parcours.apply(
            lambda s: (s == "Annulee").mean() * 100).round(1),
        "nps_moyen": gl.nps.mean().round(0),
        "taux_reclamation_pct": (gl.reclamation.mean() * 100).round(1),
        "taux_churn_pct": (g.churn.mean() * 100).round(1),
    })
    return out.reset_index().sort_values("nb_commandes", ascending=False)


def synthese(faits: pd.DataFrame, cfg: Config) -> pd.DataFrame:
    liv = faits[faits.statut_parcours == "Livree"]
    sla = cfg.business.sla_jours
    data = [
        ("Commandes totales", f"{len(faits):,}"),
        ("Commandes livrees", f"{len(liv):,}"),
        ("Commandes en cours", f"{(faits.statut_parcours=='En cours').sum():,}"),
        ("Taux de livraison dans les delais",
         f"{liv.livree_dans_delai.mean()*100:.1f}%"),
        ("Delai moyen (commande -> mise en service)",
         f"{liv.delai_livraison_j.mean():.1f} j"),
        ("Objectif SLA", f"{sla} j"),
        ("Taux d'echec de raccordement",
         f"{(faits.statut_parcours=='Echec raccordement').mean()*100:.1f}%"),
        ("Taux d'annulation",
         f"{(faits.statut_parcours=='Annulee').mean()*100:.1f}%"),
        ("NPS moyen (livrees)", f"{liv.nps.mean():.0f}"),
        ("Taux de reclamation", f"{liv.reclamation.mean()*100:.1f}%"),
        ("Taux de churn client", f"{faits.churn.mean()*100:.1f}%"),
        ("CA mensuel recurrent (livrees)",
         f"{liv.montant_mensuel.sum():,.0f} EUR"),
        ("Alertes SLA en cours", f"{faits.alerte_sla.sum():,}"),
    ]
    return pd.DataFrame(data, columns=["Indicateur", "Valeur"])


def tous_les_kpis(faits: pd.DataFrame, cfg: Config) -> dict[str, pd.DataFrame]:
    return {
        "Synthese": synthese(faits, cfg),
        "Par_canal": kpi_par(faits, "canal"),
        "Par_offre": kpi_par(faits, "offre"),
        "Par_region": kpi_par(faits, "region"),
        "Par_departement": kpi_par(faits, "departement"),
        "Par_portefeuille": kpi_par(faits, "gestionnaire_portefeuille"),
        "Par_sous_traitant": kpi_par(faits, "sous_traitant"),
        "Par_segment": kpi_par(faits, "segment"),
        "Par_mois": kpi_par(faits, "annee_mois").sort_values("annee_mois"),
    }
