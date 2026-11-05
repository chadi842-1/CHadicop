-- =====================================================================
-- 02_datamart_parcours.sql  (GCP BigQuery - Standard SQL)
-- Croise les 4 sources et construit la table de faits du parcours
-- (1 ligne = 1 commande enrichie). Equivalent SQL de 02_build_datamart.py.
-- Resultat materialise dans `fibre_mart.faits_parcours`.
-- =====================================================================

CREATE OR REPLACE TABLE `fibre_mart.faits_parcours` AS
WITH
-- Jalons cles extraits du journal d'evenements (pivot par etape)
jalons AS (
  SELECT
    id_commande,
    MIN(IF(etape = 'Commande enregistree', horodatage, NULL)) AS dt_commande,
    MIN(IF(etape = 'Mise en service',      horodatage, NULL)) AS dt_mise_en_service,
    MIN(IF(etape = 'Echec raccordement',   horodatage, NULL)) AS dt_echec,
    MIN(IF(etape = 'Annulation client',    horodatage, NULL)) AS dt_annulation
  FROM `fibre_stg.evenements`
  GROUP BY id_commande
),
-- Dernier resultat d'intervention + nombre d'interventions
interv AS (
  SELECT
    id_commande,
    COUNT(*)                                             AS nb_interventions,
    ARRAY_AGG(resultat   ORDER BY date_realisee DESC)[OFFSET(0)] AS resultat_intervention,
    ARRAY_AGG(motif_echec ORDER BY date_realisee DESC)[OFFSET(0)] AS motif_echec
  FROM `fibre_stg.interventions`
  GROUP BY id_commande
),
-- Satisfaction agregee
satis AS (
  SELECT id_commande, AVG(nps) AS nps, MAX(reclamation) AS reclamation
  FROM `fibre_stg.satisfaction`
  GROUP BY id_commande
)
SELECT
  c.*,
  j.dt_commande,
  j.dt_mise_en_service,
  j.dt_echec,
  j.dt_annulation,
  -- Statut final du parcours
  CASE
    WHEN j.dt_mise_en_service IS NOT NULL THEN 'Livree'
    WHEN j.dt_echec           IS NOT NULL THEN 'Echec raccordement'
    WHEN j.dt_annulation      IS NOT NULL THEN 'Annulee'
    ELSE 'En cours'
  END AS statut_parcours,
  -- Delai de livraison (jours)
  ROUND(TIMESTAMP_DIFF(j.dt_mise_en_service, j.dt_commande, HOUR) / 24, 2)
    AS delai_livraison_j,
  -- Respect du SLA (15 jours) parmi les livrees
  CASE
    WHEN j.dt_mise_en_service IS NULL THEN NULL
    WHEN TIMESTAMP_DIFF(j.dt_mise_en_service, j.dt_commande, HOUR) / 24 <= 15
      THEN 1 ELSE 0
  END AS livree_dans_delai,
  i.nb_interventions,
  i.resultat_intervention,
  i.motif_echec,
  s.nps,
  s.reclamation,
  FORMAT_DATE('%Y-%m', c.date_commande)               AS annee_mois,
  -- Age de la commande et alerte SLA pour les commandes en cours
  DATE_DIFF(DATE '2026-11-01', c.date_commande, DAY)  AS age_jours,
  (j.dt_mise_en_service IS NULL AND j.dt_echec IS NULL
     AND j.dt_annulation IS NULL
     AND DATE_DIFF(DATE '2026-11-01', c.date_commande, DAY) > 15) AS alerte_sla
FROM `fibre_stg.commandes` c
LEFT JOIN jalons  j USING (id_commande)
LEFT JOIN interv  i USING (id_commande)
LEFT JOIN satis   s USING (id_commande);
