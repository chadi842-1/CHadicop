"""Test de l'export du modele en etoile Power BI."""
import pandas as pd

from fibre360.reporting.powerbi_export import exporter


def test_export_star_schema(cfg, faits, monkeypatch, tmp_path):
    # rediriger la racine vers un repertoire temporaire
    monkeypatch.setattr(cfg.paths, "root", tmp_path)
    out = exporter(cfg, faits)

    fact = pd.read_csv(out / "fact_parcours.csv")
    assert len(fact) == len(faits)
    for col in ("IdCommande", "DateCommande", "Canal", "EstLivree", "AlerteSLA"):
        assert col in fact.columns
    # indicateurs binaires bien 0/1
    assert set(fact["EstLivree"].unique()) <= {0, 1}

    # les dimensions existent et ne sont pas vides
    for dim in ("dim_date", "dim_canal", "dim_sous_traitant"):
        d = pd.read_csv(out / f"{dim}.csv")
        assert not d.empty

    # cohérence référentielle : chaque canal du fait est dans la dimension
    dim_canal = pd.read_csv(out / "dim_canal.csv")
    assert set(fact["Canal"].unique()) <= set(dim_canal["Canal"])
