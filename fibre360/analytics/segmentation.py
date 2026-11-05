"""
fibre360.analytics.segmentation
==============================
Segmentation des clients par K-Means sur des variables comportementales
(valeur, anciennete, qualite d'experience, reclamations). Fournit une
lecture "portefeuille" et une priorisation relationnelle.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

from fibre360.config import Config, get_logger

log = get_logger("fibre360.segmentation")


def _features_client(faits: pd.DataFrame) -> pd.DataFrame:
    liv = faits[faits.statut_parcours == "Livree"].copy()
    g = liv.groupby("id_client")
    df = pd.DataFrame({
        "nb_commandes": g.size(),
        "ca_mensuel": g.montant_mensuel.sum(),
        "delai_moyen": g.delai_livraison_j.mean(),
        "nps_moyen": g.nps.mean(),
        "nb_reclamations": g.nb_reclamations.sum(),
        "anciennete": g.anciennete_client_mois.max(),
        "churn": g.churn.max().astype(int),
    }).dropna()
    return df


def segmenter(cfg: Config, faits: pd.DataFrame, k: int = 4) -> dict[str, pd.DataFrame]:
    df = _features_client(faits)
    cols = ["ca_mensuel", "delai_moyen", "nps_moyen", "nb_reclamations", "anciennete"]
    X = StandardScaler().fit_transform(df[cols])
    km = KMeans(n_clusters=k, n_init=10, random_state=cfg.ml.random_state)
    df["segment_kmeans"] = km.fit_predict(X)

    profil = (df.groupby("segment_kmeans")
              .agg(nb_clients=("churn", "size"),
                   ca_mensuel_moyen=("ca_mensuel", "mean"),
                   delai_moyen=("delai_moyen", "mean"),
                   nps_moyen=("nps_moyen", "mean"),
                   reclamations_moy=("nb_reclamations", "mean"),
                   anciennete_moy=("anciennete", "mean"),
                   taux_churn_pct=("churn", lambda s: s.mean() * 100))
              .round(1).reset_index())

    # libelle metier des segments selon CA et churn
    def libelle(r):
        if r.ca_mensuel_moyen >= profil.ca_mensuel_moyen.median() and r.taux_churn_pct < profil.taux_churn_pct.median():
            return "Premium fideles"
        if r.taux_churn_pct >= profil.taux_churn_pct.median() and r.nps_moyen < profil.nps_moyen.median():
            return "A risque / insatisfaits"
        if r.ca_mensuel_moyen >= profil.ca_mensuel_moyen.median():
            return "Valeur a securiser"
        return "Standard"
    profil["libelle"] = profil.apply(libelle, axis=1)
    log.info("Segmentation : %d clients en %d segments", len(df), k)
    return {"segmentation_profils": profil,
            "segmentation_clients": df.reset_index()}
