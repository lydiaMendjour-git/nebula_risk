"""
NEBULA · Risk Intelligence — plateforme BI d'analyse du risque client.

Lancer :  py -m streamlit run app.py
Ce fichier crée la navigation (menu de gauche) puis affiche la page choisie (dossier pages/).
"""
import pandas as pd
import streamlit as st
from streamlit_option_menu import option_menu

from utils.config import NOM_APP, SOUS_NOM

st.set_page_config(page_title=f"{NOM_APP} · {SOUS_NOM}", page_icon="🪐", layout="wide",
                   initial_sidebar_state="expanded")

from utils.donnees import portefeuille_actuel  # noqa: E402
from utils.style import banniere, injecter_css, intro, logo_sidebar  # noqa: E402

# (fichier, titre affiché, icône du menu, emoji de la bannière)
PAGES = [
    ("pages/1_tableau_de_bord.py", "Tableau de bord", "grid-1x2-fill", "📊"),
    ("pages/2_portefeuille.py", "Portefeuille clients", "people-fill", "👥"),
    ("pages/3_fiche_client.py", "Fiche client", "person-vcard-fill", "🪪"),
    ("pages/4_modele_ml.py", "Modèle ML", "cpu-fill", "🧠"),
    ("pages/5_simulateur.py", "Simulateur what-if", "sliders", "🎚️"),
    ("pages/6_segmentation.py", "Segmentation", "bullseye", "🌌"),
    ("pages/7_alertes_rapports.py", "Alertes & rapports", "bell-fill", "🚨"),
]
pages = [st.Page(f, title=t, default=(i == 0)) for i, (f, t, _, _) in enumerate(PAGES)]
titres = [p[1] for p in PAGES]
page = st.navigation(pages, position="hidden")

injecter_css()
intro()

with st.sidebar:
    logo_sidebar()
    st.markdown('<div class="titre-nav">Navigation</div>', unsafe_allow_html=True)
    actuelle = titres.index(page.title)
    choix = option_menu(
        None, titres, icons=[p[2] for p in PAGES], default_index=actuelle, key=f"menu_{actuelle}",
        styles={
            "container": {"padding": "6px", "background-color": "rgba(21,18,31,0.55)", "border-radius": "16px",
                          "border": "1px solid rgba(168,85,247,0.22)"},
            "icon": {"color": "#D8B4FE", "font-size": "20px", "margin-right": "6px"},
            "nav-link": {"font-family": "Sora, Inter, sans-serif", "font-size": "16.5px", "font-weight": "500", "white-space": "nowrap", "color": "#EDE9FE",
                         "border-radius": "13px", "margin": "5px 0", "padding": "12px 14px",
                         "--hover-color": "rgba(168,85,247,0.25)"},
            "nav-link-selected": {"background": "linear-gradient(120deg, #7C3AED, #A855F7 60%, #EC4899)",
                                  "color": "#ffffff", "font-weight": "700", "font-size": "16.5px",
                                  "box-shadow": "0 0 20px rgba(168,85,247,0.55)"},
        },
    )
    if choix != page.title:
        st.switch_page(pages[titres.index(choix)])

df, _, paquet = portefeuille_actuel()
banniere(page.title, PAGES[actuelle][3], df.attrs["dernier_mois"], len(df))
page.run()

# Encadré en bas de la barre latérale
with st.sidebar:
    m = paquet["metriques"][paquet["meilleur"]]
    st.markdown(f"""<div class="pied-sidebar"><span class="point-vivant"></span><b>Modèle actif</b> : {paquet['meilleur']}<br>
        AUC {m['AUC-ROC']:.3f} · entraîné le {paquet['date']}<br>
        Données au <b>{pd.Timestamp(df.attrs['dernier_mois']):%m/%Y}</b> · {len(df)} clients<br>
        <span style="color:#F0ABFC">Données 100 % fictives</span></div>""".replace("AUC 0.", "AUC 0,"),
                unsafe_allow_html=True)
