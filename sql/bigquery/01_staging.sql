-- =====================================================================
-- 01_staging.sql  (GCP BigQuery - Standard SQL)
-- Couche STAGING : nettoyage et typage des 8 sources brutes.
-- Projet "Fibre 360" - parcours Commande -> Livraison.
--
-- Hypothese : les CSV de data/raw/ sont charges dans le dataset `fibre_raw`
--   (via `bq load` ou un transfert GCS). Staging materialise dans `fibre_stg`.
-- =====================================================================

CREATE OR REPLACE TABLE `fibre_stg.clients` AS
SELECT id_client, CAST(age AS INT64) AS age, csp, segment, region,
       CAST(departement AS STRING) AS departement,
       CAST(anciennete_client_mois AS INT64) AS anciennete_client_mois,
       CAST(churn AS BOOL) AS churn,
       SAFE_CAST(date_resiliation AS TIMESTAMP) AS date_resiliation
FROM `fibre_raw.clients`
WHERE id_client IS NOT NULL;

CREATE OR REPLACE TABLE `fibre_stg.techniciens` AS
SELECT id_technicien, sous_traitant, region,
       CAST(anciennete_mois AS INT64) AS anciennete_mois,
       CAST(taux_reussite_ref AS FLOAT64) AS taux_reussite_ref
FROM `fibre_raw.techniciens`;

CREATE OR REPLACE TABLE `fibre_stg.commandes` AS
SELECT id_commande, id_client, DATE(date_commande) AS date_commande,
       canal, offre, CAST(debit_gbps AS INT64) AS debit_gbps,
       CAST(montant_mensuel AS NUMERIC) AS montant_mensuel,
       segment, region, CAST(departement AS STRING) AS departement,
       CAST(anciennete_client_mois AS INT64) AS anciennete_client_mois,
       gestionnaire_portefeuille, CAST(zone_a_construire AS BOOL) AS zone_a_construire,
       sous_traitant, id_technicien
FROM `fibre_raw.commandes`
WHERE id_commande IS NOT NULL;

CREATE OR REPLACE TABLE `fibre_stg.evenements` AS
SELECT id_commande, etape, TIMESTAMP(horodatage) AS horodatage, statut, acteur
FROM `fibre_raw.evenements`
WHERE id_commande IS NOT NULL
QUALIFY ROW_NUMBER() OVER (
  PARTITION BY id_commande, etape, horodatage ORDER BY horodatage) = 1;

CREATE OR REPLACE TABLE `fibre_stg.interventions` AS
SELECT id_commande, id_intervention, TIMESTAMP(date_prevue) AS date_prevue,
       TIMESTAMP(date_realisee) AS date_realisee, sous_traitant, id_technicien,
       resultat, NULLIF(motif_echec, '') AS motif_echec
FROM `fibre_raw.interventions`;

CREATE OR REPLACE TABLE `fibre_stg.satisfaction` AS
SELECT id_commande, DATE(date_enquete) AS date_enquete,
       CAST(nps AS INT64) AS nps, canal_contact
FROM `fibre_raw.satisfaction`;

CREATE OR REPLACE TABLE `fibre_stg.reclamations` AS
SELECT id_commande, id_reclamation, DATE(date_reclamation) AS date_reclamation,
       motif, canal, CAST(resolu AS BOOL) AS resolu,
       SAFE_CAST(delai_resolution_j AS INT64) AS delai_resolution_j
FROM `fibre_raw.reclamations`;

CREATE OR REPLACE TABLE `fibre_stg.factures` AS
SELECT id_commande, id_client, DATE(mois_facture) AS mois_facture,
       CAST(montant AS NUMERIC) AS montant
FROM `fibre_raw.factures`;
