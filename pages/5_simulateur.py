"""Page 5 — Simulateur « what-if » : et si la situation du client changeait ?"""
import streamlit as st

from utils import graphiques as g
from utils.config import LIBELLES
from utils.donnees import expliquer_client, portefeuille_actuel
from utils.modele import niveau, proba_defaut, score_depuis_pd
from utils.style import aide, badge, entete, nombre, panneau, titre_section

df, hist, paquet = portefeuille_actuel()

entete("Scénarios", "Simulateur « what-if »",
       "Modifie la situation d'un client avec les curseurs : le score est recalculé instantanément par le modèle. "
       "Idéal pour préparer un entretien : « si vous réduisez votre découvert, votre risque baisse de… ».")

ordre = df.sort_values("score", ascending=False)
options = ordre["id_client"].tolist()
noms = dict(zip(ordre["id_client"], ordre["id_client"] + " · " + ordre["nom"]))
choisi = st.session_state.get("client_id", options[0])
id_client = st.selectbox("Client de départ", options, index=options.index(choisi) if choisi in options else 0, format_func=noms.get)
st.session_state["client_id"] = id_client
base = df[df["id_client"] == id_client].iloc[0]

# Curseurs : (variable, min, max, pas, format)
CURSEURS = {
    "ca_annuel": (0.0, round(max(3 * base["ca_annuel"], 200_000) / 1000), 5.0, "%.0f k€"),
    "evolution_ca_pct": (-60.0, 60.0, 0.5, "%+.1f %%"),
    "marge_ebe_pct": (-35.0, 45.0, 0.5, "%.1f %%"),
    "encours": (0.0, round(max(3 * base["encours"], 100_000) / 1000), 5.0, "%.0f k€"),
    "tresorerie_jours": (-30.0, 200.0, 1.0, "%.0f j"),
    "utilisation_decouvert_pct": (0.0, 100.0, 1.0, "%.0f %%"),
    "nb_retards_12m": (0, 12, 1, "%d"),
    "retard_moyen_jours": (0.0, 120.0, 1.0, "%.0f j"),
    "incidents_bancaires_12m": (0, 12, 1, "%d"),
}


EN_MILLIERS = {"ca_annuel", "encours"}   # affichés en k€ sur les curseurs


def cle(v):
    return f"wi_{v}_{id_client}"


def valeur_depart(v):
    if v in EN_MILLIERS:
        return float(round(base[v] / 1000))
    return int(base[v]) if isinstance(CURSEURS[v][0], int) else float(base[v])


def appliquer(scenario):
    for v in CURSEURS:
        st.session_state[cle(v)] = valeur_depart(v)
    lo = lambda v, x: max(CURSEURS[v][0], min(CURSEURS[v][1], x))
    if scenario == "choc":
        st.session_state[cle("ca_annuel")] = float(round(base["ca_annuel"] * 0.8 / 1000))
        st.session_state[cle("evolution_ca_pct")] = lo("evolution_ca_pct", base["evolution_ca_pct"] - 20)
        st.session_state[cle("tresorerie_jours")] = lo("tresorerie_jours", base["tresorerie_jours"] - 15)
    elif scenario == "retards":
        st.session_state[cle("nb_retards_12m")] = int(min(12, base["nb_retards_12m"] + 3))
        st.session_state[cle("retard_moyen_jours")] = lo("retard_moyen_jours", base["retard_moyen_jours"] + 20)
        st.session_state[cle("incidents_bancaires_12m")] = int(min(12, base["incidents_bancaires_12m"] + 1))
    elif scenario == "desendettement":
        st.session_state[cle("encours")] = float(round(base["encours"] * 0.7 / 1000))
        st.session_state[cle("utilisation_decouvert_pct")] = lo("utilisation_decouvert_pct", base["utilisation_decouvert_pct"] - 25)
    elif scenario == "redressement":
        st.session_state[cle("nb_retards_12m")] = 0
        st.session_state[cle("retard_moyen_jours")] = 0.0
        st.session_state[cle("incidents_bancaires_12m")] = 0
        st.session_state[cle("tresorerie_jours")] = lo("tresorerie_jours", base["tresorerie_jours"] + 20)
        st.session_state[cle("utilisation_decouvert_pct")] = lo("utilisation_decouvert_pct", base["utilisation_decouvert_pct"] - 30)


titre_section("Scénarios rapides", "⚡")
b = st.columns(5)
for col, (code, texte) in zip(b, [("choc", "📉 Choc d'activité −20 %"), ("retards", "⏰ Retards en hausse"),
                                  ("desendettement", "🧩 Dette −30 %"), ("redressement", "🌱 Redressement"),
                                  ("init", "↺ Réinitialiser")]):
    col.button(texte, on_click=appliquer, args=(code,), width="stretch", key=f"sc_{code}",
               type="secondary" if code == "init" else "primary")

c1, c2 = st.columns([1, 1.15], gap="large")
with c1, panneau("curseurs"):
    titre_section("Situation simulée", "🎚️")
    simule = base.copy()
    for v, (mini, maxi, pas, fmt) in CURSEURS.items():
        if cle(v) not in st.session_state:
            st.session_state[cle(v)] = valeur_depart(v)
        val = st.slider(LIBELLES[v], min_value=mini, max_value=type(mini)(maxi), step=pas, format=fmt, key=cle(v))
        simule[v] = val * 1000 if v in EN_MILLIERS else val
    simule["ratio_endettement_pct"] = simule["encours"] / max(simule["ca_annuel"], 1) * 100
    st.caption(f"Ratio d'endettement recalculé : {nombre(simule['ratio_endettement_pct'])} % du CA "
               f"(au départ : {nombre(base['ratio_endettement_pct'])} %).")

ligne = simule.to_frame().T.infer_objects()
pd_new = float(proba_defaut(paquet, ligne)[0])
score_new = float(score_depuis_pd(pd_new))
niv_new = niveau(score_new)

with c2:
    with panneau("resultat"):
        titre_section("Score recalculé", "🎯", "▲▼ = écart avec la situation réelle")
        st.plotly_chart(g.jauge(score_new, float(base["score"]), hauteur=270), width="stretch", config=g.CONFIG)
        ecart = score_new - base["score"]
        st.markdown(f"""<div style="display:flex;gap:12px;justify-content:center;flex-wrap:wrap;margin-bottom:8px">
            <div class="pd-horizon" style="flex:1"><div class="h">Avant</div><div class="v">{base['score']:.0f}</div>{badge(str(base['niveau']))}</div>
            <div class="pd-horizon" style="flex:1"><div class="h">Après</div><div class="v" style="color:{'#FCA5A5' if ecart > 0.5 else '#86EFAC' if ecart < -0.5 else '#fff'}">{score_new:.0f}</div>{badge(niv_new)}</div>
            <div class="pd-horizon" style="flex:1"><div class="h">PD 12 mois</div><div class="v">{nombre(pd_new * 100, 1)} %</div>
            <span style="color:#9A93B5;font-size:.8rem">avant {nombre(base['pd12'] * 100, 1)} %</span></div></div>""",
                    unsafe_allow_html=True)
    with panneau("explication"):
        titre_section("Ce qui a fait bouger le score", "🧠")
        avant, _ = expliquer_client(df[df["id_client"] == id_client], float(base["score"]))
        apres, _ = expliquer_client(ligne, score_new)
        delta = apres - avant
        # On montre les variables modifiées ; le reste (effets indirects du modèle) est regroupé
        modifiees = [v for v in CURSEURS if abs(float(simule[v]) - float(base[v])) > 1e-6]
        if abs(simule["ratio_endettement_pct"] - base["ratio_endettement_pct"]) > 0.05:
            modifiees.append("ratio_endettement_pct")
        autres = delta.drop(modifiees).sum()
        delta = delta[modifiees]
        if abs(autres) > 0.05:
            delta["Effets indirects (autres variables)"] = autres
        if delta.abs().max() < 0.05:
            st.info("Bouge un curseur ou choisis un scénario pour voir son effet sur le score.")
        else:
            st.plotly_chart(g.barres_changement(delta), width="stretch", config=g.CONFIG)

aide("Le modèle ne connaît que les chiffres : il ne sait pas <b>pourquoi</b> un retard arrive. Les simulations donnent "
     "un ordre de grandeur pour discuter avec le client, pas une garantie.")
