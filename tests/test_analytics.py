"""Tests des modules analytics."""
from fibre360.analytics import (anomaly, cohorts, forecasting, kpis,
                                process_mining, segmentation)


def test_kpis_canal(faits, cfg):
    k = kpis.kpi_par(faits, "canal")
    assert {"canal", "taux_livraison_delai_pct", "taux_churn_pct"} <= set(k.columns)
    assert (k["taux_livraison_delai_pct"].dropna().between(0, 100)).all()


def test_synthese_non_vide(faits, cfg):
    s = kpis.synthese(faits, cfg)
    assert len(s) > 5 and {"Indicateur", "Valeur"} <= set(s.columns)


def test_process_mining(cfg, tables):
    res = process_mining.analyser(cfg)
    assert not res["pm_variantes"].empty
    assert res["pm_goulots"]["duree_moyenne_j"].is_monotonic_decreasing


def test_forecast_horizon(faits, cfg):
    f = forecasting.prevoir(cfg, faits, horizon=3)
    assert (f.type == "prevision").sum() == 3


def test_anomaly_colonnes(faits, cfg):
    a = anomaly.detecter(cfg, faits)
    assert {"jour", "z_nb_commandes"} <= set(a.columns)


def test_segmentation(faits, cfg):
    s = segmentation.segmenter(cfg, faits, k=4)
    assert s["segmentation_profils"]["segment_kmeans"].nunique() == 4


def test_cohortes(faits, cfg):
    r = cohorts.retention(cfg, faits)
    assert "M+0" in r.columns
