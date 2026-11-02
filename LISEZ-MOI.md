# NEBULA · Risk Intelligence

Plateforme de Business Intelligence pour analyser le risque des clients en difficulté financière
(risque de défaut, retards de paiement, surendettement), avec du machine learning pour scorer,
prédire et expliquer le risque de chaque client.

> ⚠️ **Données 100 % fictives.** Les 1 200 entreprises sont inventées par `generer_donnees.py`.
> Ne mets jamais de vraies données clients du cabinet dans ce dossier, sur ton PC perso ou sur GitHub.

---

## 1. Installer (une seule fois)

Il faut **Python 3.11, 3.12 ou 3.13**. Pour vérifier, dans le terminal de VS Code :

```
py --version
```

1. Dézippe `nebula_risk.zip` (par exemple dans `Documents\nebula_risk`).
2. Dans VS Code : **Fichier › Ouvrir le dossier…** et choisis ce dossier.
3. Ouvre le terminal : **Terminal › Nouveau terminal**, puis tape :

```
py -m pip install -r requirements.txt
```

L'installation prend 2 à 5 minutes (XGBoost et SHAP sont un peu lourds).

## 2. Lancer l'application

Toujours dans le terminal de VS Code, dans le dossier du projet :

```
py -m streamlit run app.py
```

Le navigateur s'ouvre tout seul sur http://localhost:8501.
Pour arrêter : clique dans le terminal et fais `Ctrl + C`.

La toute première fois, si le modèle a été créé avec d'autres versions des bibliothèques
que les tiennes, l'application le réentraîne automatiquement (environ 10 secondes). C'est normal.

## 3. Les 7 pages

| Page | Ce qu'on y fait |
|---|---|
| 📊 **Tableau de bord** | Chiffres clés avec flèches d'évolution sur 30 jours, courbe du risque sur 12 mois, répartition par niveau, carte de chaleur secteur × région, alertes récentes |
| 👥 **Portefeuille clients** | Tableau interactif (barre de score, pastille de risque, mini-courbe sur 12 mois), filtres à gauche, recherche, clic sur une ligne pour ouvrir la fiche, export CSV |
| 🪪 **Fiche client** | Jauge du score, probabilité de défaut à 3, 6 et 12 mois, graphique en cascade SHAP « pourquoi ce score », actions recommandées, historique du score et des paiements, **fiche PDF** |
| 🧠 **Modèle ML** | Comparaison Régression logistique / Random Forest / XGBoost (AUC, précision, rappel, F1, courbes ROC, matrice de confusion), importance des variables SHAP, bouton **Réentraîner** avec barre de progression |
| 🎚️ **Simulateur what-if** | Curseurs pour changer la situation d'un client, scénarios en un clic (choc d'activité, retards, désendettement, redressement), score recalculé en direct et explication du changement |
| 🌌 **Segmentation** | K-Means de 3 à 6 groupes, carte 2D (PCA), profil type de chaque groupe en radar |
| 🚨 **Alertes & rapports** | Seuils réglables, liste des clients à surveiller avec le motif, export CSV (s'ouvre dans Excel) et **rapport PDF** |

### Comment lire le score

- Le modèle calcule la **probabilité de défaut à 12 mois** (PD).
- Le score de 0 à 100 est la racine carrée de cette probabilité × 100 : PD 4 % → score 20, PD 25 % → score 50, PD 64 % → score 80.
- Niveaux : 🟢 **Faible** < 25 · 🟠 **Modéré** 25 à 45 · 🔴 **Élevé** 45 à 65 · 🟣 **Critique** ≥ 65.
  (Seuils modifiables dans `utils/config.py`.)

## 4. Arborescence

```
nebula_risk/
├── app.py                      ← point d'entrée : menu de gauche + grande bannière
├── generer_donnees.py          ← crée les données fictives (py generer_donnees.py)
├── entrainer_modele.py         ← entraîne et compare les modèles (py entrainer_modele.py)
├── requirements.txt            ← bibliothèques à installer
├── LISEZ-MOI.md
├── .streamlit/config.toml      ← thème sombre (couleurs, polices)
├── assets/style.css            ← tout le style : verre dépoli, néons, animations
├── data/
│   ├── clients.csv             ← 1 200 clients, situation actuelle + cible "defaut"
│   ├── historique_mensuel.csv  ← situation de chaque client sur 12 mois
│   └── paiements.csv           ← échéances : à l'heure / en retard / impayé / incident
├── models/meilleur_modele.joblib
├── pages/
│   ├── 1_tableau_de_bord.py
│   ├── 2_portefeuille.py
│   ├── 3_fiche_client.py
│   ├── 4_modele_ml.py
│   ├── 5_simulateur.py
│   ├── 6_segmentation.py
│   └── 7_alertes_rapports.py
└── utils/
    ├── config.py               ← nom de l'app, couleurs, seuils, libellés  (à personnaliser)
    ├── donnees.py              ← chargement + calcul des scores (mis en cache)
    ├── modele.py               ← machine learning + SHAP
    ├── graphiques.py           ← tous les graphiques Plotly
    ├── style.py                ← bannière, cartes KPI, formats français
    ├── recommandations.py      ← règles d'actions recommandées (modifiables)
    └── rapport_pdf.py          ← rapports PDF
```

## 5. Personnaliser

- **Changer le nom** « NEBULA » : `utils/config.py`, lignes `NOM_APP` et `SOUS_NOM`.
- **Changer les seuils des niveaux** : `utils/config.py`, ligne `SEUILS_SCORE`.
- **Changer les actions recommandées** : `utils/recommandations.py` (une règle = un `if`).
- **Autres données fictives** : change `GRAINE` ou `NB_CLIENTS` en haut de `generer_donnees.py`,
  supprime les 3 CSV du dossier `data`, puis relance l'application.

Après une modification, enregistre le fichier puis clique sur **Rerun** en haut à droite de la page
(ou appuie sur `R`).

---

## 6. Mettre la plateforme en ligne (pour la voir « en vrai »)

Oui, c'est possible et gratuit avec **Streamlit Community Cloud**. Tu obtiens une adresse du type
`https://nebula-risk.streamlit.app` que tu peux ouvrir sur n'importe quel ordinateur ou téléphone.
Comme les données sont fictives, il n'y a pas de risque de confidentialité.

### Étape 1 : mettre le code sur GitHub (10 minutes)

1. Crée un compte gratuit sur https://github.com (si tu n'en as pas).
2. En haut à droite : **+ › New repository**. Nom : `nebula-risk`. Laisse **Public**
   (ou choisis **Private** si tu préfères que personne ne voie le code). Clique **Create repository**.
3. Sur la page du dépôt vide, clique sur **uploading an existing file**.
4. Ouvre le dossier `nebula_risk` dans l'Explorateur Windows, sélectionne **tout son contenu**
   (y compris le dossier `.streamlit`) et fais-le glisser dans la page GitHub.
   Clique **Commit changes**.
   - Si `.streamlit` n'a pas été envoyé, ce n'est pas grave : l'app marchera quand même,
     seul le thème Streamlit de base sera un peu différent (le style violet vient surtout de `assets/style.css`).

### Étape 2 : publier avec Streamlit (5 minutes)

1. Va sur https://share.streamlit.io et clique **Continue with GitHub**. Accepte l'autorisation.
2. Clique **Create app** › **Deploy a public app from GitHub**.
3. Remplis :
   - **Repository** : `ton-pseudo/nebula-risk`
   - **Branch** : `main`
   - **Main file path** : `app.py`
   - **App URL** : choisis un nom, par exemple `nebula-risk`
4. Ouvre **Advanced settings** et choisis **Python 3.12**.
5. Clique **Deploy**. La première installation prend 3 à 5 minutes, ensuite l'app s'affiche.

### Bon à savoir

- **Mettre à jour** : modifie ou ré-uploade un fichier sur GitHub, l'app en ligne se met à jour toute seule.
- **Qui peut la voir ?** Par défaut, toute personne qui a le lien. Pour la limiter :
  sur share.streamlit.io, menu **⋮ › Settings › Sharing**, puis invite les adresses e-mail autorisées.
- **Mise en veille** : une app gratuite s'endort après quelques jours sans visite.
  Il suffit de cliquer sur « Wake up » pour la relancer (30 secondes).
- **Jamais de vraies données** sur GitHub ou Streamlit Cloud : uniquement les données fictives.
  Pour de vraies données clients, il faudra un hébergement validé par le cabinet (serveur interne,
  ou offre entreprise avec authentification).
