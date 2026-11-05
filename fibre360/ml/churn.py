"""
fibre360.ml.churn
================
Modele de prediction du CHURN (resiliation client) a partir du profil et de
l'experience de livraison. Fournit AUC, importances et liste des clients a
risque de depart (priorisation relationnelle / retention).
"""
from __future__ import annotations

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from fibre360.config import Config, get_logger
from fibre360.ml.features import CHURN_CAT, CHURN_NUM, dataset_churn

log = get_logger("fibre360.churn")


def entrainer(cfg: Config, faits: pd.DataFrame) -> dict:
    base, X, y = dataset_churn(cfg, faits)
    X_tr, X_te, y_tr, y_te = train_test_split(
        X, y, test_size=cfg.ml.test_size, stratify=y,
        random_state=cfg.ml.random_state)
    pre = ColumnTransformer([
        ("num", StandardScaler(), CHURN_NUM),
        ("cat", OneHotEncoder(handle_unknown="ignore"), CHURN_CAT)])
    pipe = Pipeline([("pre", pre),
                     ("clf", GradientBoostingClassifier(
                         random_state=cfg.ml.random_state))])
    pipe.fit(X_tr, y_tr)
    proba = pipe.predict_proba(X_te)[:, 1]
    auc = roc_auc_score(y_te, proba)

    base = base.copy()
    base["score_churn"] = pipe.predict_proba(X)[:, 1].round(3)
    top = (base[base.churn == False]  # clients encore actifs
           .sort_values("score_churn", ascending=False)
           [["id_client", "canal", "offre", "segment", "region",
             "anciennete_client_mois", "nps", "nb_reclamations", "score_churn"]]
           .head(500))

    cfg.paths.models.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipe, cfg.paths.models / "modele_churn.joblib")
    log.info("Churn : AUC test = %.4f | %d clients a risque identifies", auc, len(top))
    return {"auc": round(float(auc), 4),
            "taux_churn_pct": round(float(y.mean()) * 100, 1),
            "clients_a_risque": top}
