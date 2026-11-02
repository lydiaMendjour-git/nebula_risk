"""Page 6 — Segmentation : regrouper les clients qui se ressemblent (K-Means) et décrire chaque groupe."""
import pandas as pd
import streamlit as st
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

from utils import graphiques as g
from utils.config import LIBELLES
from utils.donnees import portefeuille_actuel
from utils.style import aide, entete, euros, kpis, nombre, panneau, titre_section

df, hist, paquet = portefeuille_actuel()

entete("Clustering", "Segmentation du portefeuille",
       "L'algorithme K-Means range automatiquement les clients en groupes de profils similaires. "
       "Utile pour adapter le suivi : on ne traite pas un client « fragile mais stable » comme un client « en chute libre ».")

AXES = ["ratio_endettement_pct", "tresorerie_jours", "marge_ebe_pct", "evolution_ca_pct", "nb_retards_12m",
        "incidents_bancaires_12m", "utilisation_decouvert_pct", "anciennete_ans", "score"]
NOMS = ["Très solides", "Stables", "Sous vigilance", "Fragiles", "En difficulté", "Critiques"]


@st.cache_data(show_spinner="Regroupement des clients…")
def segmenter(id_modele: str, k: int):
    X = StandardScaler().fit_transform(df[AXES])
    seg = KMeans(n_clusters=k, n_init=10, random_state=42).fit_predict(X)
    pcs = PCA(n_components=2, random_state=42).fit_transform(X)
    res = df.assign(segment=seg, pc1=pcs[:, 0], pc2=pcs[:, 1])
    # On renumérote les segments du moins risqué au plus risqué, puis on leur donne un nom
    rang = res.groupby("segment")["score"].mean().rank().astype(int) - 1
    res["segment"] = res["segment"].map(rang)
    noms_k = NOMS if k == 6 else [NOMS[round(i * 5 / (k - 1))] for i in range(k)]
    return res, {i: noms_k[i] for i in range(k)}


k = st.slider("Nombre de segments", 3, 6, 4, help="Essaie plusieurs valeurs : 4 est souvent un bon compromis.")
res, noms = segmenter(paquet["id"], k)

resume = res.groupby("segment").agg(n=("id_client", "size"), score=("score", "mean"), encours=("encours", "sum"),
                                    pd=("pd12", "mean"))
kpis([{"libelle": noms[s], "valeur": nombre(r.n), "unite": " clients", "icone": ["💎", "🛡️", "👀", "⚠️", "🔥", "🚨"][NOMS.index(noms[s])],
       "delta": f"score {r.score:.0f}", "sens": "bon" if r.score < 25 else "neutre" if r.score < 45 else "mauvais",
       "detail": f"{euros(r.encours)} d'encours"} for s, r in resume.iterrows()])

c1, c2 = st.columns([1.2, 1], gap="medium")
with c1, panneau("pca"):
    titre_section("Carte des clients (projection PCA en 2D)", "🌌", "chaque point = un client")
    st.plotly_chart(g.nuage_segments(res, noms), width="stretch", config=g.CONFIG)
with c2, panneau("radar"):
    titre_section("Profil type de chaque segment", "🕸️", "rang dans le portefeuille, 0 à 100")
    rangs = res[AXES].rank(pct=True) * 100
    profils = rangs.groupby(res["segment"]).mean()
    st.plotly_chart(g.radar(profils, noms), width="stretch", config=g.CONFIG)

with panneau("profils"):
    titre_section("Valeurs moyennes par segment", "📋")
    tab = res.groupby("segment")[AXES + ["encours", "ca_annuel"]].mean()
    tab.index = [noms[i] for i in tab.index]
    tab.insert(0, "Clients", res["segment"].value_counts().sort_index().values)
    tab = tab.rename(columns=LIBELLES)
    st.dataframe(tab.style.format(lambda x: nombre(x, 1) if abs(x) < 1000 else euros(x)), width="stretch")
    secteurs = pd.crosstab(res["segment"].map(noms), res["secteur"], normalize="index") * 100
    with st.expander("Répartition des secteurs dans chaque segment (%)"):
        st.dataframe(secteurs.round(0), width="stretch")

aide("Sur le radar, une valeur proche de 100 veut dire « parmi les plus hauts du portefeuille » pour cet indicateur. "
     "Par exemple un segment avec « Retards » à 90 et « Trésorerie » à 15 regroupe des clients qui paient en retard "
     "et ont peu de trésorerie.")
