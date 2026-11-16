"""Page 1 : le système étudié, ses paramètres et la mission imposée."""
from dataclasses import replace

import numpy as np
import pandas as pd
import streamlit as st

from core.constantes import MISSION_LEO, MISSION_LUNAIRE
from interface.commun import definir_mission, mission_courante

st.set_page_config(page_title="Mission et capsule", page_icon="🚀", layout="wide")
st.title("1. Mission et capsule")


def schema_capsule(D: float, rn_sur_d: float) -> str:
    """Schéma SVG de la capsule vue de profil : bouclier (calotte) + corps conique."""
    echelle = 40.0                       # pixels par mètre
    cx, cy = 190.0, 130.0
    demi = D / 2 * echelle
    rn = rn_sur_d * D * echelle
    profondeur = rn - np.sqrt(max(rn**2 - demi**2, 0.0))
    longueur = 0.8 * D * echelle
    haut, bas = cy - demi, cy + demi
    return f"""
<svg viewBox="0 0 520 280" width="100%" xmlns="http://www.w3.org/2000/svg"
     style="color: currentColor; font-family: sans-serif; font-size: 12px">
  <path d="M {cx} {haut} L {cx + longueur} {cy - 0.3 * demi} L {cx + longueur} {cy + 0.3 * demi}
           L {cx} {bas} Z" fill="none" stroke="currentColor" stroke-width="2"/>
  <path d="M {cx} {haut} A {rn} {rn} 0 0 0 {cx} {bas}" fill="#e4572e" fill-opacity="0.35"
        stroke="#e4572e" stroke-width="4"/>
  <line x1="10" y1="{cy}" x2="{cx - profondeur - 12}" y2="{cy}"
        stroke="currentColor" stroke-width="1.5" marker-end="url(#fleche)"/>
  <text x="10" y="{cy - 8}">écoulement</text>
  <line x1="{cx + longueur + 20}" y1="{haut}" x2="{cx + longueur + 20}" y2="{bas}"
        stroke="currentColor" stroke-dasharray="4 3"/>
  <text x="{cx + longueur + 26}" y="{cy}">D = {D:.1f} m</text>
  <text x="{cx - profondeur - 40}" y="{bas + 22}" fill="#e4572e">bouclier, R_n = {rn_sur_d * D:.1f} m</text>
  <defs><marker id="fleche" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto">
    <path d="M0,0 L8,4 L0,8 Z" fill="currentColor"/></marker></defs>
</svg>"""


col_texte, col_schema = st.columns([3, 2])
with col_texte:
    st.markdown(
        """
On **dimensionne une capsule** pour une **mission imposée** : un retour lunaire balistique.
La capsule entre à **120 km** d'altitude ; la phase étudiée s'arrête à l'ouverture des parachutes
(V < 250 m/s).
"""
    )
    st.markdown("#### Paramètres d'action (ce que l'on conçoit)")
    st.table(pd.DataFrame({
        "Paramètre": ["Angle d'entrée γ_E", "Diamètre D", "Émoussement R_n/D", "Épaisseur d'ablateur e",
                      "Masse hors bouclier m_c"],
        "Domaine étudié": ["−7° à −4,5°", "2,5 à 5 m", "0,5 à 1,5", "1 à 6 cm", "3 à 8 t"],
        "Rôle": ["trajectoire (guidage)", "géométrie, D ≥ D_min habitable", "forme du bouclier (stabilité)",
                 "dimensionnement thermique", "paramètre de mission (fixé en optimisation)"],
    }))
    st.markdown("#### Paramètres d'évaluation (ce que l'on mesure)")
    st.table(pd.DataFrame({
        "Grandeur": ["Rebond", "Décélération max n_max", "Flux max q̇_max", "Chaleur reçue Q",
                     "Épaisseur résiduelle e_res", "Température de structure T_s", "Masse du bouclier m_b"],
        "Usage": ["contrainte : aucun rebond", "contrainte ≤ n_lim ; 2ᵉ objectif", "analyse",
                  "dimensionne l'ablation", "contrainte > 0 (pas de percement)", "contrainte ≤ T_lim",
                  "objectif à minimiser"],
    }))
with col_schema:
    st.markdown("#### Schéma")
    D_schema = st.slider("Diamètre du schéma [m]", 2.5, 5.0, 3.0, 0.1)
    rn_schema = st.slider("R_n/D du schéma", 0.5, 1.5, 1.2, 0.05)
    st.markdown(schema_capsule(D_schema, rn_schema), unsafe_allow_html=True)

st.markdown("### Paramètres de la mission")
m = mission_courante()
with st.form("mission"):
    choix = st.radio("Type de mission", ["Retour lunaire", "Orbite basse"],
                     index=0 if m.nom == "Retour lunaire" else 1, horizontal=True)
    c1, c2, c3, c4, c5 = st.columns(5)
    v_e = c1.number_input("Vitesse d'entrée [m/s]", 5000.0, 12000.0, float(m.v_entree), 100.0)
    m_c = c2.number_input("Masse hors bouclier [kg]", 1000.0, 15000.0, float(m.m_c), 100.0)
    d_min = c3.number_input("Diamètre min. habitable [m]", 2.0, 4.8, min(float(m.d_min), 4.8), 0.1)
    n_lim = c4.number_input("Décélération max [g]", 1.0, 20.0, float(m.n_lim), 0.5)
    ts_lim = c5.number_input("T structure max [°C]", 100.0, 500.0, float(m.ts_lim_c), 10.0)
    st.caption("Changer de type de mission remet sa vitesse d'entrée par défaut.")
    if st.form_submit_button("Appliquer"):
        base = MISSION_LUNAIRE if choix == "Retour lunaire" else MISSION_LEO
        if choix != m.nom:
            v_e = base.v_entree
        definir_mission(replace(base, v_entree=v_e, m_c=m_c, d_min=d_min, n_lim=n_lim, ts_lim_c=ts_lim))
        st.success("Mission mise à jour : elle s'applique à toutes les pages.")

m = mission_courante()
st.caption(f"Mission courante : **{m.nom}**, V_E = {m.v_entree:.0f} m/s, m_c = {m.m_c:.0f} kg, "
           f"D_min = {m.d_min:.1f} m, n ≤ {m.n_lim:.1f} g, T_s ≤ {m.ts_lim_c:.0f} °C")
if m.m_c > 8000 or m.m_c < 3000:
    st.warning("La masse choisie sort du domaine du plan d'expériences (3 à 8 t) : "
               "les métamodèles devront extrapoler.")
