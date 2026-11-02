"""Page 2 — Portefeuille clients : tableau interactif, filtres et recherche."""
import streamlit as st

from utils.config import NIVEAUX, PASTILLES
from utils.donnees import filtrer, portefeuille_actuel
from utils.style import entete, euros, kpis, nombre

df, hist, paquet = portefeuille_actuel()

entete("Portefeuille", "Portefeuille clients",
       "Tous les clients suivis, triés du plus risqué au moins risqué. Filtre dans la barre de gauche, "
       "cherche un nom, puis clique sur une ligne pour ouvrir sa fiche.")

# ---------------- Filtres (barre latérale) ----------------
with st.sidebar:
    st.markdown("#### 🎛️ Filtres")
    niveaux = st.multiselect("Niveau de risque", NIVEAUX, placeholder="Tous")
    secteurs = st.multiselect("Secteur", sorted(df["secteur"].unique()), placeholder="Tous")
    regions = st.multiselect("Région", sorted(df["region"].unique()), placeholder="Toutes")
    tranches = {"Tous les encours": None, "Moins de 100 k€": (0, 1e5), "100 k€ à 500 k€": (1e5, 5e5),
                "500 k€ à 1 M€": (5e5, 1e6), "Plus de 1 M€": (1e6, 1e12)}
    tranche = st.selectbox("Tranche d'encours", list(tranches))

recherche = st.text_input("🔎 Rechercher un client", placeholder="Nom ou identifiant, ex : Brasserie, CL-0042…")
vue = filtrer(df, niveaux, secteurs, regions, tranches[tranche], recherche).sort_values("score", ascending=False)

kpis([
    {"libelle": "Clients affichés", "valeur": nombre(len(vue)), "icone": "👥", "detail": f"sur {len(df)}"},
    {"libelle": "Encours total", "valeur": euros(vue["encours"].sum()), "icone": "💶"},
    {"libelle": "Score moyen", "valeur": nombre(vue["score"].mean() if len(vue) else 0, 1), "unite": "/100", "icone": "📊"},
    {"libelle": "Élevé + critique", "valeur": nombre(vue["niveau"].isin(["Élevé", "Critique"]).sum()), "icone": "🔥"},
])

tableau = vue.assign(
    risque=vue["niveau"].astype(str).map(PASTILLES),
    pd12_pct=vue["pd12"] * 100,
)[["id_client", "nom", "risque", "score", "tendance", "variation_30j", "pd12_pct", "encours", "ratio_endettement_pct",
   "nb_retards_12m", "incidents_bancaires_12m", "secteur", "region"]]

selection = st.dataframe(
    tableau, hide_index=True, width="stretch", height=560, on_select="rerun", selection_mode="single-row",
    column_config={
        "id_client": st.column_config.TextColumn("ID", width="small"),
        "nom": st.column_config.TextColumn("Client", width="medium"),
        "risque": st.column_config.TextColumn("Risque"),
        "score": st.column_config.ProgressColumn("Score", min_value=0, max_value=100, format="%.0f", width="small"),
        "tendance": st.column_config.LineChartColumn("Tendance 12 mois", y_min=0, y_max=100, width="small"),
        "variation_30j": st.column_config.NumberColumn("Var. 30 j", format="%+.1f", help="Évolution du score sur un mois"),
        "pd12_pct": st.column_config.NumberColumn("PD 12 mois", format="%.1f %%", help="Probabilité de défaut à 12 mois"),
        "encours": st.column_config.NumberColumn("Encours (€)", format="localized"),
        "ratio_endettement_pct": st.column_config.NumberColumn("Endettement", format="%.0f %%"),
        "nb_retards_12m": st.column_config.NumberColumn("Retards", format="%d"),
        "incidents_bancaires_12m": st.column_config.NumberColumn("Incidents", format="%d"),
        "secteur": "Secteur", "region": "Région",
    },
)

c1, c2 = st.columns([1, 1])
lignes = selection.selection.rows if selection else []
with c1:
    if lignes:
        client = tableau.iloc[lignes[0]]
        if st.button(f"Ouvrir la fiche de {client['nom']} →", width="stretch"):
            st.session_state["client_id"] = client["id_client"]
            st.switch_page("pages/3_fiche_client.py")
    else:
        st.caption("👆 Clique sur une ligne du tableau (case à gauche) pour ouvrir la fiche du client.")
with c2:
    st.download_button("⬇️ Exporter la sélection (CSV)", vue.drop(columns=["tendance"]).to_csv(index=False, sep=";", decimal=",").encode("utf-8-sig"),
                       file_name="portefeuille_filtre.csv", mime="text/csv", width="stretch")
