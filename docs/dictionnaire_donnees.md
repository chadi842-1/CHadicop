# Dictionnaire de données — Plateforme Fibre 360

Données **fictives** générées par `fibre360/data_generation/generators.py`
(8 sources relationnelles sur 2 ans d'historique).

## Schéma relationnel (simplifié)

```
clients (id_client) 1───* commandes (id_commande) 1───* evenements
   │                          │ 1───* interventions *───1 techniciens (id_technicien)
   │                          │ 1───* satisfaction
   │                          │ 1───* reclamations
   └──────────────────────────┘ 1───* factures
```

## `clients`
| Champ | Type | Description |
|-------|------|-------------|
| id_client | texte | Clé client |
| age | entier | Âge |
| csp | texte | Catégorie socio-pro |
| segment | texte | Grand Public / Pro |
| region, departement | texte | Localisation |
| anciennete_client_mois | entier | Ancienneté chez l'opérateur |
| churn | booléen | Client résilié |
| date_resiliation | datetime | Date de résiliation (si churn) |

## `techniciens`
| Champ | Type | Description |
|-------|------|-------------|
| id_technicien | texte | Clé technicien |
| sous_traitant | texte | Prestataire employeur |
| region | texte | Zone d'intervention |
| anciennete_mois | entier | Ancienneté |
| taux_reussite_ref | décimal | Taux de réussite de référence |

## `commandes`
| Champ | Type | Description |
|-------|------|-------------|
| id_commande | texte | Clé commande |
| id_client | texte | → clients |
| date_commande | date | Date de passation |
| canal | texte | Boutique, Web, Telephone, Distributeur, App mobile |
| offre, debit_gbps, montant_mensuel | — | Offre Fibre souscrite |
| segment, region, departement | texte | Attributs |
| anciennete_client_mois | entier | Ancienneté à la commande |
| gestionnaire_portefeuille | texte | Portefeuille responsable |
| zone_a_construire | booléen | Raccordement nécessitant une construction |
| sous_traitant | texte | → prestataire |
| id_technicien | texte | → techniciens |

## `evenements` (event log)
| Champ | Type | Description |
|-------|------|-------------|
| id_commande | texte | → commandes |
| etape | texte | Activité du parcours |
| horodatage | datetime | Date/heure |
| statut | texte | OK / ECHEC / ANNULEE |
| acteur | texte | Système ou acteur |

Étapes : Commande enregistree → Etude eligibilite → Prise de RDV →
(Construction ligne) → Intervention technicien → Mise en service.
Terminaisons : Echec raccordement, Annulation client.

## `interventions`
id_commande, id_intervention, date_prevue, date_realisee, sous_traitant,
id_technicien, resultat (OK/Echec), motif_echec.

## `satisfaction`
id_commande, date_enquete, nps (-100..100), canal_contact.

## `reclamations`
id_commande, id_reclamation, date_reclamation, motif, canal, resolu,
delai_resolution_j.

## `factures`
id_commande, id_client, mois_facture, montant (3 mois post-livraison).

## Table de faits `faits_parcours` (champs enrichis)
statut_parcours, delai_livraison_j, livree_dans_delai, nb_interventions,
resultat_intervention, motif_echec, nps, nb_reclamations, reclamation,
reclamation_resolue, delai_resolution_j, ca_facture, taux_reussite_ref,
anciennete_technicien_mois, churn, date_resiliation, age, csp, annee_mois,
trimestre, annee, age_jours, alerte_sla.
