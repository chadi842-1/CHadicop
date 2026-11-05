# Note d'analyse automatisee - Parcours Commande -> Livraison Fibre
_Genere par l'agent IA le 2026-11-05 - donnees fictives de demonstration_

## 1. Synthese executive

Sur un portefeuille de **12,000 commandes**, le taux de livraison
dans les delais s'etablit a **64.0%** pour un delai moyen de
**13.9 jours** (objectif SLA : 15 j). Le taux d'echec de
raccordement est de **5.4%** et le NPS moyen de **31**.
A date, **422 commandes sont en cours**, dont
**149 a risque eleve** et **44 deja en
alerte SLA** : ce sont les dossiers a traiter en priorite.

## 2. Analyse multi-canalite

Le canal **Boutique** est le plus performant
(69.7% dans les delais, NPS 45),
tandis que le canal **Distributeur** est le plus degrade
(56.8% dans les delais, NPS 14).
L'ecart de **12.9 points** entre canaux est le premier levier
d'homogeneisation de l'experience client.

## 3. Sous-traitance et goulots de process

Le sous-traitant **OptiReseau** concentre le taux d'echec le plus
eleve (**7.2%**). Le process mining identifie le principal
goulot sur la transition **Prise de RDV -> Construction ligne**
(**12.46 j/cas** en moyenne), liee aux zones a construire.
Cote portefeuille, **PF-Centre** affiche le taux de
livraison dans les delais le plus faible (62.2%).

## 4. Facteurs de risque (modele de scoring)

Les principaux facteurs qui augmentent le risque d'un parcours degrade :
- `zone_a_construire_True` (augmente le risque, poids 2.222)
- `zone_a_construire_False` (reduit le risque, poids -1.845)
- `sous_traitant_OptiReseau` (augmente le risque, poids 1.079)
- `sous_traitant_RacoNet` (reduit le risque, poids -0.823)
- `canal_Distributeur` (augmente le risque, poids 0.652)

## 5. Plan d'actions priorise

| # | Action | Cible | Impact attendu | Horizon |
|---|--------|-------|----------------|---------|
| 1 | Cellule de rattrapage sur les **44 alertes SLA** et les **149 dossiers a risque eleve** | Commandes en cours | Reduction des depassements de delai | Immediat |
| 2 | Plan de progres contractuel avec **OptiReseau** (taux d'echec 7.2%) | Sous-traitance | -1 a -2 pts de taux d'echec | 1 mois |
| 3 | Fluidifier la transition **Prise de RDV -> Construction ligne** (anticipation des zones a construire) | Process | -2 a -3 j sur le delai moyen | 1-2 mois |
| 4 | Diffuser les bonnes pratiques du canal **Boutique** vers **Distributeur** | Multi-canalite | +12.9 pts potentiels | 2-3 mois |
| 5 | Accompagnement du portefeuille **PF-Centre** | Portefeuille | Convergence vers la moyenne | 2 mois |

> Note : analyse produite automatiquement a partir du datamart, du process
> mining et du modele de scoring. A valider avec les equipes metier avant
> deploiement (la fiche de poste insiste sur l'ecoute des utilisateurs).
