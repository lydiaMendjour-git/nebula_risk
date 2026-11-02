"""Page 1 — Tableau de bord : la vue d'ensemble du risque du portefeuille."""
import html

import streamlit as st

from utils import graphiques as g
from utils.config import COULEURS_NIVEAU
from utils.donnees import portefeuille_actuel
from utils.style import mois_fr, aide, entete, euros, kpis, nombre, panneau, pct, titre_section

df, hist, paquet = portefeuille_actuel()
mois = sorted(hist["mois"].unique())
avant = hist[hist["mois"] == mois[-2]]

entete("Vue d'ensemble", "Tableau de bord du risque",
       f"Situation du portefeuille à fin {mois_fr(df.attrs['dernier_mois'])} et évolution sur 12 mois. "
       "Chaque client reçoit un score de 0 (aucun risque) à 100 (défaut quasi certain) calculé par le modèle.")

# ---------------- KPI ----------------
risque = df["niveau"].isin(["Élevé", "Critique"])
risque_avant = avant["niveau"].isin(["Élevé", "Critique"])
part, part_avant = risque.mean(), risque_avant.mean()
encours_r, encours_r_avant = df.loc[risque, "encours"].sum(), avant.loc[risque_avant.values, "encours"].sum()
taux, taux_avant = df["pd12"].mean(), avant["pd12"].mean()
score, score_avant = df["score"].mean(), avant["score"].mean()
degrades = int((df["variation_30j"] >= 5).sum())


def fleche(delta, unite, mauvais_si_hausse=True, dec=1):
    if abs(delta) < 1e-9:
        return "■ stable", "neutre"
    hausse = delta > 0
    sens = "mauvais" if hausse == mauvais_si_hausse else "bon"
    return f"{'▲' if hausse else '▼'} {'+' if hausse else '−'}{nombre(abs(delta), dec)}{unite}", sens


d1 = fleche((part - part_avant) * 100, " pt")
d2 = fleche((encours_r / encours_r_avant - 1) * 100 if encours_r_avant else 0, " %")
d3 = fleche((taux - taux_avant) * 100, " pt", dec=2)
d4 = fleche(score - score_avant, " pt")
kpis([
    {"libelle": "Clients suivis", "valeur": nombre(len(df)), "icone": "👥", "delta": f"⚠ {degrades} en dégradation",
     "sens": "mauvais" if degrades else "neutre", "detail": "sur 30 jours"},
    {"libelle": "En risque élevé", "valeur": nombre(part * 100, 1), "unite": "%", "icone": "🔥",
     "delta": d1[0], "sens": d1[1], "detail": "vs mois dernier"},
    {"libelle": "Encours à risque", "valeur": euros(encours_r), "icone": "💶", "delta": d2[0], "sens": d2[1],
     "detail": "vs mois dernier"},
    {"libelle": "Défaut prédit 12 mois", "valeur": nombre(taux * 100, 1), "unite": "%", "icone": "🎯",
     "delta": d3[0], "sens": d3[1], "detail": "vs mois dernier"},
    {"libelle": "Score moyen", "valeur": nombre(score, 1), "unite": "/100", "icone": "📈", "delta": d4[0], "sens": d4[1],
     "detail": "variation 30 j"},
])

# ---------------- Évolution + répartition ----------------
c1, c2 = st.columns([1.75, 1], gap="medium")
with c1, panneau("evolution"):
    titre_section("Évolution du risque global", "📈", "part des clients en risque élevé ou critique")
    onglet1, onglet2 = st.tabs(["% en risque élevé", "Score moyen"])
    with onglet1:
        st.plotly_chart(g.courbe_evolution(hist), width="stretch", config=g.CONFIG)
    with onglet2:
        st.plotly_chart(g.courbe_score_moyen(hist), width="stretch", config=g.CONFIG)
with c2, panneau("donut"):
    titre_section("Répartition par niveau", "🍩")
    st.plotly_chart(g.donut(df), width="stretch", config=g.CONFIG)

# ---------------- Heatmap + alertes ----------------
c1, c2 = st.columns([1.75, 1], gap="medium")
with c1, panneau("heatmap"):
    titre_section("Carte de chaleur : secteur × région", "🗺️", "score moyen")
    st.plotly_chart(g.heatmap(df), width="stretch", config=g.CONFIG)
with c2, panneau("alertes"):
    titre_section("Alertes récentes", "🚨", "sur 30 jours")
    top = df[df["variation_30j"] > 0].sort_values("variation_30j", ascending=False).head(7)
    lignes = []
    for i, r in enumerate(top.itertuples()):
        coul = COULEURS_NIVEAU[r.niveau]
        lignes.append(f"""<div class="alerte" style="animation-delay:{0.1 + i * 0.06:.2f}s">
            <div class="barre" style="background:{coul};box-shadow:0 0 10px {coul}"></div>
            <div><div class="nom">{html.escape(r.nom)}</div>
            <div class="meta">{r.id_client} · {r.secteur} · <span style="color:{coul}">{r.niveau}</span></div></div>
            <div class="fleche" style="color:#FCA5A5">▲ {nombre(r.variation_30j, 1)}<small>score {r.score:.0f}</small></div></div>""")
    st.markdown("".join(lignes), unsafe_allow_html=True)
    if st.button("Voir toutes les alertes →", width="stretch"):
        st.switch_page("pages/7_alertes_rapports.py")

aide("<b>Comment lire ce tableau de bord ?</b> Les flèches comparent avec le mois précédent : "
     "<span style='color:#FCA5A5'>rouge</span> = le risque augmente, <span style='color:#86EFAC'>vert</span> = il baisse. "
     "Survole les graphiques pour voir le détail, et clique sur une légende pour masquer une catégorie.")
