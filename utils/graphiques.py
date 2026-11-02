"""Tous les graphiques Plotly de l'application, avec le thème sombre violet."""
from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from utils.config import COULEURS_NIVEAU, GRIS, LIBELLES, NIVEAUX, SEUILS_SCORE, TEXTE, VIOLET

# Palette des séries (modèles, segments) : vérifiée lisible par les daltoniens sur fond sombre
SERIES = ["#A855F7", "#0EA5C6", "#EC4899", "#D97706", "#6366F1", "#059669"]
GRILLE = "rgba(168,85,247,0.10)"
POLICE = "Inter, sans-serif"


MOIS_COURTS = ["janv.", "févr.", "mars", "avr.", "mai", "juin", "juil.", "août", "sept.", "oct.", "nov.", "déc."]
MOIS = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre", "novembre", "décembre"]


def axe_mois(fig: go.Figure, dates) -> go.Figure:
    """Graduations de l'axe des dates en français (« oct. 26 »)."""
    d = sorted(pd.to_datetime(pd.Series(dates).unique()))
    fig.update_xaxes(tickmode="array", tickvals=d, ticktext=[f"{MOIS_COURTS[x.month - 1]} {x:%y}" for x in d])
    return fig


def _mois_long(dates) -> list[str]:
    return [f"{MOIS[x.month - 1]} {x.year}" for x in pd.to_datetime(dates)]


def theme(fig: go.Figure, hauteur: int = 360, legende: bool = True) -> go.Figure:
    fig.update_layout(
        template="plotly_dark", height=hauteur, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family=POLICE, color=TEXTE, size=13), margin=dict(l=10, r=24, t=30, b=10),
        separators=", ",
        colorway=SERIES, showlegend=legende,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0, bgcolor="rgba(0,0,0,0)", font=dict(color=GRIS)),
        hoverlabel=dict(bgcolor="#1C1630", bordercolor=VIOLET, font=dict(family=POLICE, color=TEXTE)),
        transition=dict(duration=600, easing="cubic-in-out"),
    )
    fig.update_xaxes(gridcolor=GRILLE, zeroline=False, linecolor=GRILLE, tickfont=dict(color=GRIS))
    fig.update_yaxes(gridcolor=GRILLE, zeroline=False, linecolor=GRILLE, tickfont=dict(color=GRIS))
    return fig


CONFIG = {"displayModeBar": False, "locale": "fr"}


# ------------------------------------------------------------------ jauge
def jauge(score: float, precedent: float | None = None, hauteur: int = 290) -> go.Figure:
    niv = NIVEAUX[int(np.digitize(score, SEUILS_SCORE))]
    coul = COULEURS_NIVEAU[niv]
    bornes = [0] + SEUILS_SCORE + [100]
    fig = go.Figure(go.Indicator(
        mode="gauge+number" + ("+delta" if precedent is not None else ""),
        value=score,
        number=dict(font=dict(size=54, family="Sora, Inter, sans-serif", color="#fff"), valueformat=".0f"),
        delta=dict(reference=precedent, valueformat=".1f", increasing=dict(color="#EF4444"),
                   decreasing=dict(color="#22C55E"), font=dict(size=16)) if precedent is not None else None,
        gauge=dict(
            axis=dict(range=[0, 100], tickwidth=0, tickcolor=GRIS, tickfont=dict(color=GRIS, size=11),
                      tickvals=bornes),
            bar=dict(color=coul, thickness=0.28, line=dict(color="#fff", width=1)),
            bgcolor="rgba(255,255,255,0.03)", borderwidth=0,
            steps=[dict(range=[bornes[i], bornes[i + 1]], color=COULEURS_NIVEAU[n] + "2E") for i, n in enumerate(NIVEAUX)],
            threshold=dict(line=dict(color="#fff", width=3), thickness=0.85, value=score),
        ),
        title=dict(text=f"<span style='color:{coul};font-size:15px'>● Risque {niv.lower()}</span>"),
    ))
    return theme(fig, hauteur).update_layout(margin=dict(l=25, r=25, t=50, b=5))


# ------------------------------------------------------------------ tableau de bord
def courbe_evolution(hist: pd.DataFrame) -> go.Figure:
    g = hist.groupby("mois").agg(score=("score", "mean"),
                                 eleve=("niveau", lambda s: s.isin(["Élevé", "Critique"]).mean() * 100)).reset_index()
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=g["mois"], y=g["eleve"], name="% clients en risque élevé ou critique",
                             mode="lines+markers", line=dict(color=VIOLET, width=3, shape="spline"),
                             marker=dict(size=8, color="#0B0B12", line=dict(color=VIOLET, width=2)),
                             fill="tozeroy", fillcolor="rgba(168,85,247,0.16)",
                             customdata=_mois_long(g["mois"]),
                             hovertemplate="%{customdata}<br><b>%{y:.1f} %</b> des clients<extra></extra>"))
    fig.update_yaxes(ticksuffix=" %", rangemode="tozero")
    axe_mois(fig, g["mois"])
    return theme(fig, 330, legende=False)


def courbe_score_moyen(hist: pd.DataFrame) -> go.Figure:
    g = hist.groupby("mois")["score"].mean().reset_index()
    fig = go.Figure(go.Scatter(x=g["mois"], y=g["score"], mode="lines", line=dict(color="#EC4899", width=2.5, shape="spline"),
                               fill="tozeroy", fillcolor="rgba(236,72,153,0.10)",
                               customdata=_mois_long(g["mois"]),
                               hovertemplate="%{customdata}<br>Score moyen <b>%{y:.1f}</b><extra></extra>"))
    axe_mois(fig, g["mois"])
    return theme(fig, 330, legende=False)


def donut(df: pd.DataFrame) -> go.Figure:
    comptes = df["niveau"].value_counts().reindex(NIVEAUX).fillna(0)
    fig = go.Figure(go.Pie(
        labels=comptes.index, values=comptes.values, hole=0.68, sort=False, direction="clockwise",
        marker=dict(colors=[COULEURS_NIVEAU[n] for n in comptes.index], line=dict(color="#0B0B12", width=3)),
        text=[f"{v / comptes.sum() * 100:.0f} %" if v / comptes.sum() > 0.04 else "" for v in comptes.values],
        textinfo="text", textfont=dict(color="#fff", size=12),
        hovertemplate="<b>%{label}</b><br>%{value} clients<extra></extra>",
    ))
    fig.add_annotation(text=f"<b style='font-size:30px'>{int(comptes.sum())}</b><br><span style='color:{GRIS}'>clients</span>",
                       showarrow=False, font=dict(family="Sora, Inter, sans-serif", color="#fff"))
    return theme(fig, 330).update_layout(legend=dict(orientation="v", y=0.5, x=1.0, yanchor="middle"))


def heatmap(df: pd.DataFrame) -> go.Figure:
    pivot = df.pivot_table(index="secteur", columns="region", values="score", aggfunc="mean")
    nb = df.pivot_table(index="secteur", columns="region", values="score", aggfunc="size")
    fig = go.Figure(go.Heatmap(
        z=pivot.values, x=pivot.columns, y=pivot.index, customdata=nb.reindex_like(pivot).values,
        colorscale=[[0, "#15121F"], [0.35, "#4C1D95"], [0.65, "#A855F7"], [1, "#F0ABFC"]],
        xgap=2, ygap=2, colorbar=dict(title=dict(text="Score", font=dict(color=GRIS)), tickfont=dict(color=GRIS), thickness=10),
        hovertemplate="<b>%{y}</b> · %{x}<br>Score moyen %{z:.1f}<br>%{customdata} clients<extra></extra>",
    ))
    fig.update_xaxes(tickangle=-35, showgrid=False)
    fig.update_yaxes(showgrid=False)
    return theme(fig, 420, legende=False)


# ------------------------------------------------------------------ fiche client
def cascade(contrib: pd.Series, score_ref: float, score: float, nb: int = 8) -> go.Figure:
    """Graphique en cascade SHAP : du score moyen au score du client."""
    c = contrib.reindex(contrib.abs().sort_values(ascending=False).index)
    principaux, reste = c.iloc[:nb], c.iloc[nb:].sum()
    libelles = [LIBELLES.get(k, k) for k in principaux.index]
    valeurs = list(principaux.values)
    if abs(reste) > 0.05:
        libelles.append("Autres facteurs")
        valeurs.append(reste)
    fig = go.Figure(go.Waterfall(
        orientation="h", measure=["absolute"] + ["relative"] * len(valeurs) + ["total"],
        y=["Score moyen du portefeuille"] + libelles + ["Score du client"],
        x=[score_ref] + valeurs + [score],
        text=[f"{score_ref:.0f}"] + [f"{v:+.1f}".replace(".", ",") for v in valeurs] + [f"{score:.0f}"], textposition="outside",
        textfont=dict(color=TEXTE), cliponaxis=False,
        connector=dict(line=dict(color="rgba(168,85,247,0.35)", width=1, dash="dot")),
        increasing=dict(marker=dict(color="#EF4444", line=dict(width=0))),
        decreasing=dict(marker=dict(color="#22C55E", line=dict(width=0))),
        totals=dict(marker=dict(color=VIOLET, line=dict(width=0))),
        hovertemplate="%{y}<br>%{x:+.1f} points<extra></extra>",
    ))
    fig.update_yaxes(autorange="reversed", showgrid=False)
    fig.update_xaxes(title=dict(text="Points de score de risque", font=dict(color=GRIS)))
    return theme(fig, 60 + 38 * (len(valeurs) + 2), legende=False)


def historique_paiements(p: pd.DataFrame) -> go.Figure:
    couleurs = {"À l'heure": "#22C55E", "En retard": "#F59E0B", "Impayé": "#EF4444"}
    fig = go.Figure()
    for statut, coul in couleurs.items():
        s = p[p["statut"] == statut]
        fig.add_trace(go.Bar(x=s["mois"], y=s["jours_retard"].where(s["jours_retard"] > 0, 0.8), name=statut,
                             marker=dict(color=coul, cornerradius=4), customdata=np.column_stack([[f"{v:,.0f}".replace(",", " ") for v in s["montant_echeance"]], s["jours_retard"], _mois_long(s["mois"])]),
                             hovertemplate="%{customdata[2]}<br>Échéance %{customdata[0]} €<br>Retard : %{customdata[1]} j<extra>" + statut + "</extra>"))
    inc = p[p["incident_bancaire"] == 1]
    fig.add_trace(go.Scatter(x=inc["mois"], y=[p["jours_retard"].max() * 1.1 + 4] * len(inc), mode="markers", name="Incident bancaire",
                             marker=dict(symbol="x", size=13, color="#C026D3", line=dict(width=2, color="#F0ABFC")),
                             customdata=_mois_long(inc["mois"]), hovertemplate="%{customdata}<br>Incident bancaire<extra></extra>"))
    fig.update_yaxes(title=dict(text="Jours de retard", font=dict(color=GRIS)), rangemode="tozero")
    axe_mois(fig, p["mois"])
    return theme(fig, 320).update_layout(barmode="overlay", bargap=0.35)


def courbe_score_client(h: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    bornes = [0] + SEUILS_SCORE + [100]
    for i, n in enumerate(NIVEAUX):
        fig.add_hrect(y0=bornes[i], y1=bornes[i + 1], fillcolor=COULEURS_NIVEAU[n], opacity=0.07, line_width=0)
    fig.add_trace(go.Scatter(x=h["mois"], y=h["score"], mode="lines+markers", line=dict(color=VIOLET, width=3, shape="spline"),
                             marker=dict(size=8, color=[COULEURS_NIVEAU[n] for n in h["niveau"]], line=dict(color="#0B0B12", width=2)),
                             customdata=_mois_long(h["mois"]), hovertemplate="%{customdata}<br>Score <b>%{y:.1f}</b><extra></extra>"))
    fig.update_yaxes(range=[0, max(100, h["score"].max() + 5)])
    axe_mois(fig, h["mois"])
    return theme(fig, 320, legende=False)


def barres_changement(delta: pd.Series) -> go.Figure:
    d = delta[delta.abs() > 0.05].sort_values()
    fig = go.Figure(go.Bar(
        x=d.values, y=[LIBELLES.get(k, k) for k in d.index], orientation="h",
        marker=dict(color=["#22C55E" if v < 0 else "#EF4444" for v in d.values], cornerradius=4),
        text=[f"{v:+.1f}".replace(".", ",") for v in d.values], textposition="outside", textfont=dict(color=TEXTE),
        cliponaxis=False, hovertemplate="%{y}<br>%{x:+.1f} points<extra></extra>",
    ))
    m = max(d.abs().max(), 1) * 1.25
    fig.update_xaxes(range=[-m if d.min() < 0 else -m * 0.1, m if d.max() > 0 else m * 0.1])
    fig.update_xaxes(title=dict(text="Effet sur le score (points)", font=dict(color=GRIS)), zeroline=True, zerolinecolor=GRIS)
    return theme(fig, max(220, 60 + 34 * len(d)), legende=False)


# ------------------------------------------------------------------ modèle
def courbes_roc(roc: dict, metriques: dict) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=[0, 1], y=[0, 1], mode="lines", name="Hasard (AUC 0,50)",
                             line=dict(color=GRIS, dash="dot", width=1.5)))
    for i, (nom, (fpr, tpr)) in enumerate(roc.items()):
        fig.add_trace(go.Scatter(x=fpr, y=tpr, mode="lines", name=f"{nom} (AUC {metriques[nom]['AUC-ROC']:.3f})".replace(".", ","),
                                 line=dict(color=SERIES[i], width=2.5),
                                 hovertemplate="Faux positifs %{x:.0%}<br>Vrais positifs %{y:.0%}<extra>" + nom + "</extra>"))
    fig.update_xaxes(title=dict(text="Taux de faux positifs", font=dict(color=GRIS)), tickformat=".0%")
    fig.update_yaxes(title=dict(text="Taux de vrais positifs (rappel)", font=dict(color=GRIS)), tickformat=".0%")
    return theme(fig, 420)


def matrice_confusion(cm: np.ndarray) -> go.Figure:
    etiquettes = [["Vrais négatifs", "Fausses alertes"], ["Défauts manqués", "Défauts détectés"]]
    texte = [[f"<b>{cm[i][j]}</b><br><span style='font-size:11px'>{etiquettes[i][j]}</span>" for j in range(2)] for i in range(2)]
    fig = go.Figure(go.Heatmap(
        z=cm, x=["Prédit : sain", "Prédit : défaut"], y=["Réel : sain", "Réel : défaut"], text=texte,
        texttemplate="%{text}", textfont=dict(size=18, color="#fff"), xgap=4, ygap=4, showscale=False,
        colorscale=[[0, "#1C1630"], [1, "#7C3AED"]], hovertemplate="%{y} · %{x}<br>%{z} clients<extra></extra>",
    ))
    fig.update_yaxes(autorange="reversed", showgrid=False)
    fig.update_xaxes(showgrid=False, side="top")
    return theme(fig, 340, legende=False)


def importance_shap(contrib: pd.DataFrame) -> go.Figure:
    imp = contrib.abs().mean().sort_values()
    fig = go.Figure(go.Bar(
        x=imp.values, y=[LIBELLES.get(k, k) for k in imp.index], orientation="h",
        marker=dict(color=imp.values, colorscale=[[0, "#4C1D95"], [1, "#E879F9"]], cornerradius=4),
        hovertemplate="%{y}<br>Impact moyen %{x:.3f}<extra></extra>",
    ))
    fig.update_xaxes(title=dict(text="Impact moyen sur la prédiction (|SHAP|)", font=dict(color=GRIS)))
    return theme(fig, 460, legende=False)


def nuage_shap(contrib: pd.DataFrame, X: pd.DataFrame) -> go.Figure:
    """« Beeswarm » SHAP : chaque point = un client ; couleur = valeur de la variable (bas → haut)."""
    ordre = contrib.abs().mean().sort_values().index
    rng = np.random.default_rng(0)
    fig = go.Figure()
    for i, var in enumerate(ordre):
        v = contrib[var].to_numpy()
        if var == "secteur":
            couleur, survol = "#6B6587", X[var].astype(str)
        else:
            couleur, survol = X[var].rank(pct=True).to_numpy(), X[var].round(1).astype(str)
        fig.add_trace(go.Scattergl(
            x=v, y=i + rng.uniform(-0.28, 0.28, len(v)), mode="markers", name=LIBELLES.get(var, var), showlegend=False,
            marker=dict(size=5, color=couleur, colorscale=[[0, "#6366F1"], [0.5, "#A855F7"], [1, "#EC4899"]], cmin=0, cmax=1,
                        opacity=0.8, showscale=(i == len(ordre) - 1),
                        colorbar=dict(title=dict(text="Valeur", font=dict(color=GRIS)), tickvals=[0, 1], ticktext=["basse", "haute"],
                                      tickfont=dict(color=GRIS), thickness=10)),
            text=survol, hovertemplate=LIBELLES.get(var, var) + " = %{text}<br>SHAP %{x:+.3f}<extra></extra>",
        ))
    fig.update_yaxes(tickvals=list(range(len(ordre))), ticktext=[LIBELLES.get(k, k) for k in ordre], showgrid=False)
    fig.update_xaxes(title=dict(text="← diminue le risque   |   augmente le risque →", font=dict(color=GRIS)),
                     zeroline=True, zerolinecolor=GRIS)
    return theme(fig, 520, legende=False)


def barres_metriques(metriques: dict) -> go.Figure:
    df = pd.DataFrame(metriques).T
    fig = go.Figure()
    for i, nom in enumerate(df.index):
        fig.add_trace(go.Bar(x=df.columns, y=df.loc[nom], name=nom, marker=dict(color=SERIES[i], cornerradius=4),
                             hovertemplate="%{x}<br><b>%{y:.3f}</b><extra>" + nom + "</extra>"))
    fig.update_yaxes(range=[0, 1], tickformat=".0%")
    return theme(fig, 340).update_layout(barmode="group", bargap=0.3, bargroupgap=0.08)


# ------------------------------------------------------------------ segmentation
def nuage_segments(df: pd.DataFrame, noms: dict) -> go.Figure:
    fig = go.Figure()
    for k in sorted(df["segment"].unique()):
        s = df[df["segment"] == k]
        fig.add_trace(go.Scatter(
            x=s["pc1"], y=s["pc2"], mode="markers", name=noms[k],
            marker=dict(size=8, color=SERIES[k % len(SERIES)], opacity=0.8, line=dict(color="#0B0B12", width=1)),
            customdata=s[["nom", "score", "secteur"]],
            hovertemplate="<b>%{customdata[0]}</b><br>%{customdata[2]}<br>Score %{customdata[1]:.0f}<extra>" + noms[k] + "</extra>",
        ))
    fig.update_xaxes(title=dict(text="Axe 1 (synthèse PCA)", font=dict(color=GRIS)), showticklabels=False)
    fig.update_yaxes(title=dict(text="Axe 2 (synthèse PCA)", font=dict(color=GRIS)), showticklabels=False)
    return theme(fig, 480)


def radar(profils: pd.DataFrame, noms: dict) -> go.Figure:
    fig = go.Figure()
    axes = [LIBELLES.get(c, c) for c in profils.columns]
    for k in profils.index:
        coul = SERIES[k % len(SERIES)]
        vals = list(profils.loc[k].values)
        fig.add_trace(go.Scatterpolar(r=vals + vals[:1], theta=axes + axes[:1], name=noms[k], fill="toself",
                                      line=dict(color=coul, width=2), fillcolor=coul + "22",
                                      hovertemplate="%{theta}<br>%{r:.0f}/100<extra>" + noms[k] + "</extra>"))
    fig.update_layout(polar=dict(bgcolor="rgba(0,0,0,0)",
                                 radialaxis=dict(range=[0, 100], gridcolor=GRILLE, tickfont=dict(color=GRIS, size=9), showline=False),
                                 angularaxis=dict(gridcolor=GRILLE, tickfont=dict(color=TEXTE, size=11), linecolor=GRILLE)))
    return theme(fig, 480)


def histogramme_scores(df: pd.DataFrame, seuil: float) -> go.Figure:
    fig = go.Figure()
    for n in NIVEAUX:
        s = df[df["niveau"] == n]
        fig.add_trace(go.Histogram(x=s["score"], name=n, marker=dict(color=COULEURS_NIVEAU[n]), xbins=dict(size=2.5),
                                   hovertemplate="Score %{x}<br>%{y} clients<extra>" + n + "</extra>"))
    fig.add_vline(x=seuil, line=dict(color="#fff", width=2, dash="dash"), annotation_text="seuil d'alerte",
                  annotation_font_color="#fff")
    fig.update_xaxes(title=dict(text="Score de risque", font=dict(color=GRIS)), range=[0, 100])
    return theme(fig, 300).update_layout(barmode="stack", bargap=0.08)
