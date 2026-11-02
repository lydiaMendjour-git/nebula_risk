"""Recommandations d'actions automatiques selon le profil du client.
Chaque règle est simple et modifiable : condition → action proposée."""
from __future__ import annotations

import pandas as pd

PRIORITES = {"Urgent": "#EF4444", "Important": "#F59E0B", "À prévoir": "#A855F7", "Routine": "#22C55E"}


def recommandations(c: pd.Series) -> list[dict]:
    r = []

    def ajoute(icone, titre, detail, priorite):
        r.append({"icone": icone, "titre": titre, "detail": detail, "priorite": priorite})

    if c["score"] >= 65 and c["ratio_endettement_pct"] >= 60:
        ajoute("🧩", "Restructuration de la dette",
               f"Dette égale à {c['ratio_endettement_pct']:.0f} % du CA : étudier un rééchelonnement ou une consolidation "
               "avec la banque, voire une procédure de conciliation.", "Urgent")
    if c["nb_retards_12m"] >= 4 or c["retard_moyen_jours"] >= 30:
        ajoute("📅", "Plan d'apurement",
               f"{int(c['nb_retards_12m'])} retards en 12 mois (moyenne {c['retard_moyen_jours']:.0f} jours) : proposer un "
               "échéancier écrit pour régulariser les sommes dues.", "Urgent" if c["score"] >= 45 else "Important")
    elif c["nb_retards_12m"] >= 1:
        ajoute("✉️", "Relance amiable",
               "Quelques retards récents : relance courtoise et rappel des échéances à venir.", "À prévoir")
    if c["incidents_bancaires_12m"] >= 2 or c["utilisation_decouvert_pct"] >= 80:
        ajoute("🔍", "Surveillance renforcée",
               f"{int(c['incidents_bancaires_12m'])} incident(s) bancaire(s) et découvert utilisé à "
               f"{c['utilisation_decouvert_pct']:.0f} % : suivi mensuel des relevés.", "Important")
    if c["tresorerie_jours"] < 15:
        ajoute("💧", "Prévisionnel de trésorerie",
               f"Seulement {c['tresorerie_jours']:.0f} jours de trésorerie : bâtir un plan de trésorerie sur 13 semaines.",
               "Urgent" if c["tresorerie_jours"] < 0 else "Important")
    if c["evolution_ca_pct"] <= -15:
        ajoute("📉", "Point sur l'activité",
               f"CA en baisse de {abs(c['evolution_ca_pct']):.0f} % : entretien avec le dirigeant sur les causes et le plan de relance.",
               "Important")
    if c["marge_ebe_pct"] < 0:
        ajoute("✂️", "Analyse des coûts",
               "L'activité perd de l'argent (EBE négatif) : revoir les charges et les prix de vente.", "Important")
    if pd.notna(c.get("variation_30j")) and c["variation_30j"] >= 8:
        ajoute("⚡", "Entretien sous 15 jours",
               f"Le score a pris {c['variation_30j']:+.0f} points en un mois : dégradation rapide à comprendre.", "Urgent")
    if not r:
        ajoute("✅", "Suivi standard", "Profil sain : revue trimestrielle habituelle.", "Routine")

    ordre = list(PRIORITES)
    return sorted(r, key=lambda x: ordre.index(x["priorite"]))
