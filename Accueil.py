"""Point d'entrée de l'application : menu de navigation entre les pages."""
import streamlit as st

st.set_page_config(page_title="Capsule de rentrée", page_icon="🚀", layout="wide")

PAGES = [
    st.Page("vues/0_Accueil.py", title="Accueil", icon="🏠", default=True),
    st.Page("vues/1_Mission_et_capsule.py", title="1. Mission et capsule", icon="🛰️"),
    st.Page("vues/2_Simulation.py", title="2. Simulation", icon="📈"),
    st.Page("vues/3_Plan_d_experiences.py", title="3. Plan d'expériences", icon="🎲"),
    st.Page("vues/4_Metamodeles.py", title="4. Métamodèles", icon="🧠"),
    st.Page("vues/5_Prediction.py", title="5. Prédiction", icon="⚡"),
]

st.navigation(PAGES).run()
