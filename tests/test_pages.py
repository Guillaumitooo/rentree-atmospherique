"""Tests de fumée : chaque page Streamlit s'exécute sans exception."""
from dataclasses import replace
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from core.constantes import MISSION_LUNAIRE

RACINE = Path(__file__).resolve().parent.parent
PAGES = ["Accueil.py", "vues/0_Accueil.py", "vues/1_Mission_et_capsule.py", "vues/2_Simulation.py",
         "vues/3_Plan_d_experiences.py", "vues/4_Metamodeles.py", "vues/5_Prediction.py",
         "vues/6_Optimisation.py"]


def lancer(page: str) -> AppTest:
    return AppTest.from_file(str(RACINE / page), default_timeout=180)


@pytest.mark.parametrize("page", PAGES)
def test_page_sans_erreur(page):
    at = lancer(page).run()
    assert not at.exception


def test_prediction_hors_domaine_avertit():  # Review Focus 1
    at = lancer("vues/5_Prediction.py")
    at.session_state["mission"] = replace(MISSION_LUNAIRE, m_c=10_000.0)
    at.run()
    assert not at.exception
    assert any("domaine" in w.value for w in at.warning)


def test_optimisation_infaisable_message_clair():  # Review Focus 5
    at = lancer("vues/6_Optimisation.py")
    at.session_state["mission"] = replace(MISSION_LUNAIRE, n_lim=2.0)
    at.run()
    at.button[0].click().run()
    assert not at.exception
    assert at.error


def test_optimisation_verifiee_par_simulation():
    # Avec les marges par défaut, l'optimum et le front doivent être confirmés par la simulation
    at = lancer("vues/6_Optimisation.py").run()
    at.button[0].click().run()
    assert not at.exception
    assert any("confirme" in s.value for s in at.success)
    at.button[1].click().run()
    assert not at.exception
    assert not at.error


def test_simulation_differences_finies():
    at = lancer("vues/2_Simulation.py").run()
    at.radio[0].set_value("differences_finies").run()
    assert not at.exception
    assert any("Comparaison des modèles" in i.value for i in at.info)
