"""
fibre360.ml.train
=================
Entrainement et comparaison de plusieurs modeles de classification pour le
scoring du risque de parcours degrade (non-livraison dans les delais).

- Modeles : Regression logistique, Random Forest, Gradient Boosting
- Selection par validation croisee (ROC-AUC)
- Evaluation sur jeu de test (AUC, PR-AUC, matrice de confusion)
- Persistance du meilleur modele (joblib) + carte de modele (model card)
"""
from __future__ import annotations

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.inspection import permutation_importance
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (average_precision_score, classification_report,
                             confusion_matrix, roc_auc_score)
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split
from sklearn.pipeline import Pipeline

from fibre360.config import Config, get_logger
from fibre360.ml.features import (dataset_risque_livraison, preprocesseur)

log = get_logger("fibre360.train")


def _modeles(cfg: Config) -> dict[str, object]:
    rs = cfg.ml.random_state
    return {
        "Regression logistique": LogisticRegression(
            max_iter=1000, class_weight="balanced", random_state=rs),
        "Random Forest": RandomForestClassifier(
            n_estimators=250, max_depth=12, class_weight="balanced",
            n_jobs=-1, random_state=rs),
        "Gradient Boosting": GradientBoostingClassifier(random_state=rs),
    }


def entrainer(cfg: Config, faits: pd.DataFrame) -> dict:
    termine, X, y, en_cours = dataset_risque_livraison(cfg, faits)
    X_tr, X_te, y_tr, y_te = train_test_split(
        X, y, test_size=cfg.ml.test_size, stratify=y,
        random_state=cfg.ml.random_state)

    pre = preprocesseur(cfg)
    cv = StratifiedKFold(n_splits=cfg.ml.cv_folds, shuffle=True,
                         random_state=cfg.ml.random_state)

    comparaison, pipelines = [], {}
    for nom, clf in _modeles(cfg).items():
        pipe = Pipeline([("pre", pre), ("clf", clf)])
        scores = cross_val_score(pipe, X_tr, y_tr, cv=cv, scoring="roc_auc", n_jobs=-1)
        comparaison.append({"modele": nom, "cv_auc_moyen": round(scores.mean(), 4),
                            "cv_auc_ecart_type": round(scores.std(), 4)})
        pipe.fit(X_tr, y_tr)
        pipelines[nom] = pipe
        log.info("  %-22s CV-AUC = %.4f (+/- %.4f)", nom, scores.mean(), scores.std())

    comp = pd.DataFrame(comparaison).sort_values("cv_auc_moyen", ascending=False)
    meilleur_nom = comp.iloc[0].modele
    best = pipelines[meilleur_nom]

    # Evaluation holdout
    proba = best.predict_proba(X_te)[:, 1]
    pred = (proba >= 0.5).astype(int)
    auc = roc_auc_score(y_te, proba)
    pr_auc = average_precision_score(y_te, proba)
    cm = confusion_matrix(y_te, pred)
    rapport = classification_report(y_te, pred, target_names=["OK", "A risque"],
                                    output_dict=True)

    # Explicabilite : importance par permutation
    perm = permutation_importance(best, X_te, y_te, n_repeats=8,
                                  random_state=cfg.ml.random_state, scoring="roc_auc")
    importances = (pd.DataFrame({
        "feature": X_te.columns,
        "importance": perm.importances_mean.round(4),
        "ecart_type": perm.importances_std.round(4)})
        .sort_values("importance", ascending=False).reset_index(drop=True))

    # Scoring des commandes en cours
    scores_en_cours = pd.DataFrame()
    if not en_cours.empty:
        p = best.predict_proba(en_cours[cfg.ml.features_num + cfg.ml.features_cat])[:, 1]
        scores_en_cours = en_cours[[
            "id_commande", "canal", "offre", "segment", "region",
            "gestionnaire_portefeuille", "sous_traitant", "zone_a_construire",
            "age_jours", "alerte_sla"]].copy()
        scores_en_cours["score_risque"] = p.round(3)
        scores_en_cours["niveau_risque"] = pd.cut(
            scores_en_cours.score_risque,
            bins=[-.01, cfg.business.seuil_risque_moyen,
                  cfg.business.seuil_risque_eleve, 1.01],
            labels=["Faible", "Moyen", "Eleve"])
        scores_en_cours = scores_en_cours.sort_values("score_risque", ascending=False)

    # Persistance
    cfg.paths.models.mkdir(parents=True, exist_ok=True)
    joblib.dump(best, cfg.paths.models / "modele_risque_livraison.joblib")
    model_card = {
        "nom": "Scoring risque de parcours Fibre degrade",
        "cible": "echec de raccordement OU livraison hors delai",
        "meilleur_modele": meilleur_nom,
        "base_apprentissage": int(len(termine)),
        "taux_risque_observe_pct": round(float(y.mean()) * 100, 1),
        "test_auc": round(float(auc), 4),
        "test_pr_auc": round(float(pr_auc), 4),
        "precision_classe_risque": round(rapport["A risque"]["precision"], 3),
        "rappel_classe_risque": round(rapport["A risque"]["recall"], 3),
        "features_num": cfg.ml.features_num,
        "features_cat": cfg.ml.features_cat,
        "comparaison_modeles": comparaison,
    }
    (cfg.paths.models / "model_card_risque.json").write_text(
        json.dumps(model_card, indent=2, ensure_ascii=False), encoding="utf-8")

    log.info("Meilleur modele : %s | test AUC = %.4f | PR-AUC = %.4f",
             meilleur_nom, auc, pr_auc)
    return {"comparaison": comp, "importances": importances,
            "scores_en_cours": scores_en_cours, "model_card": model_card,
            "confusion": cm, "auc": auc}
