"""Tests de la generation de donnees."""
import fibre360.config as C


def test_toutes_les_sources_presentes(tables):
    attendues = {"techniciens", "clients", "commandes", "evenements",
                 "interventions", "satisfaction", "reclamations", "factures"}
    assert attendues <= set(tables)


def test_volume_commandes(tables, cfg):
    assert len(tables["commandes"]) == cfg.n_commandes


def test_cles_uniques(tables):
    assert tables["commandes"]["id_commande"].is_unique
    assert tables["clients"]["id_client"].is_unique


def test_integrite_referentielle(tables):
    clients = set(tables["clients"]["id_client"])
    assert set(tables["commandes"]["id_client"]) <= clients
    commandes = set(tables["commandes"]["id_commande"])
    assert set(tables["evenements"]["id_commande"]) <= commandes


def test_domaines_valides(tables):
    assert set(tables["commandes"]["canal"]) <= set(C.CANAUX)
    assert set(tables["commandes"]["offre"]) <= set(C.OFFRES)


def test_reproductibilite(cfg):
    from fibre360.data_generation.generators import DataGenerator
    a = DataGenerator(cfg).generate()["commandes"]
    b = DataGenerator(cfg).generate()["commandes"]
    assert a.equals(b)
