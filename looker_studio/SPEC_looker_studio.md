# Spécification du tableau de bord Looker Studio (ex-Google Data Studio)

Tableau de bord de partage léger, destiné aux équipes métier, connecté
**directement à BigQuery** (`fibre_mart`) — complémentaire du rapport Power BI
plus analytique.

## 1. Connexion des données

- Connecteur : **BigQuery** → projet GCP → dataset `fibre_mart`.
- Sources :
  - `kpi_synthese` (scorecards)
  - `kpi_par_canal`, `kpi_mensuel` (graphiques)
  - `faits_parcours` (table détaillée + filtres)
  - `scoring_commandes_en_cours` (table d'action)
- Alternative sans GCP : importer les CSV `data/exports/kpi_*.csv` via
  « Google Sheets » puis connecter Looker Studio aux feuilles.

## 2. Champs calculés (Looker Studio)

```
Taux SLA %        =  SUM(nb_livrees_ok) / SUM(nb_livrees)        -- format %
Statut couleur    =  CASE
                       WHEN taux_livraison_delai_pct < 60 THEN "Rouge"
                       WHEN taux_livraison_delai_pct < 75 THEN "Orange"
                       ELSE "Vert" END
Respect SLA       =  IF(delai_livraison_j <= 15, "Dans les délais", "Hors délai")
```

## 3. Structure (1 page, format 16:9)

1. **Bandeau scorecards** (source `kpi_synthese`) : taux de livraison dans les
   délais, délai moyen, taux d'échec, alertes SLA.
2. **Série temporelle** (`kpi_mensuel`) : taux SLA et délai moyen par mois.
3. **Barres** (`kpi_par_canal`) : taux de livraison dans les délais par canal.
4. **Camembert** : répartition `statut_parcours`.
5. **Tableau filtrable** (`scoring_commandes_en_cours`) : commandes en cours
   triées par `score_risque`, contrôle de filtre `niveau_risque`.

## 4. Contrôles de filtre

Plage de dates (`date_commande`), `canal`, `region`, `offre`, `segment`.

## 5. Diffusion

- Partage par lien restreint + planification d'un **envoi PDF hebdomadaire**
  par e-mail (rejoint le flux Power Automate, cf. `power_automate/`).
- Actualisation des données : cache BigQuery 12 h (ajustable).
