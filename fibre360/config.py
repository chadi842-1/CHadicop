"""
fibre360.config
===============
Configuration centralisee de la plateforme : chemins, parametres metier,
referentiels, hyper-parametres. Chargeable depuis un YAML (config/config.yaml)
avec repli sur les valeurs par defaut ci-dessous.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field, asdict
from datetime import date
from pathlib import Path
from typing import Any

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover
    yaml = None

ROOT = Path(__file__).resolve().parents[1]


# --------------------------------------------------------------------------- #
# Chemins
# --------------------------------------------------------------------------- #
@dataclass
class Paths:
    root: Path = ROOT
    raw: Path = ROOT / "data" / "raw"
    mart: Path = ROOT / "data" / "mart"
    exports: Path = ROOT / "data" / "exports"
    models: Path = ROOT / "models"
    dashboard: Path = ROOT / "dashboard"
    docs: Path = ROOT / "docs"

    def ensure(self) -> None:
        for p in (self.raw, self.mart, self.exports, self.models,
                  self.dashboard, self.docs):
            p.mkdir(parents=True, exist_ok=True)


# --------------------------------------------------------------------------- #
# Parametres metier
# --------------------------------------------------------------------------- #
@dataclass
class Business:
    sla_jours: int = 15
    date_reference: date = date(2026, 11, 1)
    horizon_debut: date = date(2024, 11, 1)   # historique sur 2 ans
    seuil_risque_eleve: float = 0.66
    seuil_risque_moyen: float = 0.33


# --------------------------------------------------------------------------- #
# Referentiels
# --------------------------------------------------------------------------- #
CANAUX = ["Boutique", "Web", "Telephone", "Distributeur", "App mobile"]
CANAL_POIDS = [0.28, 0.27, 0.18, 0.14, 0.13]
CANAL_RISQUE = {"Boutique": 0.90, "Web": 1.12, "Telephone": 1.05,
                "Distributeur": 1.30, "App mobile": 1.00}
CANAL_NPS = {"Boutique": 42, "Web": 30, "Telephone": 25,
             "Distributeur": 18, "App mobile": 35}

OFFRES = {"Fibre 1 Gb/s": 39.99, "Fibre 2 Gb/s": 49.99,
          "Fibre 5 Gb/s": 59.99, "Fibre 8 Gb/s": 69.99}
OFFRE_POIDS = [0.44, 0.30, 0.16, 0.10]

SEGMENTS = {"Grand Public": 0.80, "Pro": 0.20}

REGIONS = {
    "Ile-de-France": ["75", "77", "78", "91", "92", "93", "94", "95"],
    "Auvergne-Rhone-Alpes": ["69", "38", "73", "74", "63"],
    "Occitanie": ["31", "34", "11", "66", "81"],
    "Hauts-de-France": ["59", "62", "80", "02"],
    "Nouvelle-Aquitaine": ["33", "64", "17", "87"],
    "Grand-Est": ["67", "68", "54", "51"],
    "PACA": ["13", "06", "83", "84"],
}
REGION_POIDS = [0.26, 0.17, 0.14, 0.12, 0.12, 0.10, 0.09]

SOUS_TRAITANTS = {"RacoNet": 0.80, "FibreExpress": 0.95,
                  "ConnectPlus": 1.10, "OptiReseau": 1.35, "TelcoBuild": 1.20}
ST_POIDS = [0.26, 0.26, 0.22, 0.14, 0.12]

GESTIONNAIRES = [f"PF-{n}" for n in
                 ("Nord", "Sud", "Est", "Ouest", "Centre",
                  "Grands-Comptes", "Pro-IDF")]

MOTIFS_ECHEC = ["Absence client au RDV", "Point de branchement sature",
                "Cablage immeuble non conforme", "Adresse non raccordable",
                "Materiel manquant", "Acces impossible", "Erreur de planification"]

MOTIFS_RECLAMATION = ["Delai trop long", "Rendez-vous manque", "Facturation",
                      "Qualite du raccordement", "Information manquante",
                      "Comportement technicien"]

ETAPES = ["Commande enregistree", "Etude eligibilite", "Prise de RDV",
          "Construction ligne", "Intervention technicien", "Mise en service"]

HAPPY_PATH = (
    "Commande enregistree -> Etude eligibilite -> Prise de RDV -> "
    "Intervention technicien -> Mise en service"
)


# --------------------------------------------------------------------------- #
# ML
# --------------------------------------------------------------------------- #
@dataclass
class MLParams:
    test_size: float = 0.2
    val_size: float = 0.2
    cv_folds: int = 5
    random_state: int = 42
    features_num: list[str] = field(default_factory=lambda: [
        "debit_gbps", "montant_mensuel", "anciennete_client_mois"])
    features_cat: list[str] = field(default_factory=lambda: [
        "canal", "offre", "segment", "region", "gestionnaire_portefeuille",
        "zone_a_construire", "sous_traitant"])


# --------------------------------------------------------------------------- #
# Config racine
# --------------------------------------------------------------------------- #
@dataclass
class Config:
    paths: Paths = field(default_factory=Paths)
    business: Business = field(default_factory=Business)
    ml: MLParams = field(default_factory=MLParams)
    n_commandes: int = 60_000
    seed: int = 42

    @classmethod
    def load(cls, path: str | Path | None = None) -> "Config":
        cfg = cls()
        p = Path(path) if path else (ROOT / "config" / "config.yaml")
        if yaml and p.exists():
            data = yaml.safe_load(p.read_text()) or {}
            cfg.n_commandes = data.get("n_commandes", cfg.n_commandes)
            cfg.seed = data.get("seed", cfg.seed)
            b = data.get("business", {})
            if "sla_jours" in b:
                cfg.business.sla_jours = b["sla_jours"]
        return cfg

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["paths"] = {k: str(v) for k, v in d["paths"].items()}
        for k in ("date_reference", "horizon_debut"):
            d["business"][k] = str(d["business"][k])
        return d


# --------------------------------------------------------------------------- #
def get_logger(name: str = "fibre360") -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        h = logging.StreamHandler()
        h.setFormatter(logging.Formatter(
            "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
            datefmt="%H:%M:%S"))
        logger.addHandler(h)
        logger.setLevel(logging.INFO)
    return logger
