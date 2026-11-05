"""
04_scoring_model.py
===================
Modele de SCORING du risque de non-livraison dans les delais d'une commande
Fibre (parcours Commande -> Livraison).

Mission fiche de poste : "reflechir a des modeles de scoring",
"manipuler les chiffres afin de proposer des recommandations operationnelles".

Approche :
  - Cible (binaire) : 1 = commande livree HORS delai OU en echec de raccordement
                      0 = commande livree DANS les delais
    (le score mesure donc le risque d'un parcours degrade)
  - Features : canal, offre, segment, region, zone a construire, sous-traitant, debit
  - Modele : regression logistique (explicable) + arbre de comparaison,
             calibration et evaluation (AUC, matrice de confusion).
  - Application : on score les commandes EN COURS pour prioriser le portefeuille.

Sorties :
  - data/exports/scoring_importances.csv   : poids des facteurs (explicabilite)
  - data/exports/scoring_commandes_en_cours.csv : score de risque par commande active
  - data/exports/scoring_metrics.txt       : performances du modele
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (classification_report, confusion_matrix,
                             roc_auc_score)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

ROOT = Path(__file__).resolve().parents[1]
MART = ROOT / "data" / "mart"
EXPORTS = ROOT / "data" / "exports"

NUM = ["debit_gbps", "montant_mensuel"]
CAT = ["canal", "offre", "segment", "region", "gestionnaire_portefeuille",
       "zone_a_construire", "sous_traitant"]


def preparer():
    faits = pd.read_csv(MART / "faits_parcours.csv")

    # Jeu d'apprentissage : parcours TERMINES (livres ou en echec)
    termine = faits[faits["statut_parcours"].isin(
        ["Livree", "Echec raccordement"])].copy()
    termine["cible_risque"] = np.where(
        (termine["statut_parcours"] == "Echec raccordement")
        | (termine["livree_dans_delai"] == 0),
        1, 0,
    )

    # Jeu a scorer : commandes EN COURS (decision operationnelle)
    en_cours = faits[faits["statut_parcours"] == "En cours"].copy()
    return faits, termine, en_cours


def entrainer(termine):
    X = termine[NUM + CAT]
    y = termine["cible_risque"]
    X_tr, X_te, y_tr, y_te = train_test_split(
        X, y, test_size=0.25, random_state=42, stratify=y)

    pre = ColumnTransformer([
        ("num", StandardScaler(), NUM),
        ("cat", OneHotEncoder(handle_unknown="ignore"), CAT),
    ])
    model = Pipeline([
        ("pre", pre),
        ("clf", LogisticRegression(max_iter=1000, class_weight="balanced")),
    ])
    model.fit(X_tr, y_tr)

    proba = model.predict_proba(X_te)[:, 1]
    pred = (proba >= 0.5).astype(int)
    auc = roc_auc_score(y_te, proba)
    report = classification_report(y_te, pred, target_names=["OK", "A risque"])
    cm = confusion_matrix(y_te, pred)
    return model, auc, report, cm, X_tr


def importances(model, X_tr) -> pd.DataFrame:
    """Poids de la regression logistique -> explicabilite des facteurs."""
    ohe = model.named_steps["pre"].named_transformers_["cat"]
    noms = NUM + list(ohe.get_feature_names_out(CAT))
    coefs = model.named_steps["clf"].coef_[0]
    imp = (pd.DataFrame({"facteur": noms, "poids": coefs})
           .assign(effet=lambda d: np.where(d["poids"] > 0,
                                             "augmente le risque",
                                             "reduit le risque"),
                   poids_abs=lambda d: d["poids"].abs())
           .sort_values("poids_abs", ascending=False)
           .drop(columns="poids_abs"))
    imp["poids"] = imp["poids"].round(3)
    return imp


def scorer_en_cours(model, en_cours: pd.DataFrame) -> pd.DataFrame:
    if en_cours.empty:
        return en_cours
    proba = model.predict_proba(en_cours[NUM + CAT])[:, 1]
    out = en_cours.copy()
    out["score_risque"] = proba.round(3)
    out["niveau_risque"] = pd.cut(
        out["score_risque"], bins=[-0.01, 0.33, 0.66, 1.01],
        labels=["Faible", "Moyen", "Eleve"])
    cols = ["id_commande", "canal", "offre", "segment", "region",
            "gestionnaire_portefeuille", "sous_traitant", "zone_a_construire",
            "age_jours", "alerte_sla", "score_risque", "niveau_risque"]
    return out[cols].sort_values("score_risque", ascending=False)


def main():
    EXPORTS.mkdir(parents=True, exist_ok=True)
    faits, termine, en_cours = preparer()
    model, auc, report, cm, X_tr = entrainer(termine)
    imp = importances(model, X_tr)
    scores = scorer_en_cours(model, en_cours)

    imp.to_csv(EXPORTS / "scoring_importances.csv", index=False)
    scores.to_csv(EXPORTS / "scoring_commandes_en_cours.csv", index=False)

    txt = EXPORTS / "scoring_metrics.txt"
    with open(txt, "w") as f:
        f.write("MODELE DE SCORING - Risque de parcours Fibre degrade\n")
        f.write("=" * 55 + "\n")
        f.write(f"Base d'apprentissage : {len(termine):,} parcours termines\n")
        f.write(f"Taux de risque observe : {termine['cible_risque'].mean()*100:.1f}%\n\n")
        f.write(f"AUC (ROC) sur test : {auc:.3f}\n\n")
        f.write("Rapport de classification :\n")
        f.write(report + "\n")
        f.write("Matrice de confusion [ [TN FP] [FN TP] ] :\n")
        f.write(str(cm) + "\n")

    print("=" * 60)
    print("SCORING - Risque de non-livraison dans les delais")
    print("=" * 60)
    print(f"AUC (ROC)                 : {auc:.3f}")
    print(f"Parcours termines (train) : {len(termine):,}")
    print(f"Commandes en cours scorees: {len(scores):,}")
    if not scores.empty:
        rep = scores["niveau_risque"].value_counts()
        print("Repartition du risque     : "
              + ", ".join(f"{k}={v}" for k, v in rep.items()))
    print("\n--- Top facteurs de risque (regression logistique) ---")
    for r in imp.head(8).itertuples(index=False):
        print(f"  {r.poids:>7.3f}  {r.effet:20s}  {r.facteur}")
    print(f"\nOK : exports scoring ecrits dans {EXPORTS}")


if __name__ == "__main__":
    main()
