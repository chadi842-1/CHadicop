# Automatisation Power Automate — Alertes SLA & reporting hebdomadaire

La fiche de poste mentionne **Power Automate / process mining** et
l'amélioration des outils pour les utilisateurs. Deux flux sont spécifiés
ci-dessous (automatisation du suivi, sans intervention manuelle).

---

## Flux 1 — Alerte quotidienne « Commandes à risque » (déclencheur planifié)

**Objectif** : chaque matin, remonter aux gestionnaires les commandes en cours
à risque élevé et les alertes SLA, pour traitement prioritaire.

| Étape | Connecteur / action | Détail |
|-------|--------------------|--------|
| 1. Déclencheur | **Recurrence** | Tous les jours à 7 h 30 |
| 2. Source | **Google BigQuery – Execute query** (ou lecture du CSV `scoring_commandes_en_cours.csv` sur SharePoint) | `SELECT * FROM fibre_mart.scoring_commandes_en_cours WHERE niveau_risque = 'Eleve'` |
| 3. Condition | **Condition** | `length(outputs) > 0` |
| 4a. Si vrai | **Create HTML table** puis **Send an email (V2)** | Mail au gestionnaire concerné (routage via `gestionnaire_portefeuille`) |
| 4b. | **Post message (Teams)** | Message dans le canal « Pilotage Fibre » |
| 5. Journal | **Add row (Excel/Dataverse)** | Trace des alertes envoyées (audit) |

**Pseudo-logique**
```
Recurrence (quotidien 07:30)
  -> BigQuery : commandes niveau_risque = 'Eleve'
  -> Apply to each gestionnaire
       -> Filtrer les commandes du gestionnaire
       -> Si > 0 : e-mail récapitulatif + message Teams
  -> Enregistrer le compte d'alertes dans le journal
```

---

## Flux 2 — Reporting hebdomadaire automatique (déclencheur planifié)

**Objectif** : diffuser chaque lundi la synthèse de la semaine à la Direction.

| Étape | Connecteur / action | Détail |
|-------|--------------------|--------|
| 1. Déclencheur | **Recurrence** | Lundi 8 h 00 |
| 2. Rafraîchir | **Power BI – Refresh a dataset** | Jeu « Fibre 360 » |
| 3. Export | **Power BI – Export to File for Paginated Reports** (PDF) | Rapport « Vue Direction » |
| 4. Stockage | **OneDrive / SharePoint – Create file** | Archivage du PDF daté |
| 5. Diffusion | **Send an email (V2)** | PDF en pièce jointe à la liste Direction |
| 6. (option IA) | **Appel HTTP** vers `ai_agent/agent_insights.py` (exposé en API) | Joindre la note d'analyse rédigée automatiquement |

---

## Lien avec le process mining

Les transitions et goulots identifiés (`data/exports/pm_goulots.csv`) servent à
**paramétrer les seuils d'alerte** : par exemple, déclencher une alerte dès
qu'une commande dépasse la durée moyenne observée sur la transition
« Prise de RDV → Construction ligne ». L'automatisation remplace le suivi
manuel d'Excel par un dispositif proactif.
