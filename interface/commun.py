"""État partagé entre les pages : mission courante, données en cache, curseurs."""
import pandas as pd
import streamlit as st

from core.constantes import BORNES_DOE, MISSION_LUNAIRE, Capsule, Mission
from core.doe import CHEMIN_DOE


def mission_courante() -> Mission:
    """Mission choisie sur la page 1 (retour lunaire par défaut)."""
    return st.session_state.get("mission", MISSION_LUNAIRE)


def definir_mission(m: Mission) -> None:
    st.session_state["mission"] = m


@st.cache_data
def charger_doe() -> pd.DataFrame:
    """Plan d'expériences de référence (pré-calculé, 2 000 points)."""
    return pd.read_csv(CHEMIN_DOE)


def curseurs_capsule(cle: str, m_c_fixe: float | None = None) -> Capsule:
    """Curseurs de la barre latérale pour choisir un point de conception.

    Si m_c_fixe est donné, la masse est imposée par la mission (pas de curseur).
    """
    b = BORNES_DOE
    st.sidebar.header("Conception de la capsule")
    gamma = st.sidebar.slider("Angle d'entrée γ_E [°]", *b["gamma_deg"], -5.8, 0.05, key=f"{cle}_gamma")
    D = st.sidebar.slider("Diamètre D [m]", *b["D"], 3.0, 0.1, key=f"{cle}_D")
    rn_sur_d = st.sidebar.slider("Émoussement R_n/D [-]", *b["rn_sur_d"], 1.2, 0.05, key=f"{cle}_rn")
    e_cm = st.sidebar.slider("Épaisseur d'ablateur e [cm]", b["e"][0] * 100, b["e"][1] * 100, 3.0, 0.1,
                             key=f"{cle}_e")
    if m_c_fixe is None:
        m_c = st.sidebar.slider("Masse hors bouclier m_c [kg]", *b["m_c"], 5000.0, 100.0, key=f"{cle}_mc")
    else:
        m_c = m_c_fixe
        st.sidebar.caption(f"Masse hors bouclier imposée par la mission : {m_c:,.0f} kg".replace(",", " "))
    return Capsule(gamma_deg=gamma, D=D, rn_sur_d=rn_sur_d, e=e_cm / 100, m_c=m_c)
