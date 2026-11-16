"""Page d'accueil de l'application."""
import streamlit as st

st.set_page_config(page_title="Capsule de rentrée", page_icon="🚀", layout="wide")

st.title("🚀 Conception d'une capsule de rentrée atmosphérique")
st.subheader("Retour lunaire : enfiler l'aiguille à 11 km/s")

st.markdown(
    """
**Question technique.** Une capsule habitée revient de la Lune à 11 km/s. Elle doit entrer dans
l'atmosphère avec le bon angle : **trop rasante, elle rebondit** et repart dans l'espace ; **trop
raide, l'équipage dépasse 10 g**. Entre les deux, quel est le **bouclier thermique le plus léger**
qui garde la structure sous 250 °C ?
"""
)

st.markdown("### Démarche")
etapes = [
    ("1. Mission", "Système, paramètres d'action et d'évaluation"),
    ("2. Simulation", "Trajectoire, flux thermique, bouclier ; validation"),
    ("3. Plan d'expériences", "2 000 rentrées simulées (LHS)"),
    ("4. Métamodèles", "Régressions et classifieur du rebond"),
    ("5. Prédiction", "Réponse instantanée, comparée au simulateur"),
    ("6. Optimisation", "Masse minimale, front de Pareto, vérification"),
]
for col, (titre, texte) in zip(st.columns(len(etapes)), etapes):
    col.markdown(f"**{titre}**")
    col.caption(texte)

st.info("L'IA propose, la physique vérifie, l'ingénieur décide : chaque optimum est re-simulé.")

with st.expander("Limites du modèle"):
    st.markdown(
        """
- Point matériel, Terre sphérique **non tournante**, atmosphère **exponentielle**.
- Rentrée **balistique** (sans portance), coefficient de traînée constant (C_D = 1,4).
- Flux **convectif** au point d'arrêt (Sutton-Graves) ; le flux **radiatif**, non négligeable à
  11 km/s, est ignoré.
- Bouclier : ablation par chaleur effective, conduction en **milieu semi-infini**, surface
  interne à la température de pyrolyse pendant la chauffe, pas de « soak » après la rentrée.
- Bouclier frontal seul, assimilé à un disque de diamètre D.
"""
    )

st.caption("Projet GM5 — Optimisation de la conception avec l'IA — INSA Strasbourg")
