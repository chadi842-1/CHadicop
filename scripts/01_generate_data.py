"""
01_generate_data.py
====================
Genere un jeu de donnees SYNTHETIQUE et REALISTE du parcours
Commande -> Livraison des offres Fibre (contexte type operateur telecom).

Les donnees reelles etant confidentielles, ce generateur produit des donnees
fictives mais structurees comme un SI operationnel : plusieurs sources a croiser
(mission "croiser plusieurs sources de donnees" de la fiche de poste).

Sorties (data/raw/) :
  - commandes.csv        : referentiel des commandes Fibre (CRM / ventes)
  - evenements.csv       : journal d'evenements du parcours (process mining)
  - interventions.csv    : interventions techniques de raccordement
  - satisfaction.csv     : enquetes de satisfaction post-livraison

Usage :  python scripts/01_generate_data.py [--n 12000] [--seed 42]
"""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

RAW = Path(__file__).resolve().parents[1] / "data" / "raw"

# --------------------------------------------------------------------------- #
# Referentiels metier
# --------------------------------------------------------------------------- #
CANAUX = ["Boutique", "Web", "Telephone", "Distributeur"]
# Poids de volume et "profil de risque" par canal (multi-canalite)
CANAL_POIDS = [0.34, 0.30, 0.21, 0.15]
CANAL_RISQUE = {"Boutique": 0.90, "Web": 1.15, "Telephone": 1.05, "Distributeur": 1.30}
CANAL_NPS = {"Boutique": 42, "Web": 30, "Telephone": 25, "Distributeur": 18}

OFFRES = {
    "Fibre 1 Gb/s": 39.99,
    "Fibre 2 Gb/s": 49.99,
    "Fibre 5 Gb/s": 59.99,
    "Fibre 8 Gb/s": 69.99,
}
OFFRE_POIDS = [0.46, 0.30, 0.15, 0.09]

SEGMENTS = {"Grand Public": 0.82, "Pro": 0.18}

REGIONS = {
    "Ile-de-France": ["75", "77", "78", "91", "92", "93", "94", "95"],
    "Auvergne-Rhone-Alpes": ["69", "38", "73", "74"],
    "Occitanie": ["31", "34", "11", "66"],
    "Hauts-de-France": ["59", "62", "80"],
    "Nouvelle-Aquitaine": ["33", "64", "17"],
}
REGION_POIDS = [0.32, 0.22, 0.17, 0.15, 0.14]

# Sous-traitants de raccordement : levier majeur de la performance de livraison
SOUS_TRAITANTS = {
    "RacoNet": 0.80,       # tres performant
    "FibreExpress": 0.95,
    "ConnectPlus": 1.10,
    "OptiReseau": 1.35,    # sous-performant
}
ST_POIDS = [0.30, 0.30, 0.25, 0.15]

GESTIONNAIRES = [f"PF-{n}" for n in (
    "Nord", "Sud", "Est", "Ouest", "Centre", "Grands-Comptes")]

MOTIFS_ECHEC = [
    "Absence client au RDV",
    "Point de branchement sature",
    "Cablage immeuble non conforme",
    "Adresse non raccordable",
    "Materiel manquant",
    "Acces impossible",
]

# Etapes du parcours (activites pour le process mining)
ETAPES = [
    "Commande enregistree",
    "Etude eligibilite",
    "Prise de RDV",
    "Construction ligne",     # uniquement si zone a construire
    "Intervention technicien",
    "Mise en service",
]

SLA_JOURS = 15  # delai cible commande -> mise en service (jours ouvres approx.)


# --------------------------------------------------------------------------- #
def _choice(rng, options, weights, size):
    return rng.choice(options, size=size, p=np.array(weights) / np.sum(weights))


def generate(n: int, seed: int) -> dict[str, pd.DataFrame]:
    rng = np.random.default_rng(seed)
    start = datetime(2025, 11, 1)
    horizon = datetime(2026, 11, 1)  # aujourd'hui dans le projet
    total_days = (horizon - start).days

    # ---- 1) Table COMMANDES ---------------------------------------------- #
    ids = [f"CMD{100000 + i}" for i in range(n)]
    canal = _choice(rng, CANAUX, CANAL_POIDS, n)
    offre = _choice(rng, list(OFFRES), OFFRE_POIDS, n)
    segment = _choice(rng, list(SEGMENTS), list(SEGMENTS.values()), n)
    region = _choice(rng, list(REGIONS), REGION_POIDS, n)
    departement = [rng.choice(REGIONS[r]) for r in region]
    gestionnaire = rng.choice(GESTIONNAIRES, size=n)
    zone_a_construire = rng.random(n) < 0.28  # 28% des commandes en zone a construire
    sous_traitant = _choice(rng, list(SOUS_TRAITANTS), ST_POIDS, n)

    # Date de commande : plus de volume sur les mois recents (croissance)
    u = rng.random(n) ** 0.75
    date_commande = [start + timedelta(days=int(x * total_days)) for x in u]

    commandes = pd.DataFrame({
        "id_commande": ids,
        "id_client": [f"CLI{200000 + int(rng.integers(0, n))}" for _ in range(n)],
        "date_commande": date_commande,
        "canal": canal,
        "offre": offre,
        "debit_gbps": [int(o.split()[1]) for o in offre],
        "montant_mensuel": [OFFRES[o] for o in offre],
        "segment": segment,
        "region": region,
        "departement": departement,
        "gestionnaire_portefeuille": gestionnaire,
        "zone_a_construire": zone_a_construire,
        "sous_traitant": sous_traitant,
    })

    # ---- 2) Simulation du parcours -> delais, echecs, evenements --------- #
    evenements, interventions, satisfaction = [], [], []

    for row in commandes.itertuples(index=False):
        t0 = row.date_commande

        # Delai de base (jours) tire d'une loi gamma, module par les facteurs
        base = rng.gamma(shape=6.0, scale=1.6)  # ~ 9-10 j en moyenne
        facteur = (
            CANAL_RISQUE[row.canal]
            * SOUS_TRAITANTS[row.sous_traitant]
            * (1.45 if row.zone_a_construire else 1.0)
            * (1.12 if row.segment == "Pro" else 1.0)
        )
        delai_total = base * facteur

        # Probabilite d'echec de raccordement (fonction des memes leviers)
        p_echec = np.clip(
            0.04
            * SOUS_TRAITANTS[row.sous_traitant]
            * CANAL_RISQUE[row.canal]
            * (1.8 if row.zone_a_construire else 1.0),
            0.01, 0.45,
        )
        echec = rng.random() < p_echec
        # Annulation client (avant livraison)
        annulee = (not echec) and (rng.random() < 0.05 * CANAL_RISQUE[row.canal])

        # Commandes encore EN COURS : les plus recentes sans assez de recul
        age_jours = (horizon - t0).days
        en_cours = age_jours < delai_total and not echec and not annulee

        # Jalons temporels
        def at(offset_days):
            return t0 + timedelta(days=float(max(0.0, offset_days)))

        d1 = 0
        d2 = d1 + rng.uniform(0.5, 2.5)                      # etude eligibilite
        d3 = d2 + rng.uniform(1.0, 4.0)                      # prise de RDV
        if row.zone_a_construire:
            d_constr = d3 + rng.uniform(5.0, 20.0)           # construction ligne
        else:
            d_constr = None
        d_interv = (d_constr if d_constr is not None else d3) + rng.uniform(1.0, 5.0)
        # recalage pour que la mise en service corresponde au delai total simule
        d_mes = max(d_interv + rng.uniform(0.0, 1.0), delai_total)

        acteur = {"Boutique": "Conseiller boutique", "Web": "Selfcare",
                  "Telephone": "Televente", "Distributeur": "Partenaire"}[row.canal]

        evenements.append((row.id_commande, "Commande enregistree", at(d1), "OK", acteur))
        evenements.append((row.id_commande, "Etude eligibilite", at(d2), "OK", "SI Eligibilite"))

        if annulee:
            evenements.append((row.id_commande, "Annulation client",
                               at(d2 + rng.uniform(0, 3)), "ANNULEE", acteur))
        else:
            evenements.append((row.id_commande, "Prise de RDV", at(d3), "OK", "Planification"))
            if row.zone_a_construire:
                evenements.append((row.id_commande, "Construction ligne",
                                   at(d_constr), "OK", row.sous_traitant))

            if not en_cours:
                # Intervention technique -> enregistrement dans la table interventions
                resultat = "Echec" if echec else "OK"
                date_prevue = at(d_interv - rng.uniform(0, 1))
                date_realisee = at(d_interv)
                motif = rng.choice(MOTIFS_ECHEC) if echec else None
                interventions.append((
                    row.id_commande, f"INT{len(interventions)+500000}",
                    date_prevue, date_realisee, row.sous_traitant, resultat, motif,
                ))
                evenements.append((row.id_commande, "Intervention technicien",
                                   at(d_interv), resultat, row.sous_traitant))
                if echec:
                    evenements.append((row.id_commande, "Echec raccordement",
                                       at(d_interv + 0.1), "ECHEC", row.sous_traitant))
                else:
                    evenements.append((row.id_commande, "Mise en service",
                                       at(d_mes), "OK", "SI Activation"))
            else:
                # commande en cours : on s'arrete au dernier jalon atteint a date
                pass

        # Satisfaction : seulement pour les commandes livrees (mise en service)
        if (not echec) and (not annulee) and (not en_cours):
            base_nps = CANAL_NPS[row.canal]
            penalite = -25 if delai_total > SLA_JOURS else 8
            nps = int(np.clip(rng.normal(base_nps + penalite, 18), -100, 100))
            reclamation = (delai_total > SLA_JOURS) and (rng.random() < 0.55)
            satisfaction.append((
                row.id_commande, at(d_mes + rng.uniform(1, 7)),
                nps, rng.choice(["Email", "SMS", "Appel"]), bool(reclamation),
            ))

    ev = pd.DataFrame(evenements, columns=[
        "id_commande", "etape", "horodatage", "statut", "acteur"])
    it = pd.DataFrame(interventions, columns=[
        "id_commande", "id_intervention", "date_prevue", "date_realisee",
        "sous_traitant", "resultat", "motif_echec"])
    sa = pd.DataFrame(satisfaction, columns=[
        "id_commande", "date_enquete", "nps", "canal_contact", "reclamation"])

    return {"commandes": commandes, "evenements": ev,
            "interventions": it, "satisfaction": sa}


def main():
    ap = argparse.ArgumentParser(description="Generation des donnees Fibre C/L")
    ap.add_argument("--n", type=int, default=12000, help="nombre de commandes")
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    RAW.mkdir(parents=True, exist_ok=True)
    tables = generate(args.n, args.seed)
    for name, df in tables.items():
        path = RAW / f"{name}.csv"
        df.to_csv(path, index=False)
        print(f"  {name:14s} -> {len(df):>7,} lignes  ({path})")
    print(f"\nOK : {args.n:,} commandes generees dans {RAW}")


if __name__ == "__main__":
    main()
