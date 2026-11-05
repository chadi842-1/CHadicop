"""
fibre360.pipeline.datamart
==========================
Construit la table de faits du parcours Commande -> Livraison en croisant
les 8 sources (commandes, clients, evenements, interventions, satisfaction,
reclamations, factures, techniciens). 1 ligne = 1 commande enrichie.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from fibre360.config import Config, get_logger

log = get_logger("fibre360.datamart")


def _to_dt(df: pd.DataFrame) -> pd.DataFrame:
    for col in df.columns:
        if "date" in col or col == "horodatage":
            df[col] = pd.to_datetime(df[col], errors="coerce")
    return df


def charger_raw(cfg: Config) -> dict[str, pd.DataFrame]:
    noms = ["clients", "commandes", "evenements", "interventions",
            "satisfaction", "reclamations", "factures", "techniciens"]
    return {n: _to_dt(pd.read_csv(cfg.paths.raw / f"{n}.csv")) for n in noms}


def construire(cfg: Config, tables: dict[str, pd.DataFrame] | None = None
               ) -> pd.DataFrame:
    sla = cfg.business.sla_jours
    t = tables or charger_raw(cfg)
    cmd = t["commandes"].copy().set_index("id_commande")
    ev, it, sa = t["evenements"], t["interventions"], t["satisfaction"]
    rc, fa, cli, tec = t["reclamations"], t["factures"], t["clients"], t["techniciens"]

    def premiere(etape):
        return ev[ev.etape == etape].groupby("id_commande")["horodatage"].min()

    cmd["dt_commande"] = premiere("Commande enregistree")
    cmd["dt_mise_en_service"] = premiere("Mise en service")
    cmd["dt_echec"] = premiere("Echec raccordement")
    cmd["dt_annulation"] = premiere("Annulation client")

    def statut(r):
        if pd.notna(r.dt_mise_en_service):
            return "Livree"
        if pd.notna(r.dt_echec):
            return "Echec raccordement"
        if pd.notna(r.dt_annulation):
            return "Annulee"
        return "En cours"

    cmd["statut_parcours"] = cmd.apply(statut, axis=1)
    cmd["delai_livraison_j"] = (
        (cmd.dt_mise_en_service - cmd.dt_commande).dt.total_seconds() / 86400).round(2)
    cmd["livree_dans_delai"] = np.where(
        cmd.statut_parcours == "Livree",
        (cmd.delai_livraison_j <= sla).astype("Int64"), pd.NA)

    # interventions
    it_last = (it.sort_values("date_realisee").groupby("id_commande")
               .agg(resultat_intervention=("resultat", "last"),
                    motif_echec=("motif_echec", "last"),
                    nb_interventions=("id_intervention", "count")))
    cmd = cmd.join(it_last)

    # satisfaction
    cmd = cmd.join(sa.groupby("id_commande").agg(nps=("nps", "mean")))

    # reclamations
    rc_agg = rc.groupby("id_commande").agg(
        nb_reclamations=("id_reclamation", "count"),
        reclamation_resolue=("resolu", "max"),
        delai_resolution_j=("delai_resolution_j", "mean"))
    cmd = cmd.join(rc_agg)
    cmd["reclamation"] = cmd["nb_reclamations"].fillna(0).gt(0)
    cmd["nb_reclamations"] = cmd["nb_reclamations"].fillna(0).astype(int)

    # chiffre d'affaires facture (3 mois)
    cmd = cmd.join(fa.groupby("id_commande").agg(ca_facture=("montant", "sum")))

    # id_commande repasse en colonne avant les merges (sinon perdu)
    cmd = cmd.reset_index()

    # technicien (taux de reussite de reference)
    cmd = cmd.merge(tec[["id_technicien", "taux_reussite_ref", "anciennete_mois"]]
                    .rename(columns={"anciennete_mois": "anciennete_technicien_mois"}),
                    on="id_technicien", how="left")

    # churn client
    cmd = cmd.merge(
        cli[["id_client", "churn", "date_resiliation", "age", "csp"]],
        on="id_client", how="left")

    # dimensions temps + alertes
    cmd["annee_mois"] = cmd.dt_commande.dt.to_period("M").astype(str)
    cmd["trimestre"] = cmd.dt_commande.dt.to_period("Q").astype(str)
    cmd["annee"] = cmd.dt_commande.dt.year
    today = pd.Timestamp(cfg.business.date_reference)
    age = (today - cmd.dt_commande).dt.total_seconds() / 86400
    cmd["age_jours"] = age.round(1)
    cmd["alerte_sla"] = (cmd.statut_parcours == "En cours") & (age > sla)

    return cmd


def construire_et_ecrire(cfg: Config, tables=None) -> pd.DataFrame:
    cfg.paths.mart.mkdir(parents=True, exist_ok=True)
    faits = construire(cfg, tables)
    faits.to_csv(cfg.paths.mart / "faits_parcours.csv", index=False)
    log.info("Datamart : %d lignes, %d colonnes", len(faits), faits.shape[1])
    return faits
