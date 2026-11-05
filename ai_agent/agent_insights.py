"""
agent_insights.py
=================
Agent IA d'aide a la decision : lit les KPI, le process mining et le scoring,
puis redige automatiquement une NOTE D'ANALYSE + un PLAN D'ACTIONS
(portefeuille, multi-canalite) a destination de la Direction.

Mission fiche de poste : "aider a la decision strategique et proposer des
plans d'actions", "analyses par outils d'Intelligence Artificielle",
"les agents IA".

Fonctionnement :
  - Mode LLM : si la cle ANTHROPIC_API_KEY est presente et le SDK installe,
    l'agent envoie une synthese chiffree au modele qui redige la note.
  - Mode hors-ligne (fallback) : un moteur de regles genere la meme note de
    facon deterministe, SANS dependance externe (le projet reste reproductible).

Sortie : docs/note_analyse_auto.md
Usage  : python ai_agent/agent_insights.py
"""
from __future__ import annotations

import os
from datetime import date
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
EXPORTS = ROOT / "data" / "exports"
MART = ROOT / "data" / "mart"
DOCS = ROOT / "docs"

MODELE_LLM = "claude-opus-4-8"  # modifiable selon le modele disponible


# --------------------------------------------------------------------------- #
# 1) Collecte des faits chiffres (features de l'agent)
# --------------------------------------------------------------------------- #
def collecter_contexte() -> dict:
    faits = pd.read_csv(MART / "faits_parcours.csv")
    canal = pd.read_csv(EXPORTS / "kpi_par_canal.csv")
    st = pd.read_csv(EXPORTS / "kpi_par_sous_traitant.csv")
    pf = pd.read_csv(EXPORTS / "kpi_par_portefeuille.csv")
    goulots = pd.read_csv(EXPORTS / "pm_goulots.csv")
    importances = pd.read_csv(EXPORTS / "scoring_importances.csv")
    scores = pd.read_csv(EXPORTS / "scoring_commandes_en_cours.csv")

    livrees = faits[faits["statut_parcours"] == "Livree"]
    ctx = {
        "date": date.today().isoformat(),
        "nb_commandes": int(len(faits)),
        "taux_sla": round(livrees["livree_dans_delai"].mean() * 100, 1),
        "delai_moyen": round(livrees["delai_livraison_j"].mean(), 1),
        "taux_echec": round((faits["statut_parcours"] == "Echec raccordement").mean() * 100, 1),
        "nps": round(livrees["nps"].mean()),
        "canal_meilleur": canal.sort_values("taux_livraison_delai_%", ascending=False).iloc[0].to_dict(),
        "canal_pire": canal.sort_values("taux_livraison_delai_%").iloc[0].to_dict(),
        "st_pire": st.sort_values("taux_echec_%", ascending=False).iloc[0].to_dict(),
        "pf_pire": pf.sort_values("taux_livraison_delai_%").iloc[0].to_dict(),
        "goulot_principal": goulots.iloc[0].to_dict(),
        "top_facteurs": importances.head(5).to_dict("records"),
        "nb_en_cours": int(len(scores)),
        "nb_risque_eleve": int((scores["niveau_risque"] == "Eleve").sum()) if len(scores) else 0,
        "nb_alertes": int(scores["alerte_sla"].sum()) if len(scores) else 0,
    }
    return ctx


# --------------------------------------------------------------------------- #
# 2a) Redaction via LLM (mode connecte, optionnel)
# --------------------------------------------------------------------------- #
def rediger_llm(ctx: dict) -> str | None:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return None
    try:
        import anthropic
    except ImportError:
        return None

    prompt = (
        "Tu es analyste de donnees chez un operateur telecom. A partir des "
        "indicateurs chiffres ci-dessous sur le parcours Commande->Livraison "
        "de la Fibre, redige en francais une note d'analyse synthetique pour la "
        "Direction (3-4 paragraphes) suivie d'un plan d'actions priorise "
        "(portefeuille, multi-canalite, sous-traitance). Sois factuel et "
        "oriente decision.\n\n"
        f"Indicateurs : {ctx}"
    )
    try:
        client = anthropic.Anthropic()
        msg = client.messages.create(
            model=MODELE_LLM, max_tokens=1500,
            messages=[{"role": "user", "content": prompt}],
        )
        return msg.content[0].text
    except Exception as e:  # degradation silencieuse vers le fallback
        print(f"  (LLM indisponible : {e} -> fallback regles)")
        return None


# --------------------------------------------------------------------------- #
# 2b) Redaction par moteur de regles (mode hors-ligne, deterministe)
# --------------------------------------------------------------------------- #
def rediger_regles(ctx: dict) -> str:
    cm, cp = ctx["canal_meilleur"], ctx["canal_pire"]
    st, pf = ctx["st_pire"], ctx["pf_pire"]
    g = ctx["goulot_principal"]
    ecart_canal = round(cm["taux_livraison_delai_%"] - cp["taux_livraison_delai_%"], 1)

    note = f"""# Note d'analyse automatisee - Parcours Commande -> Livraison Fibre
_Genere par l'agent IA le {ctx['date']} - donnees fictives de demonstration_

## 1. Synthese executive

Sur un portefeuille de **{ctx['nb_commandes']:,} commandes**, le taux de livraison
dans les delais s'etablit a **{ctx['taux_sla']}%** pour un delai moyen de
**{ctx['delai_moyen']} jours** (objectif SLA : 15 j). Le taux d'echec de
raccordement est de **{ctx['taux_echec']}%** et le NPS moyen de **{ctx['nps']}**.
A date, **{ctx['nb_en_cours']} commandes sont en cours**, dont
**{ctx['nb_risque_eleve']} a risque eleve** et **{ctx['nb_alertes']} deja en
alerte SLA** : ce sont les dossiers a traiter en priorite.

## 2. Analyse multi-canalite

Le canal **{cm['canal']}** est le plus performant
({cm['taux_livraison_delai_%']}% dans les delais, NPS {cm['nps_moyen']:.0f}),
tandis que le canal **{cp['canal']}** est le plus degrade
({cp['taux_livraison_delai_%']}% dans les delais, NPS {cp['nps_moyen']:.0f}).
L'ecart de **{ecart_canal} points** entre canaux est le premier levier
d'homogeneisation de l'experience client.

## 3. Sous-traitance et goulots de process

Le sous-traitant **{st['sous_traitant']}** concentre le taux d'echec le plus
eleve (**{st['taux_echec_%']}%**). Le process mining identifie le principal
goulot sur la transition **{g['transition']}**
(**{g['duree_moyenne_j']} j/cas** en moyenne), liee aux zones a construire.
Cote portefeuille, **{pf['gestionnaire_portefeuille']}** affiche le taux de
livraison dans les delais le plus faible ({pf['taux_livraison_delai_%']}%).

## 4. Facteurs de risque (modele de scoring)

Les principaux facteurs qui augmentent le risque d'un parcours degrade :
"""
    for f in ctx["top_facteurs"]:
        note += f"- `{f['facteur']}` ({f['effet']}, poids {f['poids']})\n"

    note += f"""
## 5. Plan d'actions priorise

| # | Action | Cible | Impact attendu | Horizon |
|---|--------|-------|----------------|---------|
| 1 | Cellule de rattrapage sur les **{ctx['nb_alertes']} alertes SLA** et les **{ctx['nb_risque_eleve']} dossiers a risque eleve** | Commandes en cours | Reduction des depassements de delai | Immediat |
| 2 | Plan de progres contractuel avec **{st['sous_traitant']}** (taux d'echec {st['taux_echec_%']}%) | Sous-traitance | -1 a -2 pts de taux d'echec | 1 mois |
| 3 | Fluidifier la transition **{g['transition']}** (anticipation des zones a construire) | Process | -2 a -3 j sur le delai moyen | 1-2 mois |
| 4 | Diffuser les bonnes pratiques du canal **{cm['canal']}** vers **{cp['canal']}** | Multi-canalite | +{ecart_canal} pts potentiels | 2-3 mois |
| 5 | Accompagnement du portefeuille **{pf['gestionnaire_portefeuille']}** | Portefeuille | Convergence vers la moyenne | 2 mois |

> Note : analyse produite automatiquement a partir du datamart, du process
> mining et du modele de scoring. A valider avec les equipes metier avant
> deploiement (la fiche de poste insiste sur l'ecoute des utilisateurs).
"""
    return note


def main():
    DOCS.mkdir(parents=True, exist_ok=True)
    ctx = collecter_contexte()

    note = rediger_llm(ctx)
    mode = "LLM (Claude)"
    if note is None:
        note = rediger_regles(ctx)
        mode = "moteur de regles (hors-ligne)"

    out = DOCS / "note_analyse_auto.md"
    out.write_text(note, encoding="utf-8")
    print("=" * 60)
    print(f"AGENT IA - Note d'analyse generee ({mode})")
    print("=" * 60)
    print(f"  Taux SLA={ctx['taux_sla']}% | echec={ctx['taux_echec']}% | "
          f"en cours={ctx['nb_en_cours']} (risque eleve={ctx['nb_risque_eleve']})")
    print(f"OK : note ecrite -> {out}")


if __name__ == "__main__":
    main()
