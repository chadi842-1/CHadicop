# Plan d'actions stratégique — Parcours Commande → Livraison Fibre

Synthèse décisionnelle issue du datamart, du process mining, du scoring et du
modèle de churn. (Chiffres sur données fictives — 60 000 commandes, seed 42.)

## Diagnostic en 6 constats

1. **63 %** des commandes livrées respectent le SLA de 15 j (délai moyen 14,1 j) :
   plus d'un tiers des livraisons sont hors délai — gisement de progrès majeur.
2. **Multi-canalité très hétérogène** : Boutique 69,2 % dans les délais (NPS 44)
   vs Distributeur 52,7 % (NPS 13, délai moyen 16 j) — **~16,5 points d'écart**.
3. **Sous-traitance = levier n°1** : le sous-traitant le plus faible concentre le
   taux d'échec le plus élevé ; le scoring le confirme (facteur à forte importance).
4. **Goulot de process** : la transition « Prise de RDV → Construction ligne »
   (zones à construire) dure **12,5 j/cas** — premier contributeur au délai total.
5. **Risque actionnable** : **1 034** commandes en cours, dont **363** à risque
   élevé et **116** déjà en alerte SLA (à traiter en priorité).
6. **Churn & insatisfaction** : taux de réclamation **18,8 %**, churn **15,8 %** ;
   un délai dépassé se traduit par plus de réclamations et de résiliations.

## Plan d'actions priorisé

| Priorité | Action | Levier | KPI de suivi | Horizon |
|:---:|--------|--------|--------------|:---:|
| 🔴 P1 | Cellule de rattrapage sur les **116 alertes SLA** + **363 dossiers à risque élevé** (liste fournie par le scoring) | Portefeuille | Nb d'alertes SLA, taux de rattrapage | Immédiat |
| 🔴 P1 | Plan de progrès contractuel avec le sous-traitant le plus faible + rééquilibrage des volumes vers les prestataires performants | Sous-traitance | Taux d'échec par sous-traitant | 1 mois |
| 🟠 P2 | Anticiper les zones à construire (pré-étude, planification dédiée) pour réduire le goulot RDV → Construction | Process | Durée moyenne de la transition | 1–2 mois |
| 🟠 P2 | Industrialiser les bonnes pratiques du canal Boutique vers Web & Distributeur | Multi-canalité | Taux SLA & NPS par canal | 2–3 mois |
| 🟢 P3 | Campagne de rétention ciblant les clients à fort score de churn | Rétention | Taux de churn, NPS | 1–2 mois |
| 🟢 P3 | Déployer les alertes Power Automate + reporting hebdo automatisé | Automatisation | Délai de réaction, régularité | 1 mois |

## Gains attendus (ordre de grandeur, à valider avec le métier)

- Réduction du délai moyen de **2 à 3 jours** via le traitement du goulot.
- **+1 à 2 points** de taux de livraison dans les délais via la sous-traitance.
- Convergence des canaux : **~16 points** de potentiel sur le canal le plus faible.
- Détection proactive : passage d'un suivi **réactif** (Excel) à **prédictif** (scoring).
- Baisse du churn via une meilleure expérience de livraison et une rétention ciblée.

## Suite

Restitution aux équipes métier, recueil de leurs retours (écoute utilisateur),
puis itération sur les seuils d'alerte et les variables des modèles.
