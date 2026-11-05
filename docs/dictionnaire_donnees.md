# Dictionnaire de données — Projet « Fibre 360° »

Données **fictives** générées par `scripts/01_generate_data.py`.

## Source `commandes` (référentiel des commandes Fibre)

| Champ | Type | Description |
|-------|------|-------------|
| id_commande | texte | Identifiant unique de la commande (clé) |
| id_client | texte | Identifiant client |
| date_commande | date | Date de passation de la commande |
| canal | texte | Canal de vente : Boutique, Web, Telephone, Distributeur |
| offre | texte | Offre Fibre souscrite |
| debit_gbps | entier | Débit en Gb/s (1, 2, 5, 8) |
| montant_mensuel | décimal | Abonnement mensuel (€) |
| segment | texte | Grand Public / Pro |
| region, departement | texte | Localisation |
| gestionnaire_portefeuille | texte | Portefeuille responsable |
| zone_a_construire | booléen | Vrai si raccordement nécessitant une construction |
| sous_traitant | texte | Prestataire de raccordement |

## Source `evenements` (journal d'événements = event log)

| Champ | Type | Description |
|-------|------|-------------|
| id_commande | texte | Clé de rapprochement |
| etape | texte | Activité du parcours (voir liste ci-dessous) |
| horodatage | datetime | Date/heure de l'événement |
| statut | texte | OK / ECHEC / ANNULEE |
| acteur | texte | Système ou acteur ayant produit l'événement |

**Étapes du parcours** : Commande enregistree → Etude eligibilite →
Prise de RDV → (Construction ligne) → Intervention technicien → Mise en service.
Terminaisons alternatives : Echec raccordement, Annulation client.

## Source `interventions` (interventions techniques)

| Champ | Type | Description |
|-------|------|-------------|
| id_commande | texte | Clé |
| id_intervention | texte | Identifiant de l'intervention |
| date_prevue / date_realisee | datetime | Planifié vs réalisé |
| sous_traitant | texte | Prestataire |
| resultat | texte | OK / Echec |
| motif_echec | texte | Motif en cas d'échec (nullable) |

## Source `satisfaction` (enquête post-livraison)

| Champ | Type | Description |
|-------|------|-------------|
| id_commande | texte | Clé |
| date_enquete | date | Date de l'enquête |
| nps | entier | Score NPS (-100 à 100) |
| canal_contact | texte | Email / SMS / Appel |
| reclamation | booléen | Réclamation déposée |

## Table de faits `faits_parcours` (champs enrichis principaux)

| Champ | Description |
|-------|-------------|
| statut_parcours | Livree / Echec raccordement / Annulee / En cours |
| delai_livraison_j | Délai commande → mise en service (jours) |
| livree_dans_delai | 1 si délai ≤ SLA (15 j), 0 sinon, NA si non livrée |
| nb_interventions | Nombre d'interventions |
| resultat_intervention, motif_echec | Dernière intervention |
| nps, reclamation | Satisfaction |
| age_jours | Ancienneté de la commande (vs 2026-11-01) |
| alerte_sla | Vrai si commande en cours dépassant déjà le SLA |
