-- =====================================================================
-- 03_kpis.sql  (GCP BigQuery - Standard SQL)
-- Vues d'indicateurs servant de source aux tableaux de bord
-- Power BI / Looker Studio. Equivalent SQL de 05_kpi_export.py.
-- =====================================================================

-- ---- KPI multi-dimension (macro par parametre de dimension) ---------
-- Exemple : KPI par canal. Dupliquer en changeant la colonne de GROUP BY
-- (offre, region, gestionnaire_portefeuille, sous_traitant, annee_mois).

CREATE OR REPLACE VIEW `fibre_mart.kpi_par_canal` AS
SELECT
  canal,
  COUNT(*)                                               AS nb_commandes,
  COUNTIF(statut_parcours = 'Livree')                    AS nb_livrees,
  ROUND(AVG(IF(statut_parcours = 'Livree', delai_livraison_j, NULL)), 1)
                                                         AS delai_moyen_j,
  ROUND(AVG(IF(statut_parcours = 'Livree',
              CAST(livree_dans_delai AS FLOAT64), NULL)) * 100, 1)
                                                         AS taux_livraison_delai_pct,
  ROUND(COUNTIF(statut_parcours = 'Echec raccordement') / COUNT(*) * 100, 1)
                                                         AS taux_echec_pct,
  ROUND(COUNTIF(statut_parcours = 'Annulee') / COUNT(*) * 100, 1)
                                                         AS taux_annulation_pct,
  ROUND(AVG(IF(statut_parcours = 'Livree', nps, NULL)))  AS nps_moyen,
  ROUND(AVG(IF(statut_parcours = 'Livree',
              CAST(reclamation AS FLOAT64), NULL)) * 100, 1)
                                                         AS taux_reclamation_pct
FROM `fibre_mart.faits_parcours`
GROUP BY canal
ORDER BY nb_commandes DESC;

-- ---- Synthese globale (carte de score Direction) --------------------
CREATE OR REPLACE VIEW `fibre_mart.kpi_synthese` AS
SELECT
  COUNT(*)                                               AS commandes_totales,
  COUNTIF(statut_parcours = 'Livree')                    AS commandes_livrees,
  COUNTIF(statut_parcours = 'En cours')                  AS commandes_en_cours,
  ROUND(AVG(IF(statut_parcours = 'Livree',
              CAST(livree_dans_delai AS FLOAT64), NULL)) * 100, 1)
                                                         AS taux_livraison_delai_pct,
  ROUND(AVG(IF(statut_parcours = 'Livree', delai_livraison_j, NULL)), 1)
                                                         AS delai_moyen_j,
  ROUND(COUNTIF(statut_parcours = 'Echec raccordement') / COUNT(*) * 100, 1)
                                                         AS taux_echec_pct,
  COUNTIF(alerte_sla)                                    AS alertes_sla_en_cours
FROM `fibre_mart.faits_parcours`;

-- ---- Serie mensuelle (tendance) -------------------------------------
CREATE OR REPLACE VIEW `fibre_mart.kpi_mensuel` AS
SELECT
  annee_mois,
  COUNT(*)                                               AS nb_commandes,
  ROUND(AVG(IF(statut_parcours = 'Livree',
              CAST(livree_dans_delai AS FLOAT64), NULL)) * 100, 1)
                                                         AS taux_livraison_delai_pct,
  ROUND(AVG(IF(statut_parcours = 'Livree', delai_livraison_j, NULL)), 1)
                                                         AS delai_moyen_j
FROM `fibre_mart.faits_parcours`
GROUP BY annee_mois
ORDER BY annee_mois;
