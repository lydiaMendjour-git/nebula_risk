"""Page 3 — Fiche client : score, probabilités de défaut, explication SHAP, historique, actions."""
import html

import streamlit as st

from utils import graphiques as g
from utils.config import COULEURS_NIVEAU
from utils.donnees import donnees_brutes, expliquer_client, portefeuille_actuel
from utils.modele import pd_horizons
from utils.rapport_pdf import fiche_client
from utils.recommandations import PRIORITES, recommandations
from utils.style import aide, entete, euros, nombre, panneau, titre_section

df, hist, paquet = portefeuille_actuel()
_, _, paiements = donnees_brutes()

entete("Analyse individuelle", "Fiche client",
       "Le score du client, sa probabilité de défaut, <b>pourquoi</b> le modèle le juge risqué, et quoi faire.")

# ---------------- Sélection du client ----------------
ordre = df.sort_values("score", ascending=False)
options = ordre["id_client"].tolist()
etiquettes = dict(zip(ordre["id_client"], ordre["id_client"] + " · " + ordre["nom"] + " · score " + ordre["score"].round(0).astype(int).astype(str)))
choisi = st.session_state.get("client_id", options[0])
id_client = st.selectbox("Client", options, index=options.index(choisi) if choisi in options else 0,
                         format_func=etiquettes.get, help="Tape quelques lettres pour chercher. Les clients sont triés du plus risqué au moins risqué.")
st.session_state["client_id"] = id_client

c = df.set_index("id_client").loc[id_client]
c["id_client"] = id_client
horizons = pd_horizons(float(c["pd12"]))
ligne = df[df["id_client"] == id_client]
contrib, score_ref = expliquer_client(ligne, float(c["score"]))
recos = recommandations(c)
coul = COULEURS_NIVEAU[c["niveau"]]

# ---------------- Identité / jauge / probabilités ----------------
c1, c2, c3 = st.columns([1.05, 1.1, 1], gap="medium")
with c1:
    infos = [("Secteur", c["secteur"]), ("Région", c["region"]), ("Ancienneté", f"{nombre(c['anciennete_ans'], 0)} ans"),
             ("Salariés", nombre(c["nb_salaries"])), ("Chiffre d'affaires", euros(c["ca_annuel"])),
             ("Évolution du CA", f"{c['evolution_ca_pct']:+.1f} %".replace(".", ",")),
             ("Encours de dette", euros(c["encours"])), ("Endettement", f"{nombre(c['ratio_endettement_pct'])} % du CA"),
             ("Trésorerie", f"{nombre(c['tresorerie_jours'])} jours"), ("Retards / incidents (12 m)",
                                                                      f"{int(c['nb_retards_12m'])} / {int(c['incidents_bancaires_12m'])}")]
    lignes = "".join(f'<div class="ligne-info"><span>{a}</span><span>{html.escape(str(b))}</span></div>' for a, b in infos)
    st.markdown(f"""<div class="carte-client" style="border-color:{coul}66;box-shadow:0 0 30px {coul}22">
        <div class="n">{html.escape(c['nom'])}</div><div class="i">{id_client}</div>{lignes}</div>""", unsafe_allow_html=True)
with c2, panneau("jauge"):
    titre_section("Score de risque", "🎯")
    st.plotly_chart(g.jauge(float(c["score"]), float(c["score_m1"])), width="stretch", config=g.CONFIG)
with c3:
    titre_section("Probabilité de défaut", "⏳")
    for m in (3, 6, 12):
        p = horizons[m]
        teinte = "#22C55E" if p < 0.05 else "#F59E0B" if p < 0.15 else "#EF4444" if p < 0.35 else "#C026D3"
        st.markdown(f"""<div class="pd-horizon" style="margin-bottom:10px"><div class="h">Dans {m} mois</div>
            <div class="v" style="color:{teinte};text-shadow:0 0 18px {teinte}88">{nombre(p * 100, 1)} %</div></div>""",
                    unsafe_allow_html=True)
    st.download_button("📄 Fiche PDF", fiche_client(c, horizons, contrib, recos), file_name=f"fiche_{id_client}.pdf",
                       mime="application/pdf", width="stretch")

# ---------------- SHAP + recommandations ----------------
c1, c2 = st.columns([1.5, 1], gap="medium")
with c1, panneau("shap"):
    titre_section("Pourquoi ce score ? (explication SHAP)", "🧠")
    st.plotly_chart(g.cascade(contrib, score_ref, float(c["score"])), width="stretch", config=g.CONFIG)
    aide("On part du <b>score moyen</b> du portefeuille. Chaque barre <span style='color:#FCA5A5'>rouge</span> "
         "ajoute du risque, chaque barre <span style='color:#86EFAC'>verte</span> en retire. On arrive au score du client.")
with c2:
    titre_section("Actions recommandées", "🧭")
    blocs = []
    for i, r in enumerate(recos):
        pc = PRIORITES[r["priorite"]]
        blocs.append(f"""<div class="reco" style="animation-delay:{0.1 + i * 0.07:.2f}s"><div class="ic">{r['icone']}</div>
            <div><div class="t">{r['titre']} <span class="badge" style="color:{pc};background:{pc}1F;border:1px solid {pc}55;margin-left:6px">{r['priorite']}</span></div>
            <div class="d">{r['detail']}</div></div></div>""")
    st.markdown("".join(blocs), unsafe_allow_html=True)

# ---------------- Historique ----------------
with panneau("historique"):
    titre_section("Historique", "🕓", "12 derniers mois")
    t1, t2 = st.tabs(["Évolution du score", "Paiements et incidents"])
    with t1:
        st.plotly_chart(g.courbe_score_client(hist[hist["id_client"] == id_client]), width="stretch", config=g.CONFIG)
    with t2:
        p = paiements[paiements["id_client"] == id_client]
        st.plotly_chart(g.historique_paiements(p), width="stretch", config=g.CONFIG)
        n_ret, n_imp = (p["statut"] == "En retard").sum(), (p["statut"] == "Impayé").sum()
        st.caption(f"{12 - n_ret - n_imp} échéances payées à l'heure, {n_ret} en retard, {n_imp} impayée(s) (> 60 jours), "
                   f"{int(p['incident_bancaire'].sum())} incident(s) bancaire(s).")

if st.button("🧪 Tester des scénarios pour ce client dans le simulateur →"):
    st.switch_page("pages/5_simulateur.py")
