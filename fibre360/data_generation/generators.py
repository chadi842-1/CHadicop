"""
fibre360.data_generation.generators
====================================
Generateur de donnees SYNTHETIQUES relationnelles du parcours
Commande -> Livraison Fibre, sur 2 ans d'historique. Produit 8 sources
coherentes a croiser (contexte operateur telecom, donnees 100% fictives).

Sources :
  clients, commandes, evenements, interventions, satisfaction,
  reclamations, factures, techniciens
"""
from __future__ import annotations

from datetime import timedelta
from pathlib import Path

import numpy as np
import pandas as pd

from fibre360 import config as C
from fibre360.config import Config, get_logger

log = get_logger("fibre360.datagen")


def _choice(rng, options, weights, size):
    return rng.choice(options, size=size, p=np.array(weights) / np.sum(weights))


class DataGenerator:
    def __init__(self, cfg: Config):
        self.cfg = cfg
        self.rng = np.random.default_rng(cfg.seed)
        self.start = pd.Timestamp(cfg.business.horizon_debut)
        self.end = pd.Timestamp(cfg.business.date_reference)
        self.total_days = (self.end - self.start).days

    # ------------------------------------------------------------------ #
    def generate(self) -> dict[str, pd.DataFrame]:
        log.info("Generation de %d commandes sur %d jours d'historique",
                 self.cfg.n_commandes, self.total_days)
        techniciens = self._techniciens()
        clients = self._clients()
        commandes = self._commandes(clients, techniciens)
        parcours = self._parcours(commandes)
        clients = self._appliquer_churn(clients, commandes, parcours)
        return {
            "techniciens": techniciens,
            "clients": clients,
            "commandes": commandes,
            "evenements": parcours["evenements"],
            "interventions": parcours["interventions"],
            "satisfaction": parcours["satisfaction"],
            "reclamations": parcours["reclamations"],
            "factures": parcours["factures"],
        }

    # ------------------------------------------------------------------ #
    def _techniciens(self) -> pd.DataFrame:
        rng = self.rng
        n = 120
        st = _choice(rng, list(C.SOUS_TRAITANTS), C.ST_POIDS, n)
        region = _choice(rng, list(C.REGIONS), C.REGION_POIDS, n)
        anciennete = rng.integers(1, 180, n)  # mois
        # taux de reussite correle au sous-traitant et a l'anciennete
        base = np.array([1.0 / C.SOUS_TRAITANTS[s] for s in st])
        taux = np.clip(0.80 + 0.12 * (base - 1) + anciennete / 3000
                       + rng.normal(0, 0.03, n), 0.60, 0.99)
        return pd.DataFrame({
            "id_technicien": [f"TEC{i:04d}" for i in range(n)],
            "sous_traitant": st,
            "region": region,
            "anciennete_mois": anciennete,
            "taux_reussite_ref": taux.round(3),
        })

    # ------------------------------------------------------------------ #
    def _clients(self) -> pd.DataFrame:
        rng = self.rng
        n = int(self.cfg.n_commandes * 0.85)  # certains clients recommandent
        segment = _choice(rng, list(C.SEGMENTS), list(C.SEGMENTS.values()), n)
        region = _choice(rng, list(C.REGIONS), C.REGION_POIDS, n)
        departement = np.array([rng.choice(C.REGIONS[r]) for r in region])
        age = np.clip(rng.normal(46, 15, n), 18, 92).astype(int)
        csp = _choice(rng, ["Employe", "Cadre", "Ouvrier", "Retraite",
                            "Independant", "Etudiant"],
                      [0.28, 0.22, 0.15, 0.18, 0.10, 0.07], n)
        anciennete = rng.integers(0, 240, n)  # mois chez l'operateur
        return pd.DataFrame({
            "id_client": [f"CLI{200000 + i}" for i in range(n)],
            "age": age,
            "csp": csp,
            "segment": segment,
            "region": region,
            "departement": departement,
            "anciennete_client_mois": anciennete,
        })

    # ------------------------------------------------------------------ #
    def _commandes(self, clients, techniciens) -> pd.DataFrame:
        rng = self.rng
        n = self.cfg.n_commandes

        idx = rng.integers(0, len(clients), n)
        cl = clients.iloc[idx].reset_index(drop=True)

        canal = _choice(rng, C.CANAUX, C.CANAL_POIDS, n)
        offre = _choice(rng, list(C.OFFRES), C.OFFRE_POIDS, n)
        gestionnaire = rng.choice(C.GESTIONNAIRES, size=n)
        zone = rng.random(n) < 0.28
        st = _choice(rng, list(C.SOUS_TRAITANTS), C.ST_POIDS, n)

        # affectation d'un technicien du bon sous-traitant
        tech_par_st = {s: techniciens[techniciens.sous_traitant == s]
                       ["id_technicien"].values for s in C.SOUS_TRAITANTS}
        id_tech = [rng.choice(tech_par_st[s]) for s in st]

        # montee en charge progressive (plus de volume sur les mois recents)
        u = rng.random(n)
        days = (u ** 0.80) * self.total_days
        date_commande = [self.start + timedelta(days=float(d)) for d in days]

        return pd.DataFrame({
            "id_commande": [f"CMD{1_000_000 + i}" for i in range(n)],
            "id_client": cl["id_client"].values,
            "date_commande": pd.to_datetime(date_commande).normalize(),
            "canal": canal,
            "offre": offre,
            "debit_gbps": [int(o.split()[1]) for o in offre],
            "montant_mensuel": [C.OFFRES[o] for o in offre],
            "segment": cl["segment"].values,
            "region": cl["region"].values,
            "departement": cl["departement"].values,
            "anciennete_client_mois": cl["anciennete_client_mois"].values,
            "gestionnaire_portefeuille": gestionnaire,
            "zone_a_construire": zone,
            "sous_traitant": st,
            "id_technicien": id_tech,
        })

    # ------------------------------------------------------------------ #
    def _parcours(self, commandes) -> dict[str, pd.DataFrame]:
        rng = self.rng
        sla = self.cfg.business.sla_jours
        ev, it, sa, rc, fa = [], [], [], [], []
        acteurs = {"Boutique": "Conseiller boutique", "Web": "Selfcare",
                   "Telephone": "Televente", "Distributeur": "Partenaire",
                   "App mobile": "Selfcare"}

        for row in commandes.itertuples(index=False):
            t0 = row.date_commande
            base = rng.gamma(6.0, 1.6)
            facteur = (C.CANAL_RISQUE[row.canal]
                       * C.SOUS_TRAITANTS[row.sous_traitant]
                       * (1.45 if row.zone_a_construire else 1.0)
                       * (1.12 if row.segment == "Pro" else 1.0))
            delai_total = base * facteur

            p_echec = float(np.clip(
                0.04 * C.SOUS_TRAITANTS[row.sous_traitant]
                * C.CANAL_RISQUE[row.canal]
                * (1.8 if row.zone_a_construire else 1.0), 0.01, 0.45))
            echec = rng.random() < p_echec
            annulee = (not echec) and (rng.random() < 0.05 * C.CANAL_RISQUE[row.canal])

            age_jours = (self.end - t0).days
            en_cours = age_jours < delai_total and not echec and not annulee

            def at(d):
                return t0 + timedelta(days=float(max(0.0, d)))

            d2 = rng.uniform(0.5, 2.5)
            d3 = d2 + rng.uniform(1.0, 4.0)
            d_constr = d3 + rng.uniform(5.0, 20.0) if row.zone_a_construire else None
            d_interv = (d_constr if d_constr is not None else d3) + rng.uniform(1.0, 5.0)
            d_mes = max(d_interv + rng.uniform(0.0, 1.0), delai_total)
            acteur = acteurs[row.canal]

            ev.append((row.id_commande, "Commande enregistree", at(0), "OK", acteur))
            ev.append((row.id_commande, "Etude eligibilite", at(d2), "OK", "SI Eligibilite"))

            if annulee:
                ev.append((row.id_commande, "Annulation client",
                           at(d2 + rng.uniform(0, 3)), "ANNULEE", acteur))
            else:
                ev.append((row.id_commande, "Prise de RDV", at(d3), "OK", "Planification"))
                if row.zone_a_construire:
                    ev.append((row.id_commande, "Construction ligne",
                               at(d_constr), "OK", row.sous_traitant))
                if not en_cours:
                    resultat = "Echec" if echec else "OK"
                    motif = rng.choice(C.MOTIFS_ECHEC) if echec else None
                    it.append((row.id_commande, f"INT{len(it)+500000}",
                               at(d_interv - rng.uniform(0, 1)), at(d_interv),
                               row.sous_traitant, row.id_technicien, resultat, motif))
                    ev.append((row.id_commande, "Intervention technicien",
                               at(d_interv), resultat, row.id_technicien))
                    if echec:
                        ev.append((row.id_commande, "Echec raccordement",
                                   at(d_interv + 0.1), "ECHEC", row.sous_traitant))
                    else:
                        ev.append((row.id_commande, "Mise en service",
                                   at(d_mes), "OK", "SI Activation"))

            # Satisfaction (livrees)
            if (not echec) and (not annulee) and (not en_cours):
                base_nps = C.CANAL_NPS[row.canal]
                penalite = -25 if delai_total > sla else 8
                nps = int(np.clip(rng.normal(base_nps + penalite, 18), -100, 100))
                sa.append((row.id_commande, at(d_mes + rng.uniform(1, 7)), nps,
                           rng.choice(["Email", "SMS", "Appel"])))

                # Reclamations (plus probables si delai long)
                p_rec = 0.10 + (0.35 if delai_total > sla else 0.0)
                if rng.random() < p_rec:
                    resolu = rng.random() < 0.82
                    rc.append((row.id_commande, f"REC{len(rc)+700000}",
                               at(d_mes + rng.uniform(1, 30)),
                               rng.choice(C.MOTIFS_RECLAMATION),
                               rng.choice(["Email", "Appel", "Boutique", "App mobile"]),
                               resolu,
                               int(rng.integers(1, 15)) if resolu else None))

                # Factures (3 mois d'abonnement apres mise en service)
                for m in range(3):
                    fa.append((row.id_commande, row.id_client,
                               (at(d_mes) + pd.DateOffset(months=m)).date(),
                               round(row.montant_mensuel, 2)))

        evdf = pd.DataFrame(ev, columns=["id_commande", "etape", "horodatage",
                                         "statut", "acteur"])
        itdf = pd.DataFrame(it, columns=["id_commande", "id_intervention",
                                         "date_prevue", "date_realisee",
                                         "sous_traitant", "id_technicien",
                                         "resultat", "motif_echec"])
        sadf = pd.DataFrame(sa, columns=["id_commande", "date_enquete", "nps",
                                         "canal_contact"])
        rcdf = pd.DataFrame(rc, columns=["id_commande", "id_reclamation",
                                         "date_reclamation", "motif", "canal",
                                         "resolu", "delai_resolution_j"])
        fadf = pd.DataFrame(fa, columns=["id_commande", "id_client",
                                         "mois_facture", "montant"])
        return {"evenements": evdf, "interventions": itdf, "satisfaction": sadf,
                "reclamations": rcdf, "factures": fadf}

    # ------------------------------------------------------------------ #
    def _appliquer_churn(self, clients, commandes, parcours) -> pd.DataFrame:
        """Resiliation (churn) correlee a l'experience : delais, reclamations."""
        rng = self.rng
        sla = self.cfg.business.sla_jours
        ev = parcours["evenements"]
        rec = parcours["reclamations"]

        # delai de livraison par commande
        mes = ev[ev.etape == "Mise en service"].set_index("id_commande")["horodatage"]
        cmd0 = ev[ev.etape == "Commande enregistree"].set_index("id_commande")["horodatage"]
        delai = ((mes - cmd0).dt.total_seconds() / 86400)
        livre_long = delai[delai > sla].index
        clients_long = set(commandes[commandes.id_commande.isin(livre_long)]["id_client"])
        clients_rec = set(commandes[commandes.id_commande.isin(rec["id_commande"])]
                          ["id_client"])

        p = np.full(len(clients), 0.06)
        p += clients["id_client"].isin(clients_long).values * 0.10
        p += clients["id_client"].isin(clients_rec).values * 0.12
        p += (clients["anciennete_client_mois"].values < 12) * 0.05
        churn = rng.random(len(clients)) < np.clip(p, 0, 0.6)

        out = clients.copy()
        out["churn"] = churn
        out["date_resiliation"] = pd.NaT
        d = self.end
        out.loc[churn, "date_resiliation"] = [
            d - timedelta(days=int(rng.integers(1, 365))) for _ in range(churn.sum())]
        return out


def generer_et_ecrire(cfg: Config) -> dict[str, pd.DataFrame]:
    cfg.paths.ensure()
    tables = DataGenerator(cfg).generate()
    for name, df in tables.items():
        path = cfg.paths.raw / f"{name}.csv"
        df.to_csv(path, index=False)
        log.info("  %-14s -> %8d lignes", name, len(df))
    return tables
