# Plan d'actions stratégique — Parcours Commande → Livraison Fibre

Synthèse décisionnelle issue du datamart, du process mining et du scoring.
(Chiffres sur données fictives de démonstration — seed 42.)

## Diagnostic en 5 constats

1. **64 %** des commandes livrées respectent le SLA de 15 j (délai moyen 13,9 j) :
   marge de progrès importante, un tiers des livraisons sont hors délai.
2. **Multi-canalité hétérogène** : Boutique 69,7 % dans les délais (NPS 45) vs
   Distributeur 56,8 % (NPS 14) — **~13 points d'écart**.
3. **Sous-traitance = levier n°1** : OptiReseau concentre le taux d'échec le plus
   élevé ; le modèle de scoring confirme ce facteur (poids +1,08).
4. **Goulot de process** : la transition « Prise de RDV → Construction ligne »
   (zones à construire) dure **12,5 j/cas** en moyenne, principal contributeur au délai.
5. **422 commandes en cours**, dont **149 à risque élevé** et **44 déjà en
   alerte SLA** : un stock actionnable immédiatement.

## Plan d'actions priorisé

| Priorité | Action | Levier | KPI de suivi | Horizon |
|:---:|--------|--------|--------------|:---:|
| 🔴 P1 | Cellule de rattrapage ciblée sur les 44 alertes SLA + 149 dossiers à risque élevé (liste fournie par le scoring) | Portefeuille | Nb d'alertes SLA, taux de rattrapage | Immédiat |
| 🔴 P1 | Plan de progrès contractuel avec OptiReseau + rééquilibrage des volumes vers RacoNet/FibreExpress | Sous-traitance | Taux d'échec par sous-traitant | 1 mois |
| 🟠 P2 | Anticiper les zones à construire (pré-étude, planification dédiée) pour réduire le goulot RDV → Construction | Process | Durée moyenne de la transition | 1–2 mois |
| 🟠 P2 | Industrialiser les bonnes pratiques du canal Boutique vers Web & Distributeur | Multi-canalité | Taux SLA & NPS par canal | 2–3 mois |
| 🟢 P3 | Accompagnement des portefeuilles sous la moyenne (ex. PF-Centre) | Portefeuille | Taux SLA par gestionnaire | 2 mois |
| 🟢 P3 | Déployer les alertes Power Automate + reporting hebdo automatisé | Automatisation | Délai de réaction, régularité du reporting | 1 mois |

## Gains attendus (ordre de grandeur, à valider avec le métier)

- Réduction du délai moyen de **2 à 3 jours** via le traitement du goulot.
- **+1 à 2 points** de taux de livraison dans les délais via la sous-traitance.
- Convergence des canaux : **+13 points** de potentiel sur le canal le plus faible.
- Détection proactive : passage d'un suivi **réactif** (Excel) à **prédictif** (scoring).

## Suite

Restitution aux équipes métier, recueil de leurs retours (écoute utilisateur),
puis itération sur les seuils d'alerte et les variables du modèle de scoring.
