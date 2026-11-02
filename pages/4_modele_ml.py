"""Page 4 — Modèle de machine learning : comparaison, métriques, importance des variables, réentraînement."""
import pandas as pd
import streamlit as st

from utils import graphiques as g
from utils.donnees import donnees_brutes, paquet_modele, portefeuille_actuel, recharger_modele, shap_echantillon
from utils.modele import entrainer
from utils.style import aide, entete, kpis, nombre, panneau, titre_section

df, hist, paquet = portefeuille_actuel()
meilleur = paquet["meilleur"]
m = paquet["metriques"][meilleur]

entete("Machine learning", "Modèle de prédiction du défaut",
       f"Trois modèles sont entraînés sur {paquet['nb_entrainement']} clients puis testés sur "
       f"{len(paquet['y_test'])} clients qu'ils n'ont jamais vus. Le meilleur (selon l'AUC) est utilisé partout dans l'application.")


def v(x):
    return nombre(x * 100, 1)


kpis([
    {"libelle": "Modèle retenu", "valeur": meilleur.replace("Régression logistique", "Rég. logistique"), "icone": "🏆", "texte": True,
     "detail": f"entraîné le {paquet['date']}"},
    {"libelle": "AUC-ROC", "valeur": nombre(m["AUC-ROC"], 3), "icone": "📐", "detail": "1 = parfait, 0,5 = hasard"},
    {"libelle": "Rappel", "valeur": v(m["Rappel"]), "unite": "%", "icone": "🎣", "detail": "défauts repérés"},
    {"libelle": "Précision", "valeur": v(m["Précision"]), "unite": "%", "icone": "🎯", "detail": "alertes justes"},
    {"libelle": "F1", "valeur": v(m["F1"]), "unite": "%", "icone": "⚖️", "detail": "équilibre des deux"},
])

o1, o2, o3, o4 = st.tabs(["📊 Comparaison", "🧮 Matrice de confusion", "🧠 Importance des variables (SHAP)", "🔁 Réentraîner"])

with o1:
    c1, c2 = st.columns([1, 1.1], gap="medium")
    with c1, panneau("metriques"):
        titre_section("Métriques par modèle", "📊")
        st.plotly_chart(g.barres_metriques(paquet["metriques"]), width="stretch", config=g.CONFIG)
        tab = pd.DataFrame(paquet["metriques"]).T
        st.dataframe(tab.style.format("{:.3f}").highlight_max(color="rgba(168,85,247,0.35)"), width="stretch")
    with c2, panneau("roc"):
        titre_section("Courbes ROC comparées", "〽️")
        st.plotly_chart(g.courbes_roc(paquet["roc"], paquet["metriques"]), width="stretch", config=g.CONFIG)
    aide("<b>AUC</b> : probabilité que le modèle donne un score plus élevé à un client qui fera défaut qu'à un client sain. "
         "<b>Rappel</b> : sur 100 défauts réels, combien le modèle en a repéré. <b>Précision</b> : sur 100 alertes, combien "
         "étaient de vrais défauts. Pour du risque client, on préfère un bon rappel : rater un défaut coûte plus cher qu'une fausse alerte.")

with o2:
    nom = st.radio("Modèle", list(paquet["metriques"]), index=list(paquet["metriques"]).index(meilleur), horizontal=True)
    c1, c2 = st.columns([1.2, 1], gap="medium")
    with c1, panneau("confusion"):
        titre_section(f"Matrice de confusion : {nom}", "🧮", "seuil de 50 %")
        st.plotly_chart(g.matrice_confusion(paquet["confusion"][nom]), width="stretch", config=g.CONFIG)
    with c2:
        cm = paquet["confusion"][nom]
        aide(f"Sur les <b>{cm[1].sum()}</b> clients de test qui ont réellement fait défaut, le modèle en a détecté "
             f"<b>{cm[1][1]}</b> et en a manqué <b>{cm[1][0]}</b>.<br><br>Il a aussi déclenché <b>{cm[0][1]}</b> fausses "
             f"alertes sur {cm[0].sum()} clients sains. Ces fausses alertes ne sont pas graves : ce sont des clients à "
             "regarder de plus près.")
        st.caption(f"Gestion du déséquilibre des classes : {'activée (pondération des défauts)' if paquet['equilibre'] else 'désactivée'}. "
                   f"Taux de défaut dans les données : {nombre(paquet['taux_defaut'] * 100, 1)} %.")

with o3:
    nom_shap = st.radio("Modèle expliqué", list(paquet["metriques"]), index=list(paquet["metriques"]).index(meilleur),
                        horizontal=True, key="radio_shap")
    contrib, X = shap_echantillon(paquet["id"], nom_shap)
    c1, c2 = st.columns([1, 1.25], gap="medium")
    with c1, panneau("imp"):
        titre_section("Importance globale", "🏅", "500 clients")
        st.plotly_chart(g.importance_shap(contrib), width="stretch", config=g.CONFIG)
    with c2, panneau("beeswarm"):
        titre_section("Effet de chaque variable (SHAP summary)", "🐝")
        st.plotly_chart(g.nuage_shap(contrib, X), width="stretch", config=g.CONFIG)
    aide("Chaque point est un client. À droite du trait = la variable <b>augmente</b> son risque, à gauche = elle le "
         "<b>diminue</b>. Couleur rose = valeur haute de la variable, bleu = valeur basse. Exemple : des points roses à "
         "droite pour « Retards de paiement » veulent dire que beaucoup de retards augmentent le risque.")

with o4:
    c1, c2 = st.columns([1, 1.3], gap="medium")
    with c1, panneau("reentrainer"):
        titre_section("Réentraîner les modèles", "🔁")
        equilibrer = st.toggle("Gérer le déséquilibre des classes", value=True,
                               help="Les défauts sont rares (~11 %). Sans correction, les modèles apprennent surtout à "
                                    "reconnaître les clients sains et ratent des défauts. Désactive pour comparer le rappel.")
        if st.button("🚀 Lancer l'entraînement", width="stretch"):
            barre = st.progress(0.0, text="Préparation…")
            clients, _, _ = donnees_brutes()
            nouveau = entrainer(clients, equilibrer, progression=lambda f, t: barre.progress(f, text=t))
            recharger_modele(nouveau)
            st.toast(f"Nouveau modèle : {nouveau['meilleur']} (AUC {nouveau['metriques'][nouveau['meilleur']]['AUC-ROC']:.3f})", icon="✅")
            st.balloons()
            st.rerun()
    with c2:
        aide("Le réentraînement relance les 3 modèles, les compare, et sauvegarde le meilleur dans "
             "<code>models/meilleur_modele.joblib</code>. Toutes les pages se mettent à jour automatiquement.<br><br>"
             "Tu peux aussi le faire en ligne de commande : <code>py entrainer_modele.py</code>.")
