-- =====================================================================
-- 01_staging.sql  (GCP BigQuery - Standard SQL)
-- Couche STAGING : nettoyage et typage des 4 sources brutes.
-- Projet "Fibre 360" - parcours Commande -> Livraison.
--
-- Hypothese : les CSV de data/raw/ ont ete charges dans le dataset
--   `fibre_raw` (via `bq load` ou un transfert GCS).
-- Les vues de staging sont materialisees dans le dataset `fibre_stg`.
-- =====================================================================

-- ---- Commandes ------------------------------------------------------
CREATE OR REPLACE TABLE `fibre_stg.commandes` AS
SELECT
  id_commande,
  id_client,
  DATE(date_commande)                       AS date_commande,
  canal,
  offre,
  CAST(debit_gbps AS INT64)                 AS debit_gbps,
  CAST(montant_mensuel AS NUMERIC)          AS montant_mensuel,
  segment,
  region,
  CAST(departement AS STRING)               AS departement,
  gestionnaire_portefeuille,
  CAST(zone_a_construire AS BOOL)           AS zone_a_construire,
  sous_traitant
FROM `fibre_raw.commandes`
WHERE id_commande IS NOT NULL;

-- ---- Journal d'evenements (event log) -------------------------------
CREATE OR REPLACE TABLE `fibre_stg.evenements` AS
SELECT
  id_commande,
  etape,
  TIMESTAMP(horodatage)                     AS horodatage,
  statut,
  acteur
FROM `fibre_raw.evenements`
WHERE id_commande IS NOT NULL
QUALIFY ROW_NUMBER() OVER (                       -- dedoublonnage defensif
  PARTITION BY id_commande, etape, horodatage ORDER BY horodatage) = 1;

-- ---- Interventions techniques ---------------------------------------
CREATE OR REPLACE TABLE `fibre_stg.interventions` AS
SELECT
  id_commande,
  id_intervention,
  TIMESTAMP(date_prevue)                     AS date_prevue,
  TIMESTAMP(date_realisee)                   AS date_realisee,
  sous_traitant,
  resultat,
  NULLIF(motif_echec, '')                    AS motif_echec
FROM `fibre_raw.interventions`;

-- ---- Satisfaction ---------------------------------------------------
CREATE OR REPLACE TABLE `fibre_stg.satisfaction` AS
SELECT
  id_commande,
  DATE(date_enquete)                         AS date_enquete,
  CAST(nps AS INT64)                         AS nps,
  canal_contact,
  CAST(reclamation AS BOOL)                  AS reclamation
FROM `fibre_raw.satisfaction`;
