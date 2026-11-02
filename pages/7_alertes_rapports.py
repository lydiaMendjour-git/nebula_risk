"""Page 7 — Alertes et rapports : seuils paramétrables, liste des clients à surveiller, exports CSV et PDF."""
import datetime as dt

import pandas as pd
import streamlit as st

from utils import graphiques as g
from utils.config import PASTILLES
from utils.donnees import portefeuille_actuel
from utils.rapport_pdf import rapport_portefeuille
from utils.style import aide, entete, euros, kpis, nombre, panneau, titre_section

df, hist, paquet = portefeuille_actuel()

entete("Surveillance", "Alertes et rapports",
       "Choisis tes propres seuils d'alerte. La liste des clients à surveiller se met à jour, et tu peux la télécharger "
       "en CSV (Excel) ou en rapport PDF prêt à envoyer.")

with panneau("seuils"):
    titre_section("Seuils d'alerte", "🎚️")
    c1, c2, c3, c4, c5 = st.columns(5)
    s_score = c1.slider("Score minimum", 0, 100, 45, help="45 = début du niveau « Élevé »")
    s_degr = c2.slider("Dégradation sur 30 j (points)", 0, 30, 8)
    s_ret = c3.slider("Retards sur 12 mois", 0, 12, 5)
    s_inc = c4.slider("Incidents bancaires", 0, 10, 3)
    s_treso = c5.slider("Trésorerie sous (jours)", -30, 60, 0)
    mode = st.radio("Un client est en alerte s'il dépasse…", ["au moins un seuil", "tous les seuils"], horizontal=True)

criteres = pd.DataFrame({
    "Score élevé": df["score"] >= s_score,
    "Dégradation rapide": df["variation_30j"] >= s_degr,
    "Retards répétés": df["nb_retards_12m"] >= s_ret,
    "Incidents bancaires": df["incidents_bancaires_12m"] >= s_inc,
    "Trésorerie négative" if s_treso <= 0 else "Trésorerie faible": df["tresorerie_jours"] < s_treso,
})
alerte = criteres.any(axis=1) if mode == "au moins un seuil" else criteres.all(axis=1)
alertes = df[alerte].assign(motifs=criteres[alerte].apply(lambda r: " · ".join(r.index[r]), axis=1)).sort_values(
    "score", ascending=False)

kpis([
    {"libelle": "Clients en alerte", "valeur": nombre(len(alertes)), "icone": "🚨", "detail": f"sur {len(df)}"},
    {"libelle": "Encours concerné", "valeur": euros(alertes["encours"].sum()), "icone": "💶",
     "detail": f"{nombre(alertes['encours'].sum() / df['encours'].sum() * 100, 1)} % du total"},
    {"libelle": "Défauts attendus", "valeur": nombre(alertes["pd12"].sum(), 1), "icone": "🎯", "detail": "somme des PD 12 mois"},
    {"libelle": "Critiques", "valeur": nombre((alertes["niveau"] == "Critique").sum()), "icone": "🟣"},
])

c1, c2 = st.columns([1, 1.6], gap="medium")
with c1, panneau("histo"):
    titre_section("Distribution des scores", "📊")
    st.plotly_chart(g.histogramme_scores(df, s_score), width="stretch", config=g.CONFIG)
    motifs = criteres[alerte].sum().sort_values(ascending=False)
    st.markdown("".join(f'<div class="ligne-info"><span>{k}</span><span>{v} clients</span></div>' for k, v in motifs.items()),
                unsafe_allow_html=True)
with c2, panneau("liste"):
    titre_section("Clients à surveiller", "📋", "triés par score")
    st.dataframe(
        alertes.assign(risque=alertes["niveau"].astype(str).map(PASTILLES), pd12_pct=alertes["pd12"] * 100)[
            ["id_client", "nom", "risque", "score", "variation_30j", "pd12_pct", "encours", "motifs"]],
        hide_index=True, width="stretch", height=420,
        column_config={
            "id_client": "ID", "nom": "Client", "risque": "Risque",
            "score": st.column_config.ProgressColumn("Score", min_value=0, max_value=100, format="%.0f"),
            "variation_30j": st.column_config.NumberColumn("Var. 30 j", format="%+.1f"),
            "pd12_pct": st.column_config.NumberColumn("PD 12 m", format="%.1f %%"),
            "encours": st.column_config.NumberColumn("Encours (€)", format="localized"),
            "motifs": st.column_config.TextColumn("Motif(s) de l'alerte", width="large"),
        })

titre_section("Télécharger", "⬇️")
d1, d2, _ = st.columns([1, 1, 1.3])
export = alertes.drop(columns=["tendance"]).rename(columns={"pd12": "proba_defaut_12m"})
d1.download_button("📊 Liste des alertes (CSV / Excel)", export.to_csv(index=False, sep=";", decimal=",").encode("utf-8-sig"),
                   file_name=f"alertes_{dt.date.today():%Y%m%d}.csv", mime="text/csv", width="stretch")
seuils = {"Score minimum": s_score, "Dégradation sur 30 jours": f"{s_degr} points", "Retards sur 12 mois": s_ret,
          "Incidents bancaires": s_inc, "Trésorerie inférieure à": f"{s_treso} jours", "Règle": mode}
d2.download_button("📄 Rapport PDF du portefeuille", rapport_portefeuille(df, alertes, seuils),
                   file_name=f"rapport_risque_{dt.date.today():%Y%m%d}.pdf", mime="application/pdf", width="stretch")

aide("Le CSV s'ouvre directement dans Excel (séparateur point-virgule, virgule décimale). "
     "Le PDF contient les chiffres clés, la répartition par niveau et la liste des clients en alerte.")
