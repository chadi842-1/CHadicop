-- =====================================================================
-- 02_datamart_parcours.sql  (GCP BigQuery - Standard SQL)
-- Croise les 8 sources et construit la table de faits du parcours
-- (1 ligne = 1 commande enrichie). Equivalent SQL de fibre360/pipeline/datamart.py.
-- Resultat materialise dans `fibre_mart.faits_parcours`
-- (partitionne par mois de commande, clustere par canal / statut).
-- =====================================================================

CREATE OR REPLACE TABLE `fibre_mart.faits_parcours`
PARTITION BY DATE_TRUNC(date_commande, MONTH)
CLUSTER BY canal, statut_parcours AS
WITH
jalons AS (
  SELECT id_commande,
    MIN(IF(etape='Commande enregistree', horodatage, NULL)) AS dt_commande,
    MIN(IF(etape='Mise en service',      horodatage, NULL)) AS dt_mise_en_service,
    MIN(IF(etape='Echec raccordement',   horodatage, NULL)) AS dt_echec,
    MIN(IF(etape='Annulation client',    horodatage, NULL)) AS dt_annulation
  FROM `fibre_stg.evenements` GROUP BY id_commande
),
interv AS (
  SELECT id_commande, COUNT(*) AS nb_interventions,
    ARRAY_AGG(resultat   ORDER BY date_realisee DESC)[OFFSET(0)] AS resultat_intervention,
    ARRAY_AGG(motif_echec ORDER BY date_realisee DESC)[OFFSET(0)] AS motif_echec
  FROM `fibre_stg.interventions` GROUP BY id_commande
),
satis AS (SELECT id_commande, AVG(nps) AS nps FROM `fibre_stg.satisfaction` GROUP BY id_commande),
reclam AS (
  SELECT id_commande, COUNT(*) AS nb_reclamations,
    LOGICAL_OR(resolu) AS reclamation_resolue, AVG(delai_resolution_j) AS delai_resolution_j
  FROM `fibre_stg.reclamations` GROUP BY id_commande
),
ca AS (SELECT id_commande, SUM(montant) AS ca_facture FROM `fibre_stg.factures` GROUP BY id_commande)
SELECT
  c.*,
  j.dt_commande, j.dt_mise_en_service, j.dt_echec, j.dt_annulation,
  CASE
    WHEN j.dt_mise_en_service IS NOT NULL THEN 'Livree'
    WHEN j.dt_echec           IS NOT NULL THEN 'Echec raccordement'
    WHEN j.dt_annulation      IS NOT NULL THEN 'Annulee'
    ELSE 'En cours' END AS statut_parcours,
  ROUND(TIMESTAMP_DIFF(j.dt_mise_en_service, j.dt_commande, HOUR)/24, 2) AS delai_livraison_j,
  CASE WHEN j.dt_mise_en_service IS NULL THEN NULL
       WHEN TIMESTAMP_DIFF(j.dt_mise_en_service, j.dt_commande, HOUR)/24 <= 15 THEN 1
       ELSE 0 END AS livree_dans_delai,
  i.nb_interventions, i.resultat_intervention, i.motif_echec,
  s.nps,
  COALESCE(r.nb_reclamations, 0) AS nb_reclamations,
  (COALESCE(r.nb_reclamations, 0) > 0) AS reclamation,
  r.reclamation_resolue, r.delai_resolution_j,
  ca.ca_facture,
  t.taux_reussite_ref, t.anciennete_mois AS anciennete_technicien_mois,
  cl.churn, cl.date_resiliation, cl.age, cl.csp,
  FORMAT_DATE('%Y-%m', c.date_commande) AS annee_mois,
  DATE_DIFF(DATE '2026-11-01', c.date_commande, DAY) AS age_jours,
  (j.dt_mise_en_service IS NULL AND j.dt_echec IS NULL AND j.dt_annulation IS NULL
     AND DATE_DIFF(DATE '2026-11-01', c.date_commande, DAY) > 15) AS alerte_sla
FROM `fibre_stg.commandes` c
LEFT JOIN jalons  j  USING (id_commande)
LEFT JOIN interv  i  USING (id_commande)
LEFT JOIN satis   s  USING (id_commande)
LEFT JOIN reclam  r  USING (id_commande)
LEFT JOIN ca         USING (id_commande)
LEFT JOIN `fibre_stg.techniciens` t USING (id_technicien)
LEFT JOIN `fibre_stg.clients` cl     USING (id_client);
