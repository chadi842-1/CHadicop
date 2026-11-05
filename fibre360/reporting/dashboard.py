"""
fibre360.reporting.dashboard
============================
Genere un tableau de bord HTML autonome et interactif (Chart.js) a partir des
resultats du pipeline. Palette accessible (validee data-viz), theme clair/sombre,
tuiles KPI + graphiques + table des commandes a risque.

Sortie : dashboard/index.html
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from fibre360.config import Config, get_logger

log = get_logger("fibre360.dashboard")

# Palette categorielle validee (data-viz) - light / dark
SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4"]
STATUS = {"bon": "#008300", "moyen": "#eda100", "mauvais": "#e34948"}


def _kpi(synthese: pd.DataFrame, libelle: str) -> str:
    m = synthese[synthese.Indicateur.str.contains(libelle, case=False, regex=False)]
    return str(m.Valeur.iloc[0]) if len(m) else "-"


def generer(cfg: Config, data: dict) -> str:
    syn = data["synthese"]
    canal = data["par_canal"]
    mois = data["forecast"]
    goulots = data["pm_goulots"].head(6)
    scores = data["scores_en_cours"]
    retention = data["retention_canal"]
    churn_auc = data.get("churn_auc", "-")
    risque_auc = data.get("risque_auc", "-")

    # --- series pour Chart.js ---
    canal_sorted = canal.sort_values("nb_commandes", ascending=False)
    niv = (scores.niveau_risque.value_counts().reindex(
        ["Faible", "Moyen", "Eleve"]).fillna(0).astype(int)
        if len(scores) else pd.Series([0, 0, 0], index=["Faible", "Moyen", "Eleve"]))

    payload = {
        "canal_labels": canal_sorted.canal.tolist(),
        "canal_sla": canal_sorted.taux_livraison_delai_pct.tolist(),
        "canal_echec": canal_sorted.taux_echec_pct.tolist(),
        "mois_labels": mois.mois.tolist(),
        "mois_vol_hist": [v if t == "historique" else None
                          for v, t in zip(mois.nb_commandes, mois.type)],
        "mois_vol_prev": [v if t == "prevision" else None
                          for v, t in zip(mois.nb_commandes, mois.type)],
        "mois_delai": mois.delai_moyen_j.tolist(),
        "goulot_labels": goulots.transition.tolist(),
        "goulot_vals": goulots.duree_moyenne_j.tolist(),
        "risque_labels": niv.index.tolist(),
        "risque_vals": niv.values.tolist(),
        "ret_labels": retention.canal.tolist() if len(retention) else [],
        "ret_vals": retention.retention_12m_pct.tolist() if len(retention) else [],
        "series": SERIES, "status": STATUS,
    }

    # tableau des commandes a risque (top 15)
    top = scores.head(15) if len(scores) else pd.DataFrame()
    lignes_tbl = "".join(
        f"<tr><td>{r.id_commande}</td><td>{r.canal}</td><td>{r.offre}</td>"
        f"<td>{r.sous_traitant}</td><td>{r.region}</td>"
        f"<td style='text-align:right'>{r.age_jours:.0f}</td>"
        f"<td style='text-align:right;font-weight:600'>{r.score_risque:.2f}</td>"
        f"<td><span class='badge {_cls(r.niveau_risque)}'>{r.niveau_risque}</span></td></tr>"
        for r in top.itertuples(index=False)) or "<tr><td colspan=8>Aucune commande en cours</td></tr>"

    html = _TEMPLATE.format(
        titre="Fibre 360 - Pilotage Commande vers Livraison",
        k_sla=_kpi(syn, "livraison dans les delais"),
        k_delai=_kpi(syn, "Delai moyen"),
        k_echec=_kpi(syn, "echec de raccordement"),
        k_nps=_kpi(syn, "NPS"),
        k_churn=_kpi(syn, "churn"),
        k_alertes=_kpi(syn, "Alertes SLA"),
        k_total=_kpi(syn, "Commandes totales"),
        k_ca=_kpi(syn, "CA mensuel"),
        risque_auc=risque_auc, churn_auc=churn_auc,
        lignes_tbl=lignes_tbl,
        data_json=json.dumps(payload),
    )
    cfg.paths.dashboard.mkdir(parents=True, exist_ok=True)
    out = cfg.paths.dashboard / "index.html"
    out.write_text(html, encoding="utf-8")
    log.info("Dashboard HTML genere -> %s", out)
    return str(out)


def _cls(niveau):
    return {"Eleve": "bad", "Moyen": "warn", "Faible": "ok"}.get(str(niveau), "")


_TEMPLATE = r"""<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{titre}</title>
<script src="assets/chart.umd.min.js"></script>
<style>
  :root {{
    --surface-0:#f4f5f3; --surface-1:#fcfcfb; --border:#e3e3df;
    --text-primary:#0b0b0b; --text-secondary:#52514e; --text-muted:#8a897f;
    --accent:#2a78d6; --ok:#008300; --warn:#eda100; --bad:#e34948;
    color-scheme:light;
  }}
  @media (prefers-color-scheme: dark) {{
    :root:not([data-theme="light"]) {{
      --surface-0:#121211; --surface-1:#1a1a19; --border:#33332f;
      --text-primary:#f0efec; --text-secondary:#c3c2b7; --text-muted:#8f8e85;
      --accent:#3987e5; color-scheme:dark;
    }}
  }}
  :root[data-theme="dark"] {{
    --surface-0:#121211; --surface-1:#1a1a19; --border:#33332f;
    --text-primary:#f0efec; --text-secondary:#c3c2b7; --text-muted:#8f8e85;
    --accent:#3987e5; color-scheme:dark;
  }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0; background:var(--surface-0); color:var(--text-primary);
    font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
    line-height:1.5; }}
  header {{ padding:24px 16px 8px; max-width:1200px; margin:0 auto; }}
  h1 {{ font-size:1.5rem; margin:0 0 4px; }}
  .sub {{ color:var(--text-secondary); font-size:.9rem; }}
  main {{ max-width:1200px; margin:0 auto; padding:16px; }}
  .tiles {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(150px,1fr));
    gap:12px; margin-bottom:20px; }}
  .tile {{ background:var(--surface-1); border:1px solid var(--border);
    border-radius:12px; padding:16px; }}
  .tile .label {{ font-size:.78rem; color:var(--text-secondary);
    text-transform:uppercase; letter-spacing:.03em; }}
  .tile .value {{ font-size:1.7rem; font-weight:700; margin-top:4px; }}
  .grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(340px,1fr)); gap:16px; }}
  .card {{ background:var(--surface-1); border:1px solid var(--border);
    border-radius:12px; padding:16px; }}
  .card h2 {{ font-size:1rem; margin:0 0 12px; }}
  .card canvas {{ max-height:300px; }}
  .wide {{ grid-column:1/-1; }}
  table {{ width:100%; border-collapse:collapse; font-size:.85rem; }}
  th,td {{ padding:7px 8px; border-bottom:1px solid var(--border); text-align:left; }}
  th {{ color:var(--text-secondary); font-weight:600; font-size:.75rem;
    text-transform:uppercase; }}
  .badge {{ padding:2px 8px; border-radius:999px; font-size:.75rem; font-weight:600; }}
  .badge.bad {{ background:#e3494822; color:var(--bad); }}
  .badge.warn {{ background:#eda10022; color:var(--warn); }}
  .badge.ok {{ background:#00830022; color:var(--ok); }}
  .toggle {{ position:fixed; top:16px; right:16px; background:var(--surface-1);
    border:1px solid var(--border); border-radius:8px; padding:6px 10px;
    cursor:pointer; color:var(--text-primary); font-size:.85rem; }}
  footer {{ max-width:1200px; margin:0 auto; padding:16px; color:var(--text-muted);
    font-size:.78rem; }}
</style>
</head>
<body>
<button class="toggle" onclick="toggleTheme()">Theme clair / sombre</button>
<header>
  <h1>Fibre 360&deg; &mdash; Pilotage du parcours Commande &rarr; Livraison</h1>
  <div class="sub">Donnees fictives de demonstration &middot; Modeles : AUC risque {risque_auc} &middot; AUC churn {churn_auc}</div>
</header>
<main>
  <div class="tiles">
    <div class="tile"><div class="label">Commandes</div><div class="value">{k_total}</div></div>
    <div class="tile"><div class="label">Livraison dans les delais</div><div class="value">{k_sla}</div></div>
    <div class="tile"><div class="label">Delai moyen</div><div class="value">{k_delai}</div></div>
    <div class="tile"><div class="label">Taux d'echec</div><div class="value">{k_echec}</div></div>
    <div class="tile"><div class="label">NPS moyen</div><div class="value">{k_nps}</div></div>
    <div class="tile"><div class="label">Churn client</div><div class="value">{k_churn}</div></div>
    <div class="tile"><div class="label">Alertes SLA</div><div class="value">{k_alertes}</div></div>
    <div class="tile"><div class="label">CA mensuel recurrent</div><div class="value">{k_ca}</div></div>
  </div>
  <div class="grid">
    <div class="card"><h2>Performance par canal (multi-canalite)</h2><canvas id="c_canal"></canvas></div>
    <div class="card"><h2>Repartition du risque (commandes en cours)</h2><canvas id="c_risque"></canvas></div>
    <div class="card wide"><h2>Volume de commandes : historique & prevision</h2><canvas id="c_vol"></canvas></div>
    <div class="card"><h2>Delai moyen mensuel (jours)</h2><canvas id="c_delai"></canvas></div>
    <div class="card"><h2>Principaux goulots du process (j/cas)</h2><canvas id="c_goulot"></canvas></div>
    <div class="card"><h2>Retention a 12 mois par canal</h2><canvas id="c_ret"></canvas></div>
    <div class="card wide">
      <h2>Top commandes en cours a risque (a traiter en priorite)</h2>
      <table><thead><tr><th>Commande</th><th>Canal</th><th>Offre</th><th>Sous-traitant</th>
        <th>Region</th><th style="text-align:right">Age (j)</th>
        <th style="text-align:right">Score</th><th>Niveau</th></tr></thead>
        <tbody>{lignes_tbl}</tbody></table>
    </div>
  </div>
</main>
<footer>Genere automatiquement par le pipeline Fibre 360 (fibre360/reporting/dashboard.py).
  Donnees synthetiques &mdash; aucune donnee reelle.</footer>
<script>
const D = {data_json};
function css(v){{ return getComputedStyle(document.documentElement).getPropertyValue(v).trim(); }}
function toggleTheme(){{
  const cur = document.documentElement.getAttribute('data-theme');
  const dark = cur ? cur==='dark' : window.matchMedia('(prefers-color-scheme: dark)').matches;
  document.documentElement.setAttribute('data-theme', dark ? 'light' : 'dark');
  setTimeout(()=>location.reload(), 50);
}}
Chart.defaults.color = css('--text-secondary');
Chart.defaults.borderColor = css('--border');
Chart.defaults.font.family = getComputedStyle(document.body).fontFamily;
const S = D.series;

new Chart(c_canal, {{ type:'bar', data:{{ labels:D.canal_labels, datasets:[
  {{label:'% dans les delais', data:D.canal_sla, backgroundColor:S[0], borderRadius:4}},
  {{label:"% d'echec", data:D.canal_echec, backgroundColor:S[1], borderRadius:4}} ]}},
  options:{{responsive:true, scales:{{y:{{beginAtZero:true, max:100,
    ticks:{{callback:v=>v+'%'}}}}}}}} }});

new Chart(c_risque, {{ type:'doughnut', data:{{ labels:D.risque_labels, datasets:[
  {{data:D.risque_vals, backgroundColor:[D.status.bon, D.status.moyen, D.status.mauvais]}} ]}},
  options:{{responsive:true, plugins:{{legend:{{position:'bottom'}}}}}} }});

new Chart(c_vol, {{ type:'line', data:{{ labels:D.mois_labels, datasets:[
  {{label:'Historique', data:D.mois_vol_hist, borderColor:S[0], backgroundColor:S[0]+'33',
    tension:.25, spanGaps:false, pointRadius:2, fill:true}},
  {{label:'Prevision', data:D.mois_vol_prev, borderColor:S[1], borderDash:[6,4],
    tension:.25, pointRadius:3}} ]}},
  options:{{responsive:true, interaction:{{mode:'index', intersect:false}},
    scales:{{y:{{beginAtZero:true}}}}}} }});

new Chart(c_delai, {{ type:'line', data:{{ labels:D.mois_labels, datasets:[
  {{label:'Delai moyen (j)', data:D.mois_delai, borderColor:S[2],
    backgroundColor:S[2]+'33', tension:.25, pointRadius:2, fill:true}} ]}},
  options:{{responsive:true, plugins:{{legend:{{display:false}},
    annotation:false}}, scales:{{y:{{beginAtZero:false}}}}}} }});

new Chart(c_goulot, {{ type:'bar', data:{{ labels:D.goulot_labels, datasets:[
  {{label:'j/cas', data:D.goulot_vals, backgroundColor:S[3], borderRadius:4}} ]}},
  options:{{indexAxis:'y', responsive:true, plugins:{{legend:{{display:false}}}}}} }});

new Chart(c_ret, {{ type:'bar', data:{{ labels:D.ret_labels, datasets:[
  {{label:'% retenus a 12 mois', data:D.ret_vals, backgroundColor:S[4], borderRadius:4}} ]}},
  options:{{responsive:true, plugins:{{legend:{{display:false}}}},
    scales:{{y:{{beginAtZero:true, max:100, ticks:{{callback:v=>v+'%'}}}}}}}} }});
</script>
</body>
</html>"""
