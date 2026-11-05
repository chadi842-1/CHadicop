"""
fibre360.reporting.excel_report
==============================
Assemble l'ensemble des resultats (KPI, process mining, scoring, churn,
cohortes, prevision, anomalies, segmentation, qualite) dans un classeur Excel
multi-onglets, et exporte chaque vue en CSV pour la BI.
"""
from __future__ import annotations

import pandas as pd
from openpyxl.styles import Font, PatternFill
from openpyxl.utils import get_column_letter

from fibre360.config import Config, get_logger

log = get_logger("fibre360.excel")

_ENTETE = Font(bold=True, color="FFFFFF")
_FILL = PatternFill("solid", fgColor="1F4E78")


def _styliser(ws):
    for cell in ws[1]:
        cell.font = _ENTETE
        cell.fill = _FILL
    for col in ws.columns:
        largeur = max((len(str(c.value)) for c in col if c.value is not None),
                      default=10)
        ws.column_dimensions[get_column_letter(col[0].column)].width = min(largeur + 2, 40)
    ws.freeze_panes = "A2"


def construire_classeur(cfg: Config, vues: dict[str, pd.DataFrame]) -> str:
    cfg.paths.exports.mkdir(parents=True, exist_ok=True)
    xlsx = cfg.paths.exports / "KPI_pilotage_fibre.xlsx"
    with pd.ExcelWriter(xlsx, engine="openpyxl") as writer:
        for nom, df in vues.items():
            feuille = nom[:31]
            df.to_excel(writer, sheet_name=feuille, index=False)
            _styliser(writer.sheets[feuille])
            df.to_csv(cfg.paths.exports / f"{nom.lower()}.csv", index=False)
    log.info("Classeur Excel : %d onglets -> %s", len(vues), xlsx)
    return str(xlsx)
