"""
Machine learning : entraînement, comparaison, prédiction et explication (SHAP).

Trois modèles sont comparés : Régression logistique, Random Forest, XGBoost.
Le meilleur (selon l'AUC sur des clients jamais vus pendant l'entraînement) est sauvegardé
dans models/meilleur_modele.joblib.
"""
from __future__ import annotations

import datetime as dt
import uuid

import joblib
import numpy as np
import pandas as pd
import shap
import sklearn
import xgboost
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (confusion_matrix, f1_score, precision_score, recall_score,
                             roc_auc_score, roc_curve)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from xgboost import XGBClassifier

from utils.config import FICHIER_MODELE, NIVEAUX, SEUILS_SCORE, VARIABLES, VARIABLES_CAT, VARIABLES_NUM

NOMS_MODELES = ["Régression logistique", "Random Forest", "XGBoost"]


# ------------------------------------------------------------------ construction
def _preparation():
    return ColumnTransformer([
        ("num", StandardScaler(), VARIABLES_NUM),
        ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), VARIABLES_CAT),
    ])


def _modeles(poids: float, equilibrer: bool) -> dict:
    cw = "balanced" if equilibrer else None
    return {
        "Régression logistique": LogisticRegression(max_iter=2000, C=0.5, class_weight=cw),
        "Random Forest": RandomForestClassifier(n_estimators=300, min_samples_leaf=5, max_features="sqrt",
                                                class_weight=cw, n_jobs=-1, random_state=42),
        "XGBoost": XGBClassifier(n_estimators=350, learning_rate=0.04, max_depth=3, subsample=0.85,
                                 colsample_bytree=0.8, min_child_weight=3, reg_lambda=2.0,
                                 scale_pos_weight=poids if equilibrer else 1.0,
                                 eval_metric="auc", random_state=42, n_jobs=-1),
    }


# ------------------------------------------------------------------ entraînement
def entrainer(clients: pd.DataFrame, equilibrer: bool = True, progression=None) -> dict:
    """Entraîne les 3 modèles et renvoie un "paquet" avec modèles, métriques et courbes.
    `progression(fraction, message)` est appelé pour faire avancer une barre de progression."""
    def avance(f, msg):
        if progression:
            progression(f, msg)

    X, y = clients[VARIABLES], clients["defaut"].astype(int)
    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.25, stratify=y, random_state=42)
    poids = float((y_tr == 0).sum() / max((y_tr == 1).sum(), 1))

    paquet = {"modeles": {}, "metriques": {}, "roc": {}, "confusion": {}}
    for i, (nom, clf) in enumerate(_modeles(poids, equilibrer).items()):
        avance(0.1 + 0.25 * i, f"Entraînement : {nom}…")
        pipe = Pipeline([("prep", _preparation()), ("clf", clf)]).fit(X_tr, y_tr)
        proba = pipe.predict_proba(X_te)[:, 1]
        pred = (proba >= 0.5).astype(int)
        fpr, tpr, _ = roc_curve(y_te, proba)
        paquet["modeles"][nom] = pipe
        paquet["roc"][nom] = (fpr, tpr)
        paquet["confusion"][nom] = confusion_matrix(y_te, pred)
        paquet["metriques"][nom] = {
            "AUC-ROC": roc_auc_score(y_te, proba),
            "Précision": precision_score(y_te, pred, zero_division=0),
            "Rappel": recall_score(y_te, pred, zero_division=0),
            "F1": f1_score(y_te, pred, zero_division=0),
        }

    avance(0.85, "Choix du meilleur modèle et sauvegarde…")
    meilleur = max(paquet["metriques"], key=lambda m: paquet["metriques"][m]["AUC-ROC"])
    paquet.update({
        "meilleur": meilleur,
        "equilibre": equilibrer,
        # Correction des probabilités : quand on "sur-pondère" les défauts pendant l'entraînement,
        # le modèle les surestime. On remet les probabilités à l'échelle réelle avec ce poids.
        "poids": poids if equilibrer else 1.0,
        "fond_shap": X_tr.sample(min(200, len(X_tr)), random_state=0),
        "X_test": X_te, "y_test": y_te,
        "nb_entrainement": len(X_tr), "taux_defaut": float(y.mean()),
        "versions": {"sklearn": sklearn.__version__, "xgboost": xgboost.__version__},
        "date": dt.datetime.now().strftime("%d/%m/%Y %H:%M"),
        "id": uuid.uuid4().hex[:8],
    })
    FICHIER_MODELE.parent.mkdir(exist_ok=True)
    joblib.dump(paquet, FICHIER_MODELE)
    avance(1.0, "Terminé")
    return paquet


def charger(clients: pd.DataFrame) -> dict:
    """Charge le modèle sauvegardé. S'il n'existe pas ou a été créé avec d'autres versions
    des bibliothèques (ex : autre PC), on le réentraîne automatiquement (environ 10 secondes)."""
    try:
        paquet = joblib.load(FICHIER_MODELE)
        if paquet["versions"] == {"sklearn": sklearn.__version__, "xgboost": xgboost.__version__}:
            return paquet
    except Exception:
        pass
    return entrainer(clients)


# ------------------------------------------------------------------ prédiction
def proba_defaut(paquet: dict, X: pd.DataFrame, modele: str | None = None) -> np.ndarray:
    """Probabilité de défaut à 12 mois, remise à l'échelle réelle."""
    p = paquet["modeles"][modele or paquet["meilleur"]].predict_proba(X[VARIABLES])[:, 1]
    w = paquet["poids"]
    return p / (p + (1 - p) * w)


def score_depuis_pd(pd12) -> np.ndarray:
    """Score de risque 0-100. Racine carrée pour étaler les petites probabilités :
    PD 1 % → 10, 4 % → 20, 9 % → 30, 25 % → 50, 49 % → 70, 81 % → 90."""
    return np.clip(100 * np.sqrt(np.asarray(pd12, dtype=float)), 0, 100)


def niveau(score) -> np.ndarray | str:
    idx = np.digitize(score, SEUILS_SCORE)
    if np.ndim(idx) == 0:
        return NIVEAUX[int(idx)]
    return np.array(NIVEAUX, dtype=object)[idx]


def pd_horizons(pd12: float) -> dict:
    """Probabilité de défaut à 3, 6 et 12 mois (risque supposé réparti dans l'année,
    un peu plus concentré au début pour les clients très fragiles)."""
    acc = 1 + 0.6 * pd12   # plus le risque est fort, plus il arrive tôt
    return {m: 1 - (1 - pd12) ** min(1.0, (m / 12) ** (1 / acc)) for m in (3, 6, 12)}


# ------------------------------------------------------------------ explication (SHAP)
def explicateur(paquet: dict, modele: str | None = None):
    nom = modele or paquet["meilleur"]
    pipe = paquet["modeles"][nom]
    if nom == "Régression logistique":
        fond = pipe["prep"].transform(paquet["fond_shap"])
        return shap.LinearExplainer(pipe["clf"], shap.maskers.Independent(fond, max_samples=len(fond)))
    return shap.TreeExplainer(pipe["clf"])


def _colonnes_transformees(pipe) -> list[str]:
    noms = []
    for n in pipe["prep"].get_feature_names_out():
        n = n.split("__", 1)[1]
        noms.append("secteur" if n.startswith("secteur_") else n)
    return noms


def valeurs_shap(paquet: dict, expl, X: pd.DataFrame, modele: str | None = None):
    """Contributions SHAP regroupées par variable d'origine (le secteur est regroupé en une seule
    ligne). Renvoie (DataFrame des contributions, valeur de base)."""
    pipe = paquet["modeles"][modele or paquet["meilleur"]]
    Xt = pipe["prep"].transform(X[VARIABLES])
    sv = expl.shap_values(Xt)
    base = expl.expected_value
    if isinstance(sv, list):
        sv = sv[1]
    sv = np.asarray(sv)
    if sv.ndim == 3:            # Random Forest : une sortie par classe → on garde "défaut"
        sv = sv[:, :, 1]
    base = np.ravel(base)
    base = float(base[-1]) if base.size > 1 else float(base[0])
    df = pd.DataFrame(sv, columns=_colonnes_transformees(pipe), index=X.index)
    df = df.T.groupby(level=0, sort=False).sum().T
    return df[VARIABLES], base


def _pd_depuis_sortie(paquet, valeur, modele=None):
    """Transforme la sortie brute du modèle (log-odds ou probabilité) en PD corrigée."""
    nom = modele or paquet["meilleur"]
    p = valeur if nom == "Random Forest" else 1 / (1 + np.exp(-valeur))
    p = np.clip(p, 1e-6, 1 - 1e-6)
    w = paquet["poids"]
    return p / (p + (1 - p) * w)


def contributions_points(paquet: dict, contrib: pd.Series, base: float, score_client: float,
                         modele: str | None = None) -> tuple[pd.Series, float]:
    """Convertit les contributions SHAP en "points de score" pour qu'elles s'additionnent
    exactement : score de référence + somme des contributions = score du client."""
    score_ref = float(score_depuis_pd(_pd_depuis_sortie(paquet, base, modele)))
    total = contrib.sum()
    ratio = (score_client - score_ref) / total if abs(total) > 1e-9 else 0.0
    return contrib * ratio, score_ref
