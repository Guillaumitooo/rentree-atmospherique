"""Page 4 : entraîner et comparer les métamodèles."""
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from sklearn.inspection import permutation_importance

from core.constantes import PA
from core.metamodeles import (CIBLES, NOMS_CLASSIFIEUR, NOMS_REGRESSION, entrainer_classifieur,
                              entrainer_regression)
from interface.commun import CLASSIFIEUR_DEFAUT, REGRESSION_DEFAUT, charger_doe

st.set_page_config(page_title="Métamodèles", page_icon="🚀", layout="wide")
st.title("4. Métamodèles")

st.markdown(
    """
Un **métamodèle** apprend à reproduire le simulateur à partir des 2 000 essais : il répond en
une milliseconde au lieu de ~25 ms, ce qui permet d'explorer et d'optimiser. Les données sont
séparées en **80 % d'apprentissage** et **20 % de test** : les scores ci-dessous sont mesurés
sur des points que le modèle n'a jamais vus.
"""
)

df = charger_doe()
LIBELLES = {"n_max": "Décélération max [g]", "q_max_MW": "Flux max [MW/m²]", "Q_MJ": "Chaleur reçue [MJ/m²]",
            "t_ch": "Durée de chauffe [s]", "T_s_C": "Température de structure [°C]"}


@st.cache_resource(show_spinner="Apprentissage…")
def regression(cible: str, nom: str):
    return entrainer_regression(df, cible, nom)


@st.cache_resource(show_spinner="Apprentissage…")
def classification(nom: str):
    return entrainer_classifieur(df, nom)


@st.cache_data(show_spinner="Calcul de l'importance des variables…")
def importance(cible: str, nom: str) -> pd.DataFrame:
    r = regression(cible, nom)
    imp = permutation_importance(r.modele, r.X_test, r.y_test, n_repeats=5, random_state=0)
    return pd.DataFrame({"paramètre": PA, "importance": imp.importances_mean}).sort_values("importance")


onglet_reg, onglet_clf = st.tabs(["Régression (sans rebond)", "Classification du rebond"])

with onglet_reg:
    c1, c2 = st.columns(2)
    cible = c1.selectbox("Grandeur à prédire", CIBLES, format_func=lambda c: LIBELLES[c])
    nom = c2.selectbox("Modèle", NOMS_REGRESSION, index=NOMS_REGRESSION.index(REGRESSION_DEFAUT), key="nom_reg")
    r = regression(cible, nom)

    m = r.metriques
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("R²", f"{m['R2']:.4f}")
    k2.metric("RMSE", f"{m['RMSE']:.3g}")
    k3.metric("MAE", f"{m['MAE']:.3g}")
    k4.metric("Erreur max", f"{m['erreur_max']:.3g}")

    g1, g2 = st.columns(2)
    lim = [min(r.y_test.min(), r.y_pred.min()), max(r.y_test.max(), r.y_pred.max())]
    fig = go.Figure([go.Scatter(x=r.y_test, y=r.y_pred, mode="markers", opacity=0.6, name="points de test"),
                     go.Scatter(x=lim, y=lim, mode="lines", line_dash="dash", name="prédiction parfaite")])
    fig.update_layout(title="Graphe de parité", xaxis_title=f"Simulé — {LIBELLES[cible]}",
                      yaxis_title="Prédit", height=450)
    g1.plotly_chart(fig, use_container_width=True)
    imp = importance(cible, nom)
    g2.plotly_chart(px.bar(imp, x="importance", y="paramètre", orientation="h",
                           title="Importance des variables (permutation)").update_layout(height=450),
                    use_container_width=True)

    if cible == "t_ch":
        st.info("La durée de chauffe est la grandeur la plus difficile à apprendre : près du bord du rebond, "
                "la capsule ricoche et la chauffe peut durer plus de 1 000 s.")

    st.markdown("#### Comparaison des quatre modèles")
    if st.button("Comparer sur cette grandeur"):
        lignes = []
        for n in NOMS_REGRESSION:
            mm = regression(cible, n).metriques
            lignes.append({"modèle": n, "R²": mm["R2"], "RMSE": mm["RMSE"], "MAE": mm["MAE"],
                           "erreur max": mm["erreur_max"]})
        st.dataframe(pd.DataFrame(lignes).style.format(precision=4), hide_index=True, use_container_width=True)

    with st.expander("Modèle hybride utilisé pour la prédiction et l'optimisation"):
        st.markdown(
            """
Pour la température de structure, la prédiction finale **ne vient pas** de la régression directe
ci-dessus : le métamodèle prédit la chaleur reçue Q et la durée de chauffe t_ch, puis la
**formule physique du bouclier** calcule l'ablation et la température. C'est un modèle
**hybride IA + physique**. Avec le processus gaussien, il se trompe en moyenne de ~8 °C près de
la limite de 250 °C, contre ~11 °C pour la régression directe.
"""
        )

with onglet_clf:
    nom_clf = st.selectbox("Classifieur", NOMS_CLASSIFIEUR, index=NOMS_CLASSIFIEUR.index(CLASSIFIEUR_DEFAUT),
                           key="nom_clf")
    rc = classification(nom_clf)
    st.metric("Exactitude sur le jeu de test", f"{100 * rc.metriques['exactitude']:.2f} %")
    mc = rc.metriques["matrice_confusion"]
    st.markdown("**Matrice de confusion** (lignes : réalité, colonnes : prédiction)")
    st.table(pd.DataFrame(mc, index=["réel : pas de rebond", "réel : rebond"],
                          columns=["prédit : pas de rebond", "prédit : rebond"]))
    st.caption("En optimisation, on exige une probabilité de rebond prédite inférieure à 5 %.")

st.caption("Les modèles choisis ici sont utilisés par les pages Prédiction et Optimisation.")
