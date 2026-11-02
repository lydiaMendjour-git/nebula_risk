"""Habillage : injection du CSS, en-têtes de page, cartes KPI, mise en forme des nombres."""
from __future__ import annotations

import html

import streamlit as st

from utils.config import COULEURS_NIVEAU, FICHIER_CSS, NOM_APP, SOUS_NOM

LOGO_SVG = """
<svg viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#C4B5FD"/><stop offset=".45" stop-color="#A855F7"/>
      <stop offset=".75" stop-color="#6366F1"/><stop offset="1" stop-color="#EC4899"/>
    </linearGradient>
    <radialGradient id="c"><stop offset="0" stop-color="#fff"/><stop offset=".4" stop-color="#E9D5FF"/><stop offset="1" stop-color="#A855F7" stop-opacity="0"/></radialGradient>
  </defs>
  <circle cx="32" cy="32" r="27" fill="none" stroke="url(#g)" stroke-width="2.2" stroke-dasharray="120 50" stroke-linecap="round"/>
  <ellipse cx="32" cy="32" rx="27" ry="10" fill="none" stroke="url(#g)" stroke-width="1.6" opacity=".75" transform="rotate(-28 32 32)"/>
  <ellipse cx="32" cy="32" rx="27" ry="10" fill="none" stroke="url(#g)" stroke-width="1.2" opacity=".45" transform="rotate(42 32 32)"/>
  <circle cx="32" cy="32" r="10" fill="url(#c)"/>
  <circle cx="54" cy="20" r="3" fill="#EC4899"/>
</svg>"""


def injecter_css() -> None:
    """Charge assets/style.css dans la page (une fois par page affichée)."""
    css = FICHIER_CSS.read_text(encoding="utf-8")
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


def intro() -> None:
    """Petit écran d'ouverture « wow », affiché une seule fois par visite."""
    if not st.session_state.get("_intro_vue"):
        st.session_state["_intro_vue"] = True
        st.markdown(f"""<div class="intro"><div class="bloc"><div class="nom">{NOM_APP}</div>
            <div class="s">{SOUS_NOM}</div></div></div>""", unsafe_allow_html=True)


def logo_sidebar() -> None:
    st.markdown(f"""<div class="logo">{LOGO_SVG}<div><div class="nom">{NOM_APP}</div>
        <div class="slogan">{SOUS_NOM}</div></div></div>""", unsafe_allow_html=True)


def banniere(page: str, icone: str, dernier_mois, nb_clients: int) -> None:
    """Grande bannière affichée en haut de chaque page : logo, nom de la plateforme, page en cours."""
    import pandas as pd
    st.markdown(f"""<div class="banniere">{LOGO_SVG.replace('id="g"', 'id="g2"').replace('url(#g)', 'url(#g2)').replace('id="c"', 'id="c2"').replace('url(#c)', 'url(#c2)')}
        <div class="marque"><div class="n">{NOM_APP}</div><div class="s">{SOUS_NOM}</div></div>
        <div class="sep"></div>
        <div class="ici"><span class="l">Vous êtes ici</span><span class="p">{icone}&nbsp; {page}</span></div>
        <div class="droite"><span class="pilule">📅 Données à fin {mois_fr(dernier_mois)}</span>
        <span class="pilule">👥 {nombre(nb_clients)} clients</span><span class="pilule fictif">🧪 Données fictives</span></div>
        </div>""", unsafe_allow_html=True)


def entete(surtitre: str, titre: str, sous_titre: str = "") -> None:
    st.markdown(f"""<div class="entete"><div class="surtitre">{surtitre}</div><h1>{titre}</h1>
        <div class="sous">{sous_titre}</div></div>""", unsafe_allow_html=True)


def titre_section(texte: str, icone: str = "✦", note: str = "") -> None:
    note_html = f'<span class="note">{note}</span>' if note else ""
    st.markdown(f'<div class="titre-section"><span class="ic">{icone}</span>{texte}{note_html}</div>',
                unsafe_allow_html=True)


def aide(texte: str) -> None:
    st.markdown(f'<div class="aide">💡 {texte}</div>', unsafe_allow_html=True)


def panneau(cle: str):
    """Conteneur en verre dépoli pour encadrer un graphique : `with panneau("x"): ...`"""
    return st.container(key=f"panneau_{cle}")


def kpis(cartes: list[dict]) -> None:
    """Affiche une rangée de cartes KPI animées.
    Chaque carte : {"libelle", "valeur", "unite", "icone", "delta", "sens" (bon/mauvais/neutre), "detail"}"""
    blocs = []
    for i, c in enumerate(cartes):
        delta = ""
        if c.get("delta"):
            delta = f'<span class="delta {c.get("sens", "neutre")}">{c["delta"]}</span>'
        detail = f'<span class="detail">{c.get("detail", "")}</span>' if c.get("detail") else ""
        unite = f'<small>{c["unite"]}</small>' if c.get("unite") else ""
        blocs.append(f"""<div class="kpi" style="animation-delay:{i * 0.09:.2f}s">
            <div class="haut"><span class="libelle">{c["libelle"]}</span><span class="icone">{c.get("icone", "◆")}</span></div>
            <div class="valeur{' texte' if c.get('texte') else ''}">{c["valeur"]}{unite}</div><div>{delta}{detail}</div></div>""")
    st.markdown(f'<div class="grille-kpi">{"".join(blocs)}</div>', unsafe_allow_html=True)


def badge(niveau: str) -> str:
    coul = COULEURS_NIVEAU.get(niveau, "#9A93B5")
    return (f'<span class="badge" style="color:{coul};background:{coul}22;border:1px solid {coul}66;'
            f'box-shadow:0 0 12px {coul}33">{html.escape(niveau)}</span>')


# ---------------------------------------------------------------- nombres à la française
def nombre(x: float, decimales: int = 0) -> str:
    return f"{x:,.{decimales}f}".replace(",", " ").replace(".", ",")


def euros(x: float) -> str:
    """12 400 000 → « 12,4 M€ » ; 845 000 → « 845 k€ »."""
    a = abs(x)
    if a >= 1e9:
        return f"{nombre(x / 1e9, 1)} Md€"
    if a >= 1e6:
        return f"{nombre(x / 1e6, 1)} M€"
    if a >= 1e3:
        return f"{nombre(x / 1e3, 0)} k€"
    return f"{nombre(x, 0)} €"


MOIS = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre", "novembre", "décembre"]
MOIS_COURTS = ["janv.", "févr.", "mars", "avr.", "mai", "juin", "juil.", "août", "sept.", "oct.", "nov.", "déc."]


def mois_fr(date) -> str:
    """Timestamp → « octobre 2026 »."""
    import pandas as pd
    d = pd.Timestamp(date)
    return f"{MOIS[d.month - 1]} {d.year}"


def pct(x: float, decimales: int = 1) -> str:
    return f"{nombre(100 * x, decimales)} %"
