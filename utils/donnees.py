"""Chargement des données et calculs partagés par toutes les pages (mis en cache)."""
from __future__ import annotations

import numpy as np
import pandas as pd
import streamlit as st

from utils import modele as m
from utils.config import (FICHIER_CLIENTS, FICHIER_HISTORIQUE, FICHIER_PAIEMENTS, DOSSIER_DATA,
                          NIVEAUX, VARIABLES)


@st.cache_data(show_spinner="Chargement des données fictives…")
def donnees_brutes() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Lit les 3 CSV. S'ils n'existent pas encore, les génère automatiquement."""
    if not (FICHIER_CLIENTS.exists() and FICHIER_HISTORIQUE.exists() and FICHIER_PAIEMENTS.exists()):
        from generer_donnees import generer
        generer(DOSSIER_DATA)
    clients = pd.read_csv(FICHIER_CLIENTS)
    hist = pd.read_csv(FICHIER_HISTORIQUE, parse_dates=["mois"])
    paie = pd.read_csv(FICHIER_PAIEMENTS, parse_dates=["mois"])
    return clients, hist, paie


@st.cache_resource(show_spinner="Préparation du modèle de machine learning…")
def paquet_modele() -> dict:
    clients, _, _ = donnees_brutes()
    return m.charger(clients)


def recharger_modele(nouveau: dict) -> None:
    """Après un réentraînement : vide les caches pour que toutes les pages utilisent le nouveau modèle."""
    paquet_modele.clear()
    portefeuille.clear()
    explicateur.clear()
    shap_echantillon.clear()


@st.cache_data(show_spinner="Calcul des scores de risque…")
def portefeuille(id_modele: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Renvoie (clients avec score actuel, historique mensuel des scores)."""
    paquet = paquet_modele()
    clients, hist, _ = donnees_brutes()

    hist = hist.copy()
    hist["pd12"] = m.proba_defaut(paquet, hist)
    hist["score"] = m.score_depuis_pd(hist["pd12"])
    hist["niveau"] = m.niveau(hist["score"].to_numpy())
    hist = hist.sort_values(["id_client", "mois"])

    dernier, precedent = hist["mois"].max(), sorted(hist["mois"].unique())[-2]
    df = clients.copy()
    df["pd12"] = m.proba_defaut(paquet, df)
    df["score"] = m.score_depuis_pd(df["pd12"])
    df["niveau"] = m.niveau(df["score"].to_numpy())
    avant = hist[hist["mois"] == precedent].set_index("id_client")["score"]
    df["score_m1"] = df["id_client"].map(avant)
    df["variation_30j"] = df["score"] - df["score_m1"]
    trois = hist[hist["mois"] == sorted(hist["mois"].unique())[-4]].set_index("id_client")["score"]
    df["variation_90j"] = df["score"] - df["id_client"].map(trois)
    df["tendance"] = df["id_client"].map(hist.groupby("id_client")["score"].apply(lambda s: s.round(1).tolist()))
    df["niveau"] = pd.Categorical(df["niveau"], categories=NIVEAUX, ordered=True)
    df.attrs["dernier_mois"] = str(pd.Timestamp(dernier).date())
    return df, hist


def portefeuille_actuel() -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    paquet = paquet_modele()
    df, hist = portefeuille(paquet["id"])
    return df, hist, paquet


@st.cache_resource(show_spinner=False)
def explicateur(id_modele: str, nom_modele: str):
    return m.explicateur(paquet_modele(), nom_modele)


def expliquer_client(ligne: pd.DataFrame, score: float) -> tuple[pd.Series, float]:
    """Contributions de chaque variable au score d'un client, en points de score."""
    paquet = paquet_modele()
    expl = explicateur(paquet["id"], paquet["meilleur"])
    contrib, base = m.valeurs_shap(paquet, expl, ligne[VARIABLES])
    return m.contributions_points(paquet, contrib.iloc[0], base, score)


@st.cache_data(show_spinner="Calcul des explications SHAP…")
def shap_echantillon(id_modele: str, nom_modele: str, n: int = 500) -> tuple[pd.DataFrame, pd.DataFrame]:
    paquet = paquet_modele()
    clients, _, _ = donnees_brutes()
    ech = clients.sample(min(n, len(clients)), random_state=1)
    contrib, _ = m.valeurs_shap(paquet, explicateur(id_modele, nom_modele), ech[VARIABLES], nom_modele)
    return contrib, ech[VARIABLES]


def filtrer(df: pd.DataFrame, niveaux=None, secteurs=None, regions=None, encours=None, texte="") -> pd.DataFrame:
    masque = np.ones(len(df), dtype=bool)
    if niveaux:
        masque &= df["niveau"].isin(niveaux).to_numpy()
    if secteurs:
        masque &= df["secteur"].isin(secteurs).to_numpy()
    if regions:
        masque &= df["region"].isin(regions).to_numpy()
    if encours:
        masque &= df["encours"].between(*encours).to_numpy()
    if texte:
        t = texte.strip().lower()
        masque &= (df["nom"].str.lower().str.contains(t, regex=False)
                   | df["id_client"].str.lower().str.contains(t, regex=False)).to_numpy()
    return df[masque]
