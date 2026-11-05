"""Tests du datamart et du framework de qualite."""
import pandas as pd

from fibre360.pipeline.data_quality import ControleQualite


def test_datamart_colonnes_cles(faits):
    for col in ("id_commande", "statut_parcours", "delai_livraison_j",
                "livree_dans_delai", "churn", "alerte_sla"):
        assert col in faits.columns


def test_statuts_coherents(faits):
    assert set(faits["statut_parcours"]) <= {
        "Livree", "Echec raccordement", "Annulee", "En cours"}


def test_pas_de_delai_negatif(faits):
    liv = faits[faits.statut_parcours == "Livree"]
    assert (liv["delai_livraison_j"] >= 0).all()


def test_livree_dans_delai_binaire(faits):
    liv = faits[faits.statut_parcours == "Livree"]
    assert set(liv["livree_dans_delai"].dropna().unique()) <= {0, 1}


def test_qualite_aucun_echec(cfg, tables):
    df = ControleQualite(cfg).executer(tables)
    assert (df.statut != "FAIL").all(), df[df.statut == "FAIL"].to_dict("records")
