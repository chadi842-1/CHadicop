"""Fixtures partagees : un petit jeu de donnees genere une seule fois."""
import pytest

from fibre360.config import Config
from fibre360.data_generation.generators import DataGenerator
from fibre360.pipeline.datamart import construire


@pytest.fixture(scope="session")
def cfg(tmp_path_factory):
    c = Config()
    base = tmp_path_factory.mktemp("fibre360_data")
    c.paths.raw = base / "raw"
    c.paths.mart = base / "mart"
    c.paths.exports = base / "exports"
    c.paths.models = base / "models"
    c.paths.dashboard = base / "dashboard"
    c.paths.docs = base / "docs"
    c.paths.ensure()
    c.n_commandes = 3000
    return c


@pytest.fixture(scope="session")
def tables(cfg):
    t = DataGenerator(cfg).generate()
    for name, df in t.items():
        df.to_csv(cfg.paths.raw / f"{name}.csv", index=False)
    return t


@pytest.fixture(scope="session")
def faits(cfg, tables):
    f = construire(cfg, tables)
    f.to_csv(cfg.paths.mart / "faits_parcours.csv", index=False)
    return f
