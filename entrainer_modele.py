"""
Entraîne et compare les 3 modèles, puis sauvegarde le meilleur dans models/meilleur_modele.joblib.

    py entrainer_modele.py

(Tu peux aussi le faire depuis l'application : page « Modèle ML », onglet « Réentraîner ».)
"""
import pandas as pd

from utils.config import FICHIER_CLIENTS, DOSSIER_DATA
from utils.modele import entrainer

if __name__ == "__main__":
    if not FICHIER_CLIENTS.exists():
        from generer_donnees import generer
        generer(DOSSIER_DATA)
    clients = pd.read_csv(FICHIER_CLIENTS)
    paquet = entrainer(clients, equilibrer=True, progression=lambda f, msg: print(f"[{f:4.0%}] {msg}"))
    print("\nRésultats sur les clients de test (jamais vus pendant l'entraînement) :")
    print(pd.DataFrame(paquet["metriques"]).T.round(3).to_string())
    print(f"\nMeilleur modèle : {paquet['meilleur']} (sauvegardé dans models/meilleur_modele.joblib)")
