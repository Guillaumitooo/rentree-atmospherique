"""Tests de fumée : chaque page Streamlit s'exécute sans exception."""
from dataclasses import replace
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from core.constantes import MISSION_LUNAIRE

RACINE = Path(__file__).resolve().parent.parent
PAGES = ["Accueil.py", "vues/0_Accueil.py", "vues/1_Mission_et_capsule.py", "vues/2_Simulation.py",
         "vues/3_Plan_d_experiences.py", "vues/4_Metamodeles.py", "vues/5_Prediction.py"]


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
