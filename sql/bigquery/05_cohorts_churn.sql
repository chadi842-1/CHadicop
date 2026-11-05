-- =====================================================================
-- 05_cohorts_churn.sql  (GCP BigQuery - Standard SQL)
-- Analyse de cohortes / retention et modele de churn BigQuery ML.
-- Equivalent SQL de fibre360/analytics/cohorts.py et fibre360/ml/churn.py.
-- =====================================================================

-- ---- 1) Retention a 12 mois par canal d'acquisition -----------------
CREATE OR REPLACE VIEW `fibre_mart.retention_canal` AS
WITH livrees AS (
  SELECT id_client, canal, dt_mise_en_service, date_resiliation
  FROM `fibre_mart.faits_parcours`
  WHERE statut_parcours = 'Livree'
    AND TIMESTAMP_ADD(dt_mise_en_service, INTERVAL 365 DAY) <= TIMESTAMP '2026-11-01'
)
SELECT canal,
  COUNT(*) AS clients_observables,
  ROUND(AVG(CASE WHEN date_resiliation IS NOT NULL
            AND date_resiliation <= TIMESTAMP_ADD(dt_mise_en_service, INTERVAL 365 DAY)
            THEN 0 ELSE 1 END) * 100, 1) AS retention_12m_pct
FROM livrees
GROUP BY canal
ORDER BY retention_12m_pct DESC;

-- ---- 2) Table de cohortes mensuelles (taux de survie) ---------------
CREATE OR REPLACE VIEW `fibre_mart.cohortes_mensuelles` AS
WITH base AS (
  SELECT FORMAT_DATE('%Y-%m', DATE(dt_mise_en_service)) AS cohorte,
         DATE(dt_mise_en_service) AS dt_mes, date_resiliation
  FROM `fibre_mart.faits_parcours` WHERE statut_parcours = 'Livree'
)
SELECT cohorte, COUNT(*) AS taille,
  ROUND(AVG(IF(date_resiliation IS NULL OR DATE(date_resiliation) >
     DATE_ADD(dt_mes, INTERVAL 3 MONTH), 1, 0)) * 100, 1) AS survie_m3_pct,
  ROUND(AVG(IF(date_resiliation IS NULL OR DATE(date_resiliation) >
     DATE_ADD(dt_mes, INTERVAL 6 MONTH), 1, 0)) * 100, 1) AS survie_m6_pct
FROM base GROUP BY cohorte HAVING taille >= 30 ORDER BY cohorte;

-- ---- 3) Modele de churn BigQuery ML ---------------------------------
CREATE OR REPLACE MODEL `fibre_mart.modele_churn`
OPTIONS(model_type='LOGISTIC_REG', input_label_cols=['churn'],
        auto_class_weights=TRUE) AS
SELECT canal, offre, segment, region, anciennete_client_mois, age,
       delai_livraison_j, nps, nb_reclamations, churn
FROM `fibre_mart.faits_parcours`
WHERE statut_parcours = 'Livree' AND churn IS NOT NULL;

-- Evaluation :  SELECT * FROM ML.EVALUATE(MODEL `fibre_mart.modele_churn`);

-- ---- 4) Clients actifs a plus fort risque de depart -----------------
CREATE OR REPLACE TABLE `fibre_mart.clients_churn_a_risque` AS
SELECT id_client, canal, offre, nps, nb_reclamations,
  p.predicted_churn_probs[OFFSET(0)].prob AS score_churn
FROM ML.PREDICT(MODEL `fibre_mart.modele_churn`,
     (SELECT * FROM `fibre_mart.faits_parcours`
       WHERE statut_parcours='Livree' AND churn = FALSE)) p
ORDER BY score_churn DESC
LIMIT 500;
