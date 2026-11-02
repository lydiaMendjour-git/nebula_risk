"""Création des rapports PDF (portefeuille et fiche client) avec fpdf2."""
from __future__ import annotations

import datetime as dt

import pandas as pd
from fpdf import FPDF

from utils.config import NOM_APP, SOUS_NOM

VIOLET = (124, 58, 237)
FONCE = (21, 18, 31)
GRIS = (110, 104, 135)
COUL_NIVEAU = {"Faible": (34, 197, 94), "Modéré": (245, 158, 11), "Élevé": (239, 68, 68), "Critique": (192, 38, 211)}


def _t(texte) -> str:
    """Les polices intégrées du PDF ne connaissent pas certains caractères : on les remplace."""
    rempl = {"€": "EUR", "–": "-", "—": "-", "’": "'", "…": "...", "→": "->", "≥": ">=", "≤": "<=", " ": " ", "\xa0": " "}
    s = str(texte)
    for a, b in rempl.items():
        s = s.replace(a, b)
    return s.encode("latin-1", "replace").decode("latin-1")


def _eur(x: float) -> str:
    return _t(f"{x:,.0f} €".replace(",", " "))


class _PDF(FPDF):
    titre = ""

    def header(self):
        self.set_fill_color(*FONCE)
        self.rect(0, 0, 210, 24, "F")
        self.set_fill_color(*VIOLET)
        self.rect(0, 24, 210, 1.2, "F")
        self.set_xy(12, 7)
        self.set_text_color(216, 180, 254)
        self.set_font("helvetica", "B", 15)
        self.cell(0, 6, _t(f"{NOM_APP}  ·  {SOUS_NOM}".replace("·", "-")))
        self.set_xy(12, 14)
        self.set_text_color(233, 230, 245)
        self.set_font("helvetica", "", 10)
        self.cell(0, 5, _t(self.titre))
        self.set_y(32)

    def footer(self):
        self.set_y(-12)
        self.set_font("helvetica", "I", 8)
        self.set_text_color(*GRIS)
        self.cell(0, 5, _t(f"Données fictives - généré le {dt.date.today():%d/%m/%Y} - page {self.page_no()}"), align="C")

    def section(self, texte):
        self.ln(3)
        self.set_text_color(*VIOLET)
        self.set_font("helvetica", "B", 12)
        self.cell(0, 7, _t(texte), new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(*VIOLET)
        self.line(self.l_margin, self.get_y(), 210 - self.r_margin, self.get_y())
        self.ln(2)
        self.set_text_color(30, 30, 30)

    def kpis(self, items):
        w = (210 - 24) / len(items)
        y = self.get_y()
        for i, (lib, val) in enumerate(items):
            x = 12 + i * w
            self.set_fill_color(245, 240, 255)
            self.set_draw_color(216, 180, 254)
            self.rect(x + 1, y, w - 2, 18, "DF")
            self.set_xy(x + 3, y + 2)
            self.set_font("helvetica", "", 7.5)
            self.set_text_color(*GRIS)
            self.cell(w - 6, 4, _t(lib.upper()))
            self.set_xy(x + 3, y + 7.5)
            self.set_font("helvetica", "B", 13)
            self.set_text_color(*VIOLET)
            self.cell(w - 6, 8, _t(val))
        self.set_y(y + 22)

    def tableau(self, entetes, lignes, largeurs, colonne_niveau=None):
        self.set_font("helvetica", "B", 8.5)
        self.set_fill_color(*FONCE)
        self.set_text_color(255, 255, 255)
        for e, w in zip(entetes, largeurs):
            self.cell(w, 7, _t(e), border=0, fill=True)
        self.ln()
        self.set_font("helvetica", "", 8.5)
        for k, ligne in enumerate(lignes):
            if self.get_y() > 275:
                self.add_page()
            self.set_fill_color(*((248, 246, 253) if k % 2 == 0 else (255, 255, 255)))
            for j, (v, w) in enumerate(zip(ligne, largeurs)):
                if colonne_niveau is not None and j == colonne_niveau:
                    self.set_text_color(*COUL_NIVEAU.get(v, (30, 30, 30)))
                    self.set_font("helvetica", "B", 8.5)
                else:
                    self.set_text_color(30, 30, 30)
                    self.set_font("helvetica", "", 8.5)
                self.cell(w, 6.2, _t(v)[: int(w / 1.75)], fill=True)
            self.ln()


def rapport_portefeuille(df: pd.DataFrame, alertes: pd.DataFrame, seuils: dict) -> bytes:
    pdf = _PDF()
    pdf.titre = f"Rapport de risque du portefeuille - situation au {pd.Timestamp(df.attrs.get('dernier_mois', dt.date.today())):%m/%Y}"
    pdf.set_auto_page_break(True, 15)
    pdf.add_page()
    risque = df["niveau"].isin(["Élevé", "Critique"])
    pdf.kpis([("Clients suivis", f"{len(df)}"), ("En risque élevé", f"{risque.mean():.1%}".replace(".", ",")),
              ("Encours à risque", _t(f"{df.loc[risque, 'encours'].sum() / 1e6:.1f} M€".replace(".", ","))),
              ("Défaut prédit", f"{df['pd12'].mean():.1%}".replace(".", ",")), ("Alertes", f"{len(alertes)}")])

    pdf.section("Répartition par niveau de risque")
    rep = df.groupby("niveau", observed=False).agg(n=("id_client", "size"), enc=("encours", "sum"), pd=("pd12", "mean"))
    pdf.tableau(["Niveau", "Clients", "Part", "Encours", "PD 12 mois moyenne"],
                [[str(n), f"{int(r.n)}", f"{r.n / len(df):.1%}", _eur(r.enc), f"{r.pd:.1%}"] for n, r in rep.iterrows()],
                [40, 25, 25, 50, 46], colonne_niveau=0)

    pdf.section("Seuils d'alerte utilisés")
    pdf.set_font("helvetica", "", 9.5)
    for k, v in seuils.items():
        pdf.cell(0, 5.5, _t(f"-  {k} : {v}"), new_x="LMARGIN", new_y="NEXT")

    pdf.section(f"Clients à surveiller ({len(alertes)})")
    lignes = [[r.id_client, r.nom, r.secteur, f"{r.score:.0f}",
               f"{r.variation_30j:+.1f}" if pd.notna(r.variation_30j) else "-", f"{r.pd12:.1%}", _eur(r.encours), str(r.niveau)]
              for r in alertes.head(60).itertuples()]
    pdf.tableau(["ID", "Client", "Secteur", "Score", "Var. 30 j", "PD 12 m", "Encours", "Niveau"], lignes,
                [18, 56, 24, 14, 17, 17, 22, 18], colonne_niveau=7)
    if len(alertes) > 60:
        pdf.set_font("helvetica", "I", 8)
        pdf.cell(0, 6, _t(f"... et {len(alertes) - 60} autres clients (voir l'export CSV)."))
    return bytes(pdf.output())


def fiche_client(c: pd.Series, horizons: dict, contrib: pd.Series, recos: list[dict]) -> bytes:
    pdf = _PDF()
    pdf.titre = f"Fiche risque - {c['nom']} ({c['id_client']})"
    pdf.add_page()
    pdf.kpis([("Score de risque", f"{c['score']:.0f} / 100"), ("Niveau", str(c["niveau"])),
              ("PD 3 mois", f"{horizons[3]:.1%}"), ("PD 6 mois", f"{horizons[6]:.1%}"), ("PD 12 mois", f"{horizons[12]:.1%}")])
    pdf.section("Identité et chiffres clés")
    infos = [("Secteur", c["secteur"]), ("Région", c["region"]), ("Ancienneté", f"{c['anciennete_ans']:.0f} ans"),
             ("Chiffre d'affaires", _eur(c["ca_annuel"])), ("Évolution du CA", f"{c['evolution_ca_pct']:+.1f} %"),
             ("Encours de dette", _eur(c["encours"])), ("Ratio d'endettement", f"{c['ratio_endettement_pct']:.0f} %"),
             ("Trésorerie", f"{c['tresorerie_jours']:.0f} jours de CA"), ("Retards (12 mois)", f"{int(c['nb_retards_12m'])}"),
             ("Incidents bancaires (12 mois)", f"{int(c['incidents_bancaires_12m'])}")]
    pdf.tableau(["Indicateur", "Valeur"], [[a, str(b)] for a, b in infos], [90, 96])
    pdf.section("Principaux facteurs de risque (SHAP, en points de score)")
    from utils.config import LIBELLES
    top = contrib.reindex(contrib.abs().sort_values(ascending=False).index).head(6)
    pdf.tableau(["Facteur", "Effet"], [[LIBELLES.get(k, k), f"{v:+.1f} points"] for k, v in top.items()], [120, 66])
    pdf.section("Actions recommandées")
    for r in recos:
        pdf.set_font("helvetica", "B", 10)
        pdf.set_text_color(*VIOLET)
        pdf.cell(0, 6, _t(f"[{r['priorite']}]  {r['titre']}"), new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("helvetica", "", 9.5)
        pdf.set_text_color(40, 40, 40)
        pdf.multi_cell(0, 5, _t(r["detail"]), new_x="LMARGIN", new_y="NEXT")
        pdf.ln(1)
    return bytes(pdf.output())
