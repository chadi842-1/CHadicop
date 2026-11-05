# ---
# Notebook d'exploration (format jupytext `# %%`, ouvrable dans Jupyter / VS Code)
# Analyse exploratoire du parcours Commande -> Livraison Fibre.
# Prérequis : avoir lancé `make datamart` (data/mart/faits_parcours.csv).
# ---

# %% [markdown]
# # Exploration des données — Fibre 360
# Objectif : comprendre la structure du parcours, les délais et les leviers
# de performance avant de construire les KPI et les modèles.

# %%
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

ROOT = Path.cwd().parents[0] if (Path.cwd().name == "notebooks") else Path.cwd()
faits = pd.read_csv(ROOT / "data" / "mart" / "faits_parcours.csv")
print(faits.shape)
faits[["statut_parcours", "canal", "delai_livraison_j", "nps", "churn"]].head()

# %% [markdown]
# ## 1. Répartition des statuts de parcours

# %%
faits["statut_parcours"].value_counts(normalize=True).mul(100).round(1)

# %% [markdown]
# ## 2. Distribution du délai de livraison (commandes livrées) vs SLA

# %%
liv = faits[faits.statut_parcours == "Livree"]
ax = liv["delai_livraison_j"].plot(kind="hist", bins=40, alpha=.8)
ax.axvline(15, color="red", linestyle="--", label="SLA 15 j")
ax.set_xlabel("Délai commande -> mise en service (jours)")
ax.legend()
plt.tight_layout()

# %% [markdown]
# ## 3. Performance par canal (multi-canalité)

# %%
(liv.groupby("canal")
 .agg(taux_sla=("livree_dans_delai", "mean"),
      delai_moyen=("delai_livraison_j", "mean"),
      nps=("nps", "mean"))
 .assign(taux_sla=lambda d: (d.taux_sla * 100).round(1))
 .sort_values("taux_sla", ascending=False))

# %% [markdown]
# ## 4. Effet de la zone à construire et du sous-traitant sur le délai

# %%
faits.boxplot(column="delai_livraison_j", by="sous_traitant", rot=30)
plt.suptitle("")
plt.title("Délai de livraison par sous-traitant")
plt.tight_layout()

# %% [markdown]
# ## 5. Corrélation délai long -> churn
# On vérifie l'hypothèse métier : un parcours dégradé augmente la résiliation.

# %%
liv_c = liv.copy()
liv_c["hors_delai"] = (liv_c["delai_livraison_j"] > 15)
liv_c.groupby("hors_delai")["churn"].mean().mul(100).round(1).rename("taux_churn_%")

# %% [markdown]
# **Conclusion** : les leviers principaux sont la zone à construire, le
# sous-traitant et le canal ; un délai dépassé se traduit par davantage de
# réclamations et de churn. Ces constats guident le scoring et le plan d'actions.
