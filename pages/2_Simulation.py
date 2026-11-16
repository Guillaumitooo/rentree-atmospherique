"""Page 2 : simuler une rentrée et valider le simulateur."""
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from core.constantes import CD, MISSION_LEO, Capsule, Mission
from core.trajectoire import simuler
from core.validation import n_max_allen_eggers, q_max_allen_eggers
from interface.commun import curseurs_capsule, mission_courante

st.set_page_config(page_title="Simulation", page_icon="🚀", layout="wide")
st.title("2. Simulation d'une rentrée")

mission = mission_courante()
capsule = curseurs_capsule("sim", m_c_fixe=mission.m_c)


@st.cache_data
def simulation(c: Capsule, m: Mission):
    return simuler(c, m)


@st.cache_data
def balayage_validation(D: float, rn_sur_d: float, e: float, m_c: float) -> pd.DataFrame:
    """Simulations en orbite basse de −1° à −7°, comparées à Allen-Eggers."""
    lignes = []
    for g in np.arange(-1.0, -7.01, -0.5):
        c = Capsule(g, D, rn_sur_d, e, m_c)
        r = simuler(c, MISSION_LEO)
        beta = (m_c + r.m_b) / (CD * np.pi * D**2 / 4)
        n_ae = n_max_allen_eggers(MISSION_LEO.v_entree, g)
        q_ae = q_max_allen_eggers(MISSION_LEO.v_entree, g, beta, c.rn)
        lignes.append({"γ_E [°]": g, "n_max simulé [g]": r.n_max, "n_max Allen-Eggers [g]": n_ae,
                       "écart n_max [%]": 100 * (n_ae - r.n_max) / r.n_max,
                       "q̇_max simulé [MW/m²]": r.q_max / 1e6, "q̇_max Allen-Eggers [MW/m²]": q_ae / 1e6,
                       "écart q̇_max [%]": 100 * (q_ae - r.q_max) / r.q_max})
    return pd.DataFrame(lignes)


onglet_sim, onglet_val = st.tabs(["Rentrée", "Validation (orbite basse)"])

with onglet_sim:
    r = simulation(capsule, mission)
    st.caption(f"Mission : **{mission.nom}** (V_E = {mission.v_entree:.0f} m/s)")

    if r.rebond:
        st.error("🔁 **Rebond** : la capsule ressort de l'atmosphère. Entrée trop rasante.")
    elif r.percement:
        st.error("🔥 **Percement** : l'ablateur est entièrement consommé.")
    elif r.n_max > mission.n_lim or r.T_s_C > mission.ts_lim_c:
        st.warning("⚠️ La rentrée aboutit mais viole une contrainte (décélération ou température).")
    else:
        st.success("✅ Rentrée **faisable** : toutes les contraintes sont respectées.")

    c1, c2, c3 = st.columns(3)
    c4, c5, c6 = st.columns(3)
    c1.metric("n_max", f"{r.n_max:.1f} g", delta=f"limite {mission.n_lim:.0f} g", delta_color="off")
    c2.metric("q̇_max", f"{r.q_max / 1e6:.2f} MW/m²")
    c3.metric("Chaleur reçue Q", f"{r.Q / 1e6:.0f} MJ/m²")
    c4.metric("Ablation", f"{r.e_abl * 100:.2f} cm")
    c5.metric("T structure", "percé" if r.percement else f"{r.T_s_C:.0f} °C",
              delta=f"limite {mission.ts_lim_c:.0f} °C", delta_color="off")
    c6.metric("Masse bouclier", f"{r.m_b:.0f} kg")

    fig = make_subplots(rows=2, cols=2, subplot_titles=(
        "Altitude en fonction de la vitesse", "Décélération", "Flux thermique au point d'arrêt",
        "Trajectoire (altitude / distance au sol)"))
    fig.add_trace(go.Scatter(x=r.V / 1e3, y=r.h / 1e3, name="h(V)"), 1, 1)
    fig.add_trace(go.Scatter(x=r.t, y=r.n, name="n(t)"), 1, 2)
    fig.add_hline(y=mission.n_lim, line_dash="dash", line_color="red", row=1, col=2)
    fig.add_trace(go.Scatter(x=r.t, y=r.q / 1e6, name="q̇(t)"), 2, 1)
    fig.add_trace(go.Scatter(x=r.s / 1e3, y=r.h / 1e3, name="h(s)"), 2, 2)
    fig.update_xaxes(title_text="V [km/s]", autorange="reversed", row=1, col=1)
    fig.update_yaxes(title_text="h [km]", row=1, col=1)
    fig.update_xaxes(title_text="t [s]", row=1, col=2)
    fig.update_yaxes(title_text="n [g]", row=1, col=2)
    fig.update_xaxes(title_text="t [s]", row=2, col=1)
    fig.update_yaxes(title_text="q̇ [MW/m²]", row=2, col=1)
    fig.update_xaxes(title_text="s [km]", row=2, col=2)
    fig.update_yaxes(title_text="h [km]", row=2, col=2)
    fig.update_layout(height=650, showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

    st.caption(f"Durée simulée {r.duree:.0f} s · chauffe {r.t_ch:.0f} s · portée {r.portee / 1e3:.0f} km")

with onglet_val:
    st.markdown(
        """
Les formules d'**Allen-Eggers** donnent n_max et q̇_max pour une rentrée balistique à pente
constante. On les compare au simulateur sur une **entrée d'orbite basse** (7,8 km/s), avec la
géométrie choisie dans la barre latérale.

**À retenir :** l'accord est bon pour les entrées raides, mais se dégrade pour les entrées
rasantes, où la gravité et la courbure de la trajectoire comptent. À 11 km/s (retour lunaire),
la formule se trompe d'un facteur 3 à 5 : d'où la nécessité du simulateur.
"""
    )
    val = balayage_validation(capsule.D, capsule.rn_sur_d, capsule.e, capsule.m_c)
    g1, g2 = st.columns(2)
    fig_n = go.Figure([
        go.Scatter(x=val["γ_E [°]"], y=val["n_max simulé [g]"], name="simulation", mode="lines+markers"),
        go.Scatter(x=val["γ_E [°]"], y=val["n_max Allen-Eggers [g]"], name="Allen-Eggers",
                   mode="lines", line_dash="dash"),
    ])
    fig_n.update_layout(title="Décélération maximale", xaxis_title="γ_E [°]", yaxis_title="n_max [g]")
    g1.plotly_chart(fig_n, use_container_width=True)
    fig_q = go.Figure([
        go.Scatter(x=val["γ_E [°]"], y=val["q̇_max simulé [MW/m²]"], name="simulation", mode="lines+markers"),
        go.Scatter(x=val["γ_E [°]"], y=val["q̇_max Allen-Eggers [MW/m²]"], name="Allen-Eggers",
                   mode="lines", line_dash="dash"),
    ])
    fig_q.update_layout(title="Flux thermique maximal", xaxis_title="γ_E [°]", yaxis_title="q̇_max [MW/m²]")
    g2.plotly_chart(fig_q, use_container_width=True)
    st.dataframe(val.style.format("{:.1f}"), use_container_width=True, hide_index=True)
