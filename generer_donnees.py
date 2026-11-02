"""
Génère des données 100 % FICTIVES et réalistes pour la plateforme.

    py generer_donnees.py

Crée trois fichiers dans le dossier data/ :
  - clients.csv            : 1 200 entreprises clientes, situation actuelle + cible "defaut" (0/1)
  - historique_mensuel.csv : la situation de chaque client sur les 12 derniers mois
  - paiements.csv          : l'historique des échéances (à l'heure, en retard, impayé, incident)

Principe : chaque client a un "niveau de fragilité caché" qui évolue dans le temps.
Les chiffres observables (retards, trésorerie, dette...) en découlent, avec du bruit,
comme dans la réalité. Le modèle de machine learning devra retrouver le risque
uniquement à partir des chiffres observables.
"""
from pathlib import Path

import numpy as np
import pandas as pd

GRAINE = 42          # change ce nombre pour obtenir un autre jeu de données
NB_CLIENTS = 1200
NB_MOIS = 12         # mois d'historique conservés
DERNIER_MOIS = "2026-10-01"

SECTEURS = {
    # nom : (CA médian en €, sur-risque du secteur, préfixes de noms)
    "BTP": (850_000, 0.35, ["Bâtiments", "Maçonnerie", "Charpentes", "Rénovation", "Toitures"]),
    "Commerce": (620_000, 0.15, ["Boutique", "Épicerie", "Comptoir", "Maison", "Bazar"]),
    "Restauration": (420_000, 0.55, ["Brasserie", "Restaurant", "Bistrot", "Boulangerie", "Traiteur"]),
    "Transport": (1_100_000, 0.30, ["Transports", "Logistique", "Express", "Fret", "Ambulances"]),
    "Industrie": (2_400_000, 0.05, ["Ateliers", "Mécanique", "Usinage", "Plasturgie", "Métallerie"]),
    "Services": (380_000, -0.15, ["Conseil", "Agence", "Studio", "Solutions", "Services"]),
    "Santé": (650_000, -0.40, ["Pharmacie", "Cabinet", "Laboratoire", "Clinique vétérinaire", "Optique"]),
    "Agriculture": (520_000, 0.10, ["EARL", "GAEC", "Domaine", "Ferme", "Vergers"]),
}
REGIONS = [
    "Île-de-France", "Auvergne-Rhône-Alpes", "Nouvelle-Aquitaine", "Occitanie", "Hauts-de-France",
    "Grand Est", "Provence-Alpes-Côte d'Azur", "Pays de la Loire", "Bretagne", "Normandie",
    "Bourgogne-Franche-Comté", "Centre-Val de Loire", "Corse",
]
POIDS_REGIONS = np.array([18, 12, 9, 9, 8, 8, 8, 6, 5, 5, 4, 4, 1], dtype=float)
NOMS = [
    "Martin", "Bernard", "Thomas", "Petit", "Robert", "Richard", "Durand", "Dubois", "Moreau", "Laurent",
    "Simon", "Michel", "Lefèvre", "Leroy", "Roux", "David", "Bertrand", "Morel", "Fournier", "Girard",
    "Bonnet", "Dupont", "Lambert", "Fontaine", "Rousseau", "Vincent", "Muller", "Lefebvre", "Faure", "André",
    "Mercier", "Blanc", "Guérin", "Boyer", "Garnier", "Chevalier", "François", "Legrand", "Gauthier", "Garcia",
    "Perrin", "Robin", "Clément", "Morin", "Nicolas", "Henry", "Roussel", "Mathieu", "Gautier", "Masson",
    "Marchand", "Duval", "Denis", "Dumont", "Marie", "Lemaire", "Noël", "Meyer", "Dufour", "Meunier",
    "Brun", "Blanchard", "Giraud", "Joly", "Rivière", "Lucas", "Brunet", "Gaillard", "Barbier", "Arnaud",
]
FORMES = ["SARL", "SAS", "SASU", "EURL", "SA"]


def _sigmoide(x):
    return 1 / (1 + np.exp(-x))


def generer(dossier: Path | str = Path(__file__).resolve().parent / "data", graine: int = GRAINE) -> None:
    rng = np.random.default_rng(graine)
    dossier = Path(dossier)
    dossier.mkdir(parents=True, exist_ok=True)
    n, H = NB_CLIENTS, 24  # on simule 24 mois pour calculer des cumuls "sur 12 mois" dès le 1er mois affiché

    # ---------- Identité ----------
    noms_secteurs = list(SECTEURS)
    secteur = rng.choice(noms_secteurs, n, p=[.17, .17, .14, .09, .10, .18, .08, .07])
    region = rng.choice(REGIONS, n, p=POIDS_REGIONS / POIDS_REGIONS.sum())
    anciennete = np.round(1 + rng.exponential(9, n), 1).clip(0.5, 60)
    noms = []
    for i in range(n):
        prefixe = rng.choice(SECTEURS[secteur[i]][2])
        noms.append(f"{prefixe} {rng.choice(NOMS)} {rng.choice(FORMES)}")
    # Rendre les noms uniques
    vus = {}
    for i, nom in enumerate(noms):
        if nom in vus:
            vus[nom] += 1
            noms[i] = f"{nom} {vus[nom]}"
        else:
            vus[nom] = 1

    # ---------- Fragilité cachée qui évolue dans le temps ----------
    sur_risque = np.array([SECTEURS[s][1] for s in secteur])
    base = rng.normal(0, 1, n) + sur_risque - 0.30 * (np.log1p(anciennete) - 2.2)
    tendance = rng.normal(0, 0.35, n)
    chute = rng.random(n) < 0.12                  # 12 % des clients se dégradent nettement
    tendance[chute] += rng.uniform(0.8, 2.0, chute.sum())
    reprise = rng.random(n) < 0.08                # 8 % se redressent
    tendance[reprise] -= rng.uniform(0.5, 1.2, reprise.sum())
    t = (np.arange(H) - (H - 1)) / 12             # de -1,9 an à 0 (aujourd'hui)
    bruit = np.cumsum(rng.normal(0, 0.12, (n, H)), axis=1)
    fragilite = base[:, None] + tendance[:, None] * (t[None, :] + 0.5) + bruit - bruit[:, [-1]] * 0.5

    # ---------- Événements mensuels ----------
    retard = rng.random((n, H)) < _sigmoide(-2.4 + 1.25 * fragilite)
    jours = np.where(retard, np.round(5 + rng.gamma(2, 5 + 6 * np.clip(fragilite, 0, None))), 0)
    incident = rng.random((n, H)) < _sigmoide(-4.3 + 1.35 * fragilite)

    # ---------- Données financières ----------
    ca_median = np.array([SECTEURS[s][0] for s in secteur])
    ca_base = ca_median * np.exp(rng.normal(0, 0.7, n))
    evo_base = rng.normal(3, 6, n)
    marge_base = rng.normal(9, 5, n)
    dette_base = ca_base * np.exp(rng.normal(np.log(0.35), 0.5, n) + 0.22 * base)
    salaries = np.maximum(1, np.round(ca_base / rng.uniform(70_000, 160_000, n))).astype(int)

    lignes_hist, lignes_paie = [], []
    mois = pd.date_range(end=DERNIER_MOIS, periods=NB_MOIS, freq="MS")
    for k, m in enumerate(mois):
        h = H - NB_MOIS + k                      # indice dans la simulation
        f = fragilite[:, h]
        fen = slice(h - 11, h + 1)
        nb_ret = retard[:, fen].sum(axis=1)
        ret_moy = np.where(nb_ret > 0, jours[:, fen].sum(axis=1) / np.maximum(nb_ret, 1), 0)
        evo = np.clip(evo_base - 6.5 * (f - base) - 2.0 * f + rng.normal(0, 2, n), -60, 60)
        ca = ca_base * (1 + evo / 100 * (k - NB_MOIS + 1) / 12)
        dette = dette_base * (1 + 0.06 * (f - base)).clip(0.5, None)
        lignes_hist.append(pd.DataFrame({
            "id_client": [f"CL-{i + 1:04d}" for i in range(n)],
            "mois": m.strftime("%Y-%m-%d"),
            "ca_annuel": ca.round(0),
            "evolution_ca_pct": evo.round(1),
            "marge_ebe_pct": np.clip(marge_base - 3.2 * f + rng.normal(0, 1.5, n), -35, 45).round(1),
            "encours": dette.round(0),
            "ratio_endettement_pct": (dette / ca * 100).round(1),
            "tresorerie_jours": np.clip(42 - 13 * f + rng.normal(0, 7, n), -30, 200).round(0),
            "utilisation_decouvert_pct": (100 * _sigmoide(-0.9 + 1.1 * f + rng.normal(0, 0.35, n))).round(1),
            "nb_retards_12m": nb_ret,
            "retard_moyen_jours": ret_moy.round(1),
            "incidents_bancaires_12m": incident[:, fen].sum(axis=1),
            "anciennete_ans": (anciennete - (NB_MOIS - 1 - k) / 12).clip(0.1).round(1),
            "nb_salaries": salaries,
        }))
        echeance = (dette / 60).round(0)
        statut = np.where(~retard[:, h], "À l'heure", np.where(jours[:, h] > 60, "Impayé", "En retard"))
        lignes_paie.append(pd.DataFrame({
            "id_client": [f"CL-{i + 1:04d}" for i in range(n)],
            "mois": m.strftime("%Y-%m-%d"),
            "montant_echeance": echeance,
            "jours_retard": jours[:, h].astype(int),
            "statut": statut,
            "incident_bancaire": incident[:, h].astype(int),
        }))

    historique = pd.concat(lignes_hist, ignore_index=True)
    paiements = pd.concat(lignes_paie, ignore_index=True)

    # ---------- Situation actuelle + cible "défaut dans les 12 mois" ----------
    actuel = historique[historique["mois"] == historique["mois"].max()].reset_index(drop=True)
    z = lambda c: (actuel[c] - actuel[c].mean()) / actuel[c].std()
    logit = (1.05 * fragilite[:, -1] + 0.45 * tendance + 0.35 * z("ratio_endettement_pct").clip(-2, 3)
             + 0.25 * (actuel["incidents_bancaires_12m"] >= 2) + rng.normal(0, 0.55, n))
    # Ajuste la constante pour viser environ 11 % de défauts
    bas, haut = -10.0, 5.0
    for _ in range(60):
        c = (bas + haut) / 2
        if _sigmoide(c + logit).mean() > 0.11:
            haut = c
        else:
            bas = c
    defaut = (rng.random(n) < _sigmoide(c + logit)).astype(int)

    clients = pd.DataFrame({
        "id_client": actuel["id_client"],
        "nom": noms,
        "secteur": secteur,
        "region": region,
    }).join(actuel.drop(columns=["id_client", "mois"]))
    clients["defaut"] = defaut

    clients.to_csv(dossier / "clients.csv", index=False, encoding="utf-8")
    historique.merge(clients[["id_client", "secteur", "region"]], on="id_client").to_csv(
        dossier / "historique_mensuel.csv", index=False, encoding="utf-8")
    paiements.to_csv(dossier / "paiements.csv", index=False, encoding="utf-8")
    print(f"{n} clients fictifs générés dans {dossier} (taux de défaut : {defaut.mean():.1%})")


if __name__ == "__main__":
    generer()
