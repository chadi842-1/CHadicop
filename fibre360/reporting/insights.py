"""
fibre360.reporting.insights
===========================
Agent IA d'aide a la decision : synthetise les resultats du pipeline et redige
une note d'analyse + un plan d'actions (portefeuille, multi-canalite,
sous-traitance, retention). Mode LLM (Claude) si cle disponible, sinon moteur
de regles deterministe hors-ligne.
"""
from __future__ import annotations

import os
from datetime import date

import pandas as pd

from fibre360.config import Config, get_logger

log = get_logger("fibre360.insights")
MODELE_LLM = "claude-opus-4-8"


def construire_contexte(cfg: Config, res: dict) -> dict:
    syn = res["synthese"].set_index("Indicateur")["Valeur"].to_dict()
    canal = res["par_canal"]
    st = res["par_sous_traitant"]
    pf = res["par_portefeuille"]
    goulots = res["pm_goulots"]
    scores = res["scores_en_cours"]
    return {
        "date": date.today().isoformat(),
        "synthese": syn,
        "canal_meilleur": canal.sort_values("taux_livraison_delai_pct", ascending=False).iloc[0].to_dict(),
        "canal_pire": canal.sort_values("taux_livraison_delai_pct").iloc[0].to_dict(),
        "st_pire": st.sort_values("taux_echec_pct", ascending=False).iloc[0].to_dict(),
        "pf_pire": pf.sort_values("taux_livraison_delai_pct").iloc[0].to_dict(),
        "goulot": goulots.iloc[0].to_dict(),
        "importances": res["importances"].head(6).to_dict("records"),
        "nb_en_cours": int(len(scores)),
        "nb_risque_eleve": int((scores.niveau_risque == "Eleve").sum()) if len(scores) else 0,
        "nb_alertes": int(scores.alerte_sla.sum()) if len(scores) else 0,
        "risque_auc": res.get("risque_auc"),
        "churn_auc": res.get("churn_auc"),
    }


def _llm(ctx: dict) -> str | None:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return None
    try:
        import anthropic
    except ImportError:
        return None
    prompt = ("Tu es analyste de donnees chez un operateur telecom. A partir des "
              "indicateurs ci-dessous sur le parcours Commande->Livraison de la Fibre, "
              "redige en francais une note d'analyse pour la Direction (3-4 paragraphes) "
              "suivie d'un plan d'actions priorise (portefeuille, multi-canalite, "
              f"sous-traitance, retention). Indicateurs : {ctx}")
    try:
        client = anthropic.Anthropic()
        msg = client.messages.create(model=MODELE_LLM, max_tokens=1600,
                                     messages=[{"role": "user", "content": prompt}])
        return msg.content[0].text
    except Exception as e:  # pragma: no cover
        log.warning("LLM indisponible (%s) -> fallback regles", e)
        return None


def _regles(ctx: dict) -> str:
    s = ctx["synthese"]
    cm, cp = ctx["canal_meilleur"], ctx["canal_pire"]
    st, pf, g = ctx["st_pire"], ctx["pf_pire"], ctx["goulot"]
    ecart = round(cm["taux_livraison_delai_pct"] - cp["taux_livraison_delai_pct"], 1)
    note = f"""# Note d'analyse automatisee - Parcours Commande -> Livraison Fibre
_Genere par l'agent IA le {ctx['date']} - donnees fictives de demonstration_

## 1. Synthese executive

Sur **{s.get('Commandes totales')}** commandes, le taux de livraison dans les
delais est de **{s.get('Taux de livraison dans les delais')}** (delai moyen
{s.get('Delai moyen (commande -> mise en service)')}, objectif {s.get('Objectif SLA')}).
Taux d'echec de raccordement : **{s.get("Taux d'echec de raccordement")}** ;
NPS **{s.get('NPS moyen (livrees)')}** ; churn client **{s.get('Taux de churn client')}**.
A date, **{ctx['nb_en_cours']}** commandes sont en cours, dont
**{ctx['nb_risque_eleve']}** a risque eleve et **{ctx['nb_alertes']}** en alerte SLA
(modele de scoring, AUC {ctx['risque_auc']}).

## 2. Multi-canalite

Canal le plus performant : **{cm['canal']}** ({cm['taux_livraison_delai_pct']}% dans
les delais, NPS {cm['nps_moyen']:.0f}). Canal le plus degrade : **{cp['canal']}**
({cp['taux_livraison_delai_pct']}%, NPS {cp['nps_moyen']:.0f}) - un ecart de
**{ecart} points** a resorber.

## 3. Sous-traitance, process et portefeuille

Le sous-traitant **{st['sous_traitant']}** concentre le taux d'echec le plus eleve
(**{st['taux_echec_pct']}%**). Le process mining identifie le goulot principal sur
**{g['transition']}** (**{g['duree_moyenne_j']} j/cas**). Cote portefeuille,
**{pf['gestionnaire_portefeuille']}** est le plus en retrait
({pf['taux_livraison_delai_pct']}% dans les delais).

## 4. Facteurs de risque (importance par permutation)

"""
    for f in ctx["importances"]:
        note += f"- `{f['feature']}` (importance {f['importance']})\n"
    note += f"""
## 5. Plan d'actions priorise

| # | Action | Levier | Horizon |
|---|--------|--------|---------|
| 1 | Traiter les **{ctx['nb_alertes']} alertes SLA** + **{ctx['nb_risque_eleve']} dossiers a risque eleve** (liste du scoring) | Portefeuille | Immediat |
| 2 | Plan de progres avec **{st['sous_traitant']}** + rebasculer les volumes vers les prestataires performants | Sous-traitance | 1 mois |
| 3 | Anticiper les zones a construire pour reduire le goulot **{g['transition']}** | Process | 1-2 mois |
| 4 | Diffuser les pratiques du canal **{cm['canal']}** vers **{cp['canal']}** (+{ecart} pts potentiels) | Multi-canalite | 2-3 mois |
| 5 | Campagne de retention ciblant les clients a fort score de churn (AUC {ctx['churn_auc']}) | Retention | 1-2 mois |
| 6 | Accompagner le portefeuille **{pf['gestionnaire_portefeuille']}** | Portefeuille | 2 mois |

> Analyse generee a partir du datamart, du process mining, du scoring et du modele
> de churn. A valider avec les equipes metier (ecoute utilisateur).
"""
    return note


def rediger(cfg: Config, res: dict) -> str:
    ctx = construire_contexte(cfg, res)
    note = _llm(ctx)
    mode = "LLM (Claude)"
    if note is None:
        note = _regles(ctx)
        mode = "moteur de regles hors-ligne"
    cfg.paths.docs.mkdir(parents=True, exist_ok=True)
    out = cfg.paths.docs / "note_analyse_auto.md"
    out.write_text(note, encoding="utf-8")
    log.info("Note d'analyse redigee (%s) -> %s", mode, out)
    return str(out)
