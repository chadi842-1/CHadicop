-- =====================================================================
-- 04_scoring_features.sql  (GCP BigQuery - Standard SQL)
-- Prepare la table de features pour le modele de scoring (04_scoring_model.py)
-- et illustre une alternative "in-database" avec BigQuery ML.
-- =====================================================================

-- ---- 1) Table de features ------------------------------------------
-- Base d'apprentissage : parcours TERMINES (livres ou en echec),
-- cible = 1 si parcours degrade (echec OU livraison hors delai).
CREATE OR REPLACE TABLE `fibre_mart.scoring_features` AS
SELECT
  id_commande,
  canal, offre, segment, region, gestionnaire_portefeuille,
  zone_a_construire, sous_traitant, debit_gbps, montant_mensuel,
  statut_parcours,
  CASE
    WHEN statut_parcours = 'Echec raccordement' THEN 1
    WHEN statut_parcours = 'Livree' AND livree_dans_delai = 0 THEN 1
    WHEN statut_parcours = 'Livree' AND livree_dans_delai = 1 THEN 0
    ELSE NULL                      -- commandes en cours : a scorer, pas a entrainer
  END AS cible_risque
FROM `fibre_mart.faits_parcours`;

-- ---- 2) (Optionnel) Modele BigQuery ML ------------------------------
-- Entrainement d'une regression logistique directement dans BigQuery.
CREATE OR REPLACE MODEL `fibre_mart.modele_risque_livraison`
OPTIONS(
  model_type        = 'LOGISTIC_REG',
  input_label_cols  = ['cible_risque'],
  auto_class_weights = TRUE
) AS
SELECT
  canal, offre, segment, region, gestionnaire_portefeuille,
  zone_a_construire, sous_traitant, debit_gbps, montant_mensuel,
  cible_risque
FROM `fibre_mart.scoring_features`
WHERE cible_risque IS NOT NULL;

-- ---- 3) Evaluation --------------------------------------------------
-- SELECT * FROM ML.EVALUATE(MODEL `fibre_mart.modele_risque_livraison`);

-- ---- 4) Scoring des commandes EN COURS ------------------------------
CREATE OR REPLACE TABLE `fibre_mart.scoring_commandes_en_cours` AS
SELECT
  f.id_commande, f.canal, f.offre, f.segment, f.region,
  f.gestionnaire_portefeuille, f.sous_traitant, f.zone_a_construire,
  p.predicted_cible_risque_probs[OFFSET(0)].prob AS score_risque,
  CASE
    WHEN p.predicted_cible_risque_probs[OFFSET(0)].prob >= 0.66 THEN 'Eleve'
    WHEN p.predicted_cible_risque_probs[OFFSET(0)].prob >= 0.33 THEN 'Moyen'
    ELSE 'Faible'
  END AS niveau_risque
FROM ML.PREDICT(
       MODEL `fibre_mart.modele_risque_livraison`,
       (SELECT * FROM `fibre_mart.scoring_features`
         WHERE statut_parcours = 'En cours')) p
JOIN `fibre_mart.faits_parcours` f USING (id_commande)
ORDER BY score_risque DESC;
