"""Page 6 : optimisation sur le métamodèle, puis vérification par simulation."""
from dataclasses import replace

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from core.constantes import Mission
from core.optimisation import optimiser_nsga2, optimiser_slsqp, verifier
from interface.commun import alertes_domaine, mission_courante, modeles_choisis, predicteur

st.set_page_config(page_title="Optimisation", page_icon="🚀", layout="wide")
st.title("6. Optimisation")

mission = mission_courante()
nom_reg, nom_clf = modeles_choisis()
st.caption(f"Mission : **{mission.nom}** (m_c = {mission.m_c:.0f} kg, D ≥ {mission.d_min:.1f} m, "
           f"n ≤ {mission.n_lim:.1f} g, T_s ≤ {mission.ts_lim_c:.0f} °C) · métamodèles : {nom_reg} / {nom_clf}")
alertes = alertes_domaine(mission)
for alerte in alertes:
    st.warning(f"⚠️ {alerte} Les solutions proposées ne sont pas fiables : seule la vérification par "
               "simulation fait foi.")

st.markdown(
    """
L'optimiseur cherche sur le **métamodèle** (rapide), puis chaque solution est **re-simulée**.
L'optimum se trouve toujours sur les limites : la moindre erreur du métamodèle peut alors le
faire déborder. On se garde donc une **marge de sécurité** sur les contraintes.
"""
)
c1, c2 = st.columns(2)
marge_n = c1.slider("Marge sur la décélération [g]", 0.0, 2.0, 0.5, 0.1)
marge_t = c2.slider("Marge sur la température de structure [°C]", 0.0, 50.0, 20.0, 5.0)
# Mission « durcie » utilisée par l'optimiseur ; la vérification se fait sur la vraie mission
mission_optim = replace(mission, n_lim=mission.n_lim - marge_n, ts_lim_c=mission.ts_lim_c - marge_t)

pred = predicteur(nom_reg, nom_clf)


@st.cache_data(show_spinner="Optimisation (criblage puis SLSQP)…")
def masse_minimale(_pred, cle_modeles: tuple, m_optim: Mission, m_reelle: Mission):
    r = optimiser_slsqp(_pred, m_optim)
    verif = verifier(pd.DataFrame([{**r.x, **r.predit}]), m_reelle) if r.succes else None
    return r, verif


@st.cache_data(show_spinner="Algorithme génétique NSGA-II…")
def front_pareto(_pred, cle_modeles: tuple, m_optim: Mission, m_reelle: Mission):
    front = optimiser_nsga2(_pred, m_optim)
    if front.empty:
        return front, None
    # 5 points répartis le long du front, re-simulés
    idx = np.unique(np.linspace(0, len(front) - 1, min(5, len(front))).round().astype(int))
    choisis = front.iloc[idx]
    sortie = _pred.predire(choisis.assign(m_c=m_reelle.m_c))
    verif = verifier(choisis.assign(T_s_C=sortie["T_s_C"].to_numpy()), m_reelle)
    return front, verif


onglet_masse, onglet_pareto = st.tabs(["Masse minimale", "Front de Pareto"])

with onglet_masse:
    if st.button("Lancer l'optimisation", type="primary"):
        st.session_state["optim_masse"] = True
    if st.session_state.get("optim_masse"):
        r, verif = masse_minimale(pred, (nom_reg, nom_clf), mission_optim, mission)
        if not r.succes:
            st.error(f"❌ {r.message}. Assouplissez la mission (décélération, température) ou réduisez les marges.")
        else:
            v = verif.iloc[0]
            k = st.columns(5)
            k[0].metric("Angle d'entrée", f"{r.x['gamma_deg']:.2f}°")
            k[1].metric("Diamètre", f"{r.x['D']:.2f} m")
            k[2].metric("R_n/D", f"{r.x['rn_sur_d']:.2f}")
            k[3].metric("Épaisseur", f"{100 * r.x['e']:.2f} cm")
            k[4].metric("Masse du bouclier", f"{r.m_b:.0f} kg")

            st.markdown("#### Vérification par simulation")
            ts_sim = v["T_s_C_sim"]

            def ok(condition: bool) -> str:
                return "✅" if condition else "❌"

            tableau = pd.DataFrame({
                "Métamodèle": [f"{100 * r.predit['p_rebond']:.1f} % de probabilité", f"{r.predit['n_max']:.2f}",
                               f"{r.predit['T_s_C']:.0f}", f"{100 * r.predit['e_res']:.2f}"],
                "Simulation": ["oui" if v["rebond_sim"] else "non", f"{v['n_max_sim']:.2f}",
                               "percé" if pd.isna(ts_sim) else f"{ts_sim:.0f}", f"{100 * v['e_res_sim']:.2f}"],
                "Écart": ["", f"{r.predit['n_max'] - v['n_max_sim']:+.2f}",
                          "" if pd.isna(ts_sim) else f"{r.predit['T_s_C'] - ts_sim:+.0f}",
                          f"{100 * (r.predit['e_res'] - v['e_res_sim']):+.2f}"],
                "Limite de la mission": ["aucun rebond", f"≤ {mission.n_lim:.1f}", f"≤ {mission.ts_lim_c:.0f}",
                                         "positive"],
                "Respectée": [ok(not v["rebond_sim"]), ok(v["n_max_sim"] <= mission.n_lim),
                              ok(not pd.isna(ts_sim) and ts_sim <= mission.ts_lim_c), ok(v["e_res_sim"] > 0)],
            }, index=["Rebond", "Décélération max [g]", "Température de structure [°C]",
                      "Épaisseur résiduelle [cm]"])
            st.table(tableau)
            if v["respecte"]:
                st.success("✅ La simulation confirme : toutes les contraintes de la mission sont respectées.")
            elif alertes:
                st.error("❌ La simulation **invalide** cette solution : le métamodèle extrapole hors de son "
                         "domaine (voir l'avertissement en haut de page). Revenez dans le domaine étudié.")
            else:
                st.error("❌ La simulation **invalide** cette solution : une contrainte est violée. "
                         "Augmentez les marges de sécurité.")

            notes = []
            if abs(r.x["D"] - mission.d_min) < 0.02:
                notes.append("**D est à son minimum habitable** : le bouclier pèse ∝ D², l'optimiseur réduit la "
                             "capsule autant que le volume habitable le permet.")
            if r.x["rn_sur_d"] > 1.48:
                notes.append("**R_n/D est à son maximum** : un nez plus émoussé réduit le flux "
                             "(q̇ ∝ 1/√R_n) ; la borne traduit la limite de stabilité de la capsule.")
            if notes:
                st.info("Optimum en butée — résultat normal, à expliquer :\n\n- " + "\n- ".join(notes))

with onglet_pareto:
    st.markdown(
        "Deux objectifs contradictoires : **alléger le bouclier** et **ménager l'équipage**. "
        "Chaque point du front est un compromis : on ne peut améliorer l'un sans dégrader l'autre."
    )
    if st.button("Calculer le front de Pareto"):
        st.session_state["optim_pareto"] = True
    if st.session_state.get("optim_pareto"):
        front, verif = front_pareto(pred, (nom_reg, nom_clf), mission_optim, mission)
        if front.empty:
            st.error("❌ Aucune solution ne respecte les contraintes de la mission.")
        else:
            fig = go.Figure([
                go.Scatter(x=front["n_max"], y=front["m_b"], mode="markers", name="front (métamodèle)",
                           customdata=np.column_stack([front["gamma_deg"], front["D"], 100 * front["e"]]),
                           hovertemplate="n = %{x:.2f} g<br>m_b = %{y:.0f} kg<br>γ = %{customdata[0]:.2f}°"
                                         "<br>D = %{customdata[1]:.2f} m<br>e = %{customdata[2]:.2f} cm"),
                go.Scatter(x=verif["n_max_sim"], y=verif["m_b"], mode="markers", name="re-simulés (vert = validé)",
                           marker=dict(symbol="circle-open", size=14, line=dict(width=2),
                                       color=np.where(verif["respecte"], "#2ca02c", "#d62728"))),
            ])
            fig.add_vline(x=mission.n_lim, line_dash="dash", line_color="red")
            fig.update_layout(xaxis_title="Décélération maximale n_max [g]",
                              yaxis_title="Masse du bouclier m_b [kg]", height=500)
            st.plotly_chart(fig, width="stretch")
            st.markdown("#### Points re-simulés")
            lisible = pd.DataFrame({
                "γ_E [°]": verif["gamma_deg"].round(2), "D [m]": verif["D"].round(2),
                "R_n/D": verif["rn_sur_d"].round(2), "e [cm]": (100 * verif["e"]).round(2),
                "m_b [kg]": verif["m_b"].round(0), "n_max simulé [g]": verif["n_max_sim"].round(2),
                "écart n_max [%]": verif["ecart_n_max_pct"].round(1), "T_s simulée [°C]": verif["T_s_C_sim"].round(0),
                "écart T_s [°C]": verif["ecart_T_s_C"].round(0),
                "validé": verif["respecte"].map({True: "✅", False: "❌"}),
            })
            st.dataframe(lisible, hide_index=True, width="stretch")
