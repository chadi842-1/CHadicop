"""
fibre360.pipeline.data_quality
==============================
Framework leger de QUALITE DE DONNEES. Chaque regle produit un resultat
(PASS / WARN / FAIL) avec un detail chiffre. Un rapport consolide est exporte
en CSV + Markdown. S'inspire des controles d'un outil type Great Expectations,
mais sans dependance lourde.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from fibre360.config import Config, get_logger

log = get_logger("fibre360.dq")


@dataclass
class Resultat:
    table: str
    regle: str
    statut: str   # PASS / WARN / FAIL
    valeur: float
    seuil: str
    detail: str


class ControleQualite:
    def __init__(self, cfg: Config):
        self.cfg = cfg
        self.resultats: list[Resultat] = []

    # -- primitives ----------------------------------------------------- #
    def _ajout(self, table, regle, ok, valeur, seuil, detail, warn=False):
        statut = "PASS" if ok else ("WARN" if warn else "FAIL")
        self.resultats.append(Resultat(table, regle, statut, round(float(valeur), 4),
                                        seuil, detail))

    def unicite(self, df, table, col):
        dup = int(df[col].duplicated().sum())
        self._ajout(table, f"unicite({col})", dup == 0, dup, "== 0",
                    f"{dup} doublons")

    def non_null(self, df, table, col, seuil=0.0):
        taux = df[col].isna().mean()
        self._ajout(table, f"non_null({col})", taux <= seuil, taux * 100,
                    f"<= {seuil*100:.0f}%", f"{taux*100:.2f}% de valeurs nulles")

    def plage(self, df, table, col, lo, hi):
        hors = int(((df[col] < lo) | (df[col] > hi)).sum())
        self._ajout(table, f"plage({col} in [{lo},{hi}])", hors == 0, hors,
                    "== 0", f"{hors} valeurs hors plage")

    def domaine(self, df, table, col, valeurs):
        hors = int((~df[col].isin(valeurs)).sum())
        self._ajout(table, f"domaine({col})", hors == 0, hors, "== 0",
                    f"{hors} valeurs hors referentiel")

    def integrite_ref(self, enfant, parent, table, col):
        orphelins = int((~enfant[col].isin(parent[col])).sum())
        self._ajout(table, f"integrite_ref({col})", orphelins == 0, orphelins,
                    "== 0", f"{orphelins} cles orphelines")

    def fraicheur(self, df, table, col, jours_max):
        last = pd.to_datetime(df[col]).max()
        age = (pd.Timestamp(self.cfg.business.date_reference) - last).days
        self._ajout(table, f"fraicheur({col})", age <= jours_max, age,
                    f"<= {jours_max} j", f"donnee la plus recente il y a {age} j",
                    warn=True)

    # -- batterie de controles ----------------------------------------- #
    def executer(self, tables: dict[str, pd.DataFrame]) -> pd.DataFrame:
        import fibre360.config as CFG
        cmd = tables["commandes"]
        cli = tables["clients"]
        ev = tables["evenements"]

        self.unicite(cmd, "commandes", "id_commande")
        self.unicite(cli, "clients", "id_client")
        self.non_null(cmd, "commandes", "canal")
        self.non_null(cmd, "commandes", "montant_mensuel")
        self.plage(cmd, "commandes", "montant_mensuel", 10, 200)
        self.plage(cmd, "commandes", "debit_gbps", 1, 8)
        self.plage(cli, "clients", "age", 18, 100)
        self.domaine(cmd, "commandes", "canal", CFG.CANAUX)
        self.domaine(cmd, "commandes", "offre", list(CFG.OFFRES))
        self.integrite_ref(cmd, cli, "commandes", "id_client")
        self.integrite_ref(ev, cmd, "evenements", "id_commande")
        self.fraicheur(cmd, "commandes", "date_commande", 30)

        df = pd.DataFrame([r.__dict__ for r in self.resultats])
        return df

    def rapport(self, tables) -> pd.DataFrame:
        df = self.executer(tables)
        self.cfg.paths.exports.mkdir(parents=True, exist_ok=True)
        df.to_csv(self.cfg.paths.exports / "data_quality_report.csv", index=False)

        n_fail = (df.statut == "FAIL").sum()
        n_warn = (df.statut == "WARN").sum()
        lignes = ["# Rapport de qualite des donnees\n",
                  f"- Controles : **{len(df)}**  |  PASS : "
                  f"**{(df.statut=='PASS').sum()}**  |  WARN : **{n_warn}**  |  "
                  f"FAIL : **{n_fail}**\n",
                  "\n| Table | Regle | Statut | Valeur | Seuil | Detail |",
                  "|-------|-------|:------:|-------:|-------|--------|"]
        for r in df.itertuples(index=False):
            lignes.append(f"| {r.table} | `{r.regle}` | {r.statut} | "
                          f"{r.valeur} | {r.seuil} | {r.detail} |")
        (self.cfg.paths.exports / "data_quality_report.md").write_text(
            "\n".join(lignes), encoding="utf-8")
        log.info("Qualite : %d controles (%d FAIL, %d WARN)", len(df), n_fail, n_warn)
        return df
