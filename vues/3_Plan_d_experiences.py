"""Page 3 : le plan d'expériences numérique et l'exploration des données."""
import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

from core.constantes import PA
from core.doe import simuler_plan, tirer_lhs
from interface.commun import charger_doe, mission_courante

st.set_page_config(page_title="Plan d'expériences", page_icon="🚀", layout="wide")
st.title("3. Plan d'expériences")

mission = mission_courante()
st.markdown(
    """
On remplace les essais physiques par des **simulations** : 2 000 capsules tirées par
**Latin Hypercube** (chaque paramètre est découpé en 2 000 tranches, chaque tranche est utilisée
une fois) sont simulées. Ces données servent ensuite à entraîner les métamodèles.
"""
)

# --- Choix des données -----------------------------------------------------------
source = st.radio("Données affichées", ["Plan de référence (2 000 points, retour lunaire)",
                                         "Petit plan personnalisé (mission courante)"], horizontal=True)
if source.startswith("Petit"):
    c1, c2 = st.columns([1, 3])
    n = c1.number_input("Nombre de points", 20, 200, 100, 10)
    if c2.button(f"Générer et simuler {n} points ({mission.nom})"):
        with st.spinner("Simulation en cours…"):
            st.session_state["doe_perso"] = simuler_plan(tirer_lhs(int(n), graine=np.random.randint(1e6)),
                                                         mission)
    if "doe_perso" not in st.session_state:
        st.info("Cliquez sur le bouton pour générer un plan.")
        st.stop()
    df = st.session_state["doe_perso"]
else:
    df = charger_doe()


# --- Classement des points -----------------------------------------------------------
def classe(ligne) -> str:
    if ligne["rebond"]:
        return "rebond"
    if ligne["n_max"] > mission.n_lim:
        return f"n > {mission.n_lim:.0f} g"
    if ligne["percement"] or ligne["T_s_C"] > mission.ts_lim_c:
        return "bouclier insuffisant"
    return "faisable"


df = df.assign(classe=df.apply(classe, axis=1))
compte = df["classe"].value_counts()
cols = st.columns(4)
for col, nom in zip(cols, ["faisable", "rebond", f"n > {mission.n_lim:.0f} g", "bouclier insuffisant"]):
    col.metric(nom, f"{compte.get(nom, 0)} points", f"{100 * compte.get(nom, 0) / len(df):.1f} %",
               delta_color="off")

st.download_button("Télécharger les données (CSV)", df.to_csv(index=False).encode("utf-8"),
                   "plan_experiences.csv", "text/csv")

onglet_couloir, onglet_distrib, onglet_corr, onglet_table = st.tabs(
    ["Couloir d'entrée", "Distributions", "Corrélations", "Tableau"])

couleurs = {"faisable": "#2ca02c", "rebond": "#1f77b4", f"n > {mission.n_lim:.0f} g": "#d62728",
            "bouclier insuffisant": "#ff7f0e"}

with onglet_couloir:
    st.markdown(
        "Chaque point est une capsule simulée. La **bande verte** est le couloir d'entrée : "
        "au-dessus, la capsule rebondit ; en dessous, la décélération est trop forte."
    )
    fig = px.scatter(df, x="gamma_deg", y="D", color="classe", color_discrete_map=couleurs, opacity=0.7,
                     hover_data=PA + ["n_max", "T_s_C", "m_b"],
                     labels={"gamma_deg": "Angle d'entrée γ_E [°]", "D": "Diamètre D [m]"})
    fig.update_layout(height=550)
    st.plotly_chart(fig, use_container_width=True)

with onglet_distrib:
    grandeur = st.selectbox("Grandeur", ["n_max", "q_max_MW", "Q_MJ", "t_ch", "T_s_C", "m_b", "e_abl"])
    st.plotly_chart(px.histogram(df[~df["rebond"]], x=grandeur, color="classe", color_discrete_map=couleurs,
                                 nbins=50, title=f"{grandeur} (points sans rebond)"),
                    use_container_width=True)

with onglet_corr:
    st.markdown("Corrélations linéaires entre paramètres d'action et résultats (points sans rebond).")
    cols_corr = PA + ["n_max", "q_max_MW", "Q_MJ", "t_ch", "T_s_C", "m_b"]
    corr = df[~df["rebond"]][cols_corr].corr()
    st.plotly_chart(px.imshow(corr, text_auto=".2f", color_continuous_scale="RdBu_r", zmin=-1, zmax=1,
                              aspect="auto"), use_container_width=True)
    st.caption("Rappel : corrélation ne veut pas dire causalité, et une relation non linéaire peut avoir "
               "une corrélation faible.")

with onglet_table:
    st.dataframe(df, use_container_width=True, height=450)
