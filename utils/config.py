"""Réglages généraux : nom de la plateforme, couleurs, seuils de risque, libellés des variables.
Tu peux modifier ce fichier sans risque : tout le reste de l'application lit ces valeurs."""
from pathlib import Path

# ---------- Nom affiché ----------
NOM_APP = "NEBULA"
SOUS_NOM = "Risk Intelligence"

# ---------- Dossiers ----------
RACINE = Path(__file__).resolve().parent.parent
DOSSIER_DATA = RACINE / "data"
DOSSIER_MODELES = RACINE / "models"
FICHIER_CLIENTS = DOSSIER_DATA / "clients.csv"
FICHIER_HISTORIQUE = DOSSIER_DATA / "historique_mensuel.csv"
FICHIER_PAIEMENTS = DOSSIER_DATA / "paiements.csv"
FICHIER_MODELE = DOSSIER_MODELES / "meilleur_modele.joblib"
FICHIER_CSS = RACINE / "assets" / "style.css"

# ---------- Couleurs ----------
VIOLET = "#A855F7"
VIOLET_FONCE = "#7C3AED"
INDIGO = "#6366F1"
MAGENTA = "#EC4899"
LAVANDE = "#C4B5FD"
TEXTE = "#E9E6F5"
GRIS = "#9A93B5"
FOND = "#0B0B12"
PALETTE = [VIOLET, INDIGO, MAGENTA, VIOLET_FONCE, LAVANDE, "#F0ABFC", "#818CF8", "#F472B6"]

# ---------- Niveaux de risque (score de 0 à 100) ----------
# Un client est "Faible" si score < 25, "Modéré" si < 45, "Élevé" si < 65, sinon "Critique".
NIVEAUX = ["Faible", "Modéré", "Élevé", "Critique"]
SEUILS_SCORE = [25, 45, 65]
COULEURS_NIVEAU = {"Faible": "#22C55E", "Modéré": "#F59E0B", "Élevé": "#EF4444", "Critique": "#C026D3"}
PASTILLES = {"Faible": "🟢 Faible", "Modéré": "🟠 Modéré", "Élevé": "🔴 Élevé", "Critique": "🟣 Critique"}

# ---------- Variables utilisées par le modèle ----------
VARIABLES_NUM = [
    "ca_annuel", "evolution_ca_pct", "marge_ebe_pct", "encours", "ratio_endettement_pct",
    "tresorerie_jours", "utilisation_decouvert_pct", "nb_retards_12m", "retard_moyen_jours",
    "incidents_bancaires_12m", "anciennete_ans", "nb_salaries",
]
VARIABLES_CAT = ["secteur"]
VARIABLES = VARIABLES_NUM + VARIABLES_CAT

LIBELLES = {
    "ca_annuel": "Chiffre d'affaires annuel",
    "evolution_ca_pct": "Évolution du CA (%)",
    "marge_ebe_pct": "Marge EBE (%)",
    "encours": "Encours de dette",
    "ratio_endettement_pct": "Ratio d'endettement (%)",
    "tresorerie_jours": "Trésorerie (jours de CA)",
    "utilisation_decouvert_pct": "Utilisation du découvert (%)",
    "nb_retards_12m": "Retards de paiement (12 mois)",
    "retard_moyen_jours": "Retard moyen (jours)",
    "incidents_bancaires_12m": "Incidents bancaires (12 mois)",
    "anciennete_ans": "Ancienneté (ans)",
    "nb_salaries": "Nombre de salariés",
    "secteur": "Secteur d'activité",
    "score": "Score de risque",
}

# Texte d'aide affiché au survol des variables (pour les débutants)
AIDE = {
    "ratio_endettement_pct": "Dette totale divisée par le chiffre d'affaires. 80 % = la dette représente 80 % d'une année de ventes.",
    "tresorerie_jours": "Combien de jours l'entreprise peut tenir avec sa trésorerie, au rythme de ses ventes.",
    "utilisation_decouvert_pct": "Part du découvert autorisé qui est utilisée en moyenne.",
    "marge_ebe_pct": "Excédent brut d'exploitation divisé par le CA : ce que l'activité rapporte avant amortissements et intérêts.",
}
