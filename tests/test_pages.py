"""Tests de fumée : chaque page Streamlit s'exécute sans exception."""
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

RACINE = Path(__file__).resolve().parent.parent
PAGES = ["Accueil.py", "pages/1_Mission_et_capsule.py", "pages/2_Simulation.py"]


def lancer(page: str) -> AppTest:
    return AppTest.from_file(str(RACINE / page), default_timeout=60)


@pytest.mark.parametrize("page", PAGES)
def test_page_sans_erreur(page):
    at = lancer(page).run()
    assert not at.exception
