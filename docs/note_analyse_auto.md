# Note d'analyse automatisee - Parcours Commande -> Livraison Fibre
_Genere par l'agent IA le 2026-11-05 - donnees fictives de demonstration_

## 1. Synthese executive

Sur **60,000** commandes, le taux de livraison dans les
delais est de **63.0%** (delai moyen
14.1 j, objectif 15 j).
Taux d'echec de raccordement : **5.3%** ;
NPS **31** ; churn client **15.8%**.
A date, **1034** commandes sont en cours, dont
**363** a risque eleve et **116** en alerte SLA
(modele de scoring, AUC 0.8799).

## 2. Multi-canalite

Canal le plus performant : **Boutique** (69.2% dans
les delais, NPS 44). Canal le plus degrade : **Distributeur**
(52.7%, NPS 13) - un ecart de
**16.5 points** a resorber.

## 3. Sous-traitance, process et portefeuille

Le sous-traitant **OptiReseau** concentre le taux d'echec le plus eleve
(**6.8%**). Le process mining identifie le goulot principal sur
**Prise de RDV -> Construction ligne** (**12.53 j/cas**). Cote portefeuille,
**PF-Sud** est le plus en retrait
(61.8% dans les delais).

## 4. Facteurs de risque (importance par permutation)

- `zone_a_construire` (importance 0.3051)
- `sous_traitant` (importance 0.0606)
- `canal` (importance 0.0222)
- `segment` (importance 0.0027)
- `offre` (importance 0.0002)
- `montant_mensuel` (importance 0.0001)

## 5. Plan d'actions priorise

| # | Action | Levier | Horizon |
|---|--------|--------|---------|
| 1 | Traiter les **116 alertes SLA** + **363 dossiers a risque eleve** (liste du scoring) | Portefeuille | Immediat |
| 2 | Plan de progres avec **OptiReseau** + rebasculer les volumes vers les prestataires performants | Sous-traitance | 1 mois |
| 3 | Anticiper les zones a construire pour reduire le goulot **Prise de RDV -> Construction ligne** | Process | 1-2 mois |
| 4 | Diffuser les pratiques du canal **Boutique** vers **Distributeur** (+16.5 pts potentiels) | Multi-canalite | 2-3 mois |
| 5 | Campagne de retention ciblant les clients a fort score de churn (AUC 0.635) | Retention | 1-2 mois |
| 6 | Accompagner le portefeuille **PF-Sud** | Portefeuille | 2 mois |

> Analyse generee a partir du datamart, du process mining, du scoring et du modele
> de churn. A valider avec les equipes metier (ecoute utilisateur).
