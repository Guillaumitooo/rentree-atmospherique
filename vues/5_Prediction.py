"""Page 5 : prédiction instantanée par le métamodèle, comparée au simulateur."""
import time

import pandas as pd
import streamlit as st

from core.constantes import PA
from core.metamodeles import hors_domaine
from core.trajectoire import simuler
from interface.commun import curseurs_capsule, mission_courante, modeles_choisis, predicteur

st.set_page_config(page_title="Prédiction", page_icon="🚀", layout="wide")
st.title("5. Prédiction")

mission = mission_courante()
capsule = curseurs_capsule("pred", m_c_fixe=mission.m_c)
nom_reg, nom_clf = modeles_choisis()
st.caption(f"Métamodèles : **{nom_reg}** (régression) et **{nom_clf}** (rebond) · mission : {mission.nom}")

X = pd.DataFrame([{c: getattr(capsule, c) for c in PA}])
if hors_domaine(X)[0]:
    st.warning("⚠️ Ce point sort du domaine du plan d'expériences : le métamodèle **extrapole**, "
               "sa prédiction n'est pas fiable. Seule la simulation fait foi.")
if mission.nom != "Retour lunaire" or mission.v_entree != 11_000.0:
    st.warning("⚠️ Les métamodèles ont été entraînés pour le retour lunaire à 11 km/s : "
               "hors domaine pour cette mission.")

pred = predicteur(nom_reg, nom_clf)
t0 = time.perf_counter()
p = pred.predire(X).iloc[0]
t_pred = time.perf_counter() - t0
t0 = time.perf_counter()
s = simuler(capsule, mission).resume()
t_sim = time.perf_counter() - t0

c1, c2 = st.columns(2)
c1.metric("Temps de prédiction", f"{1000 * t_pred:.1f} ms")
c2.metric("Temps de simulation", f"{1000 * t_sim:.1f} ms")


def fmt(v, f="{:.2f}"):
    return "—" if pd.isna(v) else f.format(v)


lignes = [
    ("Rebond", f"{100 * p['p_rebond']:.0f} % de probabilité", "oui" if s["rebond"] else "non", ""),
    ("Décélération max [g]", fmt(p["n_max"]), fmt(s["n_max"]), fmt(p["n_max"] - s["n_max"], "{:+.2f}")),
    ("Flux max [MW/m²]", fmt(p["q_max_MW"]), fmt(s["q_max_MW"]), fmt(p["q_max_MW"] - s["q_max_MW"], "{:+.3f}")),
    ("Chaleur reçue [MJ/m²]", fmt(p["Q_MJ"], "{:.1f}"), fmt(s["Q_MJ"], "{:.1f}"),
     fmt(p["Q_MJ"] - s["Q_MJ"], "{:+.1f}")),
    ("Épaisseur résiduelle [cm]", fmt(100 * p["e_res"]), fmt(100 * s["e_res"]),
     fmt(100 * (p["e_res"] - s["e_res"]), "{:+.2f}")),
    ("Température de structure [°C]", fmt(p["T_s_C"], "{:.0f}"), fmt(s["T_s_C"], "{:.0f}"),
     fmt(p["T_s_C"] - s["T_s_C"], "{:+.0f}")),
    ("Masse du bouclier [kg]", fmt(p["m_b"], "{:.0f}"), fmt(s["m_b"], "{:.0f}"), "exacte (formule)"),
]
st.table(pd.DataFrame(lignes, columns=["Grandeur", "Métamodèle", "Simulation", "Écart"]).set_index("Grandeur"))

if s["rebond"]:
    st.info("La simulation rebondit : les grandeurs thermiques prédites n'ont pas de sens (modèles appris "
            "sur les rentrées sans rebond).")
st.caption("L'IA propose, la physique vérifie : la colonne Simulation est la référence.")
