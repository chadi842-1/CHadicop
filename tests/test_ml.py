"""Tests des modeles ML (scoring risque de livraison et churn)."""
from fibre360.ml import churn, train


def test_scoring_risque(faits, cfg):
    r = train.entrainer(cfg, faits)
    # un modele utile doit battre nettement le hasard
    assert r["auc"] > 0.70
    assert {"modele", "cv_auc_moyen"} <= set(r["comparaison"].columns)
    assert (cfg.paths.models / "modele_risque_livraison.joblib").exists()
    assert (cfg.paths.models / "model_card_risque.json").exists()


def test_scoring_en_cours_borne(faits, cfg):
    r = train.entrainer(cfg, faits)
    sc = r["scores_en_cours"]
    if not sc.empty:
        assert sc["score_risque"].between(0, 1).all()
        assert set(sc["niveau_risque"].dropna()) <= {"Faible", "Moyen", "Eleve"}


def test_importances_triees(faits, cfg):
    r = train.entrainer(cfg, faits)
    imp = r["importances"]
    assert imp["importance"].is_monotonic_decreasing


def test_churn(faits, cfg):
    c = churn.entrainer(cfg, faits)
    assert 0.0 <= c["auc"] <= 1.0
    assert not c["clients_a_risque"].empty
    assert (cfg.paths.models / "modele_churn.joblib").exists()
