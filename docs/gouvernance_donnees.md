# Gouvernance & éthique des données

La fiche de poste insiste sur le **respect de la confidentialité des données**.
Ce projet applique les principes suivants.

## 1. Données fictives

- **Aucune donnée réelle ni personnelle n'est utilisée.** Toutes les tables sont
  générées aléatoirement par `fibre360/data_generation/`.
- Les identifiants (`id_client`, `id_commande`) sont synthétiques et ne
  correspondent à personne.

## 2. Principes transposables à un contexte réel

| Principe | Mise en œuvre |
|----------|---------------|
| Minimisation | On ne manipule que les champs utiles à l'analyse du parcours. |
| Pseudonymisation | Les clés clients seraient hachées ; pas de nom/adresse en clair. |
| Finalité | Données utilisées pour le pilotage opérationnel, pas de profilage individuel abusif. |
| Traçabilité | Logs horodatés, rapport de qualité versionné, modèles documentés (model cards). |
| Explicabilité | Modèles explicables (importance des facteurs) → décisions auditables. |
| Accès | En production : habilitations par rôle sur BigQuery (datasets séparés raw/stg/mart). |

## 3. Usage du scoring

- Le score de risque de livraison sert à **prioriser l'action opérationnelle**
  (dossiers à rattraper), pas à pénaliser un client.
- Le score de churn sert à **cibler la rétention** (geste commercial, suivi),
  dans l'intérêt du client comme de l'entreprise.
- Toute décision reste **validée par le métier** (l'IA assiste, ne remplace pas).

## 4. Qualité & fiabilité

- Contrôles qualité systématiques avant analyse (`data_quality_report`).
- Résultats reproductibles (graine aléatoire fixée).
- Les limites des modèles sont documentées (churn difficile à prédire : AUC modérée,
  assumée et communiquée plutôt que survendue).
