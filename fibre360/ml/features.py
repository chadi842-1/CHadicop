"""
fibre360.ml.features
====================
Preparation des jeux d'apprentissage et pre-processeur commun aux modeles.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from fibre360.config import Config


def preprocesseur(cfg: Config) -> ColumnTransformer:
    return ColumnTransformer([
        ("num", StandardScaler(), cfg.ml.features_num),
        ("cat", OneHotEncoder(handle_unknown="ignore"), cfg.ml.features_cat),
    ])


def dataset_risque_livraison(cfg: Config, faits: pd.DataFrame):
    """Cible = parcours degrade (echec OU livraison hors delai)."""
    termine = faits[faits.statut_parcours.isin(
        ["Livree", "Echec raccordement"])].copy()
    termine["cible"] = np.where(
        (termine.statut_parcours == "Echec raccordement")
        | (termine.livree_dans_delai == 0), 1, 0)
    cols = cfg.ml.features_num + cfg.ml.features_cat
    en_cours = faits[faits.statut_parcours == "En cours"].copy()
    return termine, termine[cols], termine["cible"], en_cours


# Jeu de features dedie au churn : profil + EXPERIENCE de livraison vecue
CHURN_NUM = ["anciennete_client_mois", "age", "debit_gbps", "montant_mensuel",
             "delai_livraison_j", "nps", "nb_reclamations"]
CHURN_CAT = ["canal", "offre", "segment", "region"]


def dataset_churn(cfg: Config, faits: pd.DataFrame):
    """Cible = resiliation du client. 1 ligne par client, a partir de sa
    1ere commande livree (l'experience de livraison nourrit le modele)."""
    liv = faits[faits.statut_parcours == "Livree"].copy()
    base = liv.sort_values("dt_commande").groupby("id_client").first().reset_index()
    base = base.dropna(subset=["churn"])
    base["cible"] = base["churn"].astype(int)
    # imputation simple des experiences manquantes
    for c in CHURN_NUM:
        base[c] = base[c].fillna(base[c].median())
    return base, base[CHURN_NUM + CHURN_CAT], base["cible"]
