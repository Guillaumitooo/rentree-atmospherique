"""Tests de fumée : chaque page Streamlit s'exécute sans exception."""
from dataclasses import replace
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from core.constantes import MISSION_LEO, MISSION_LUNAIRE

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
    masse = next(m for m in at.metric if m.label == "Masse du bouclier")
    assert float(masse.value.split()[0]) < 195  # optimum ~185 kg, pas le point de criblage (~222 kg)
    at.button[1].click().run()
    assert not at.exception
    assert not at.error


def test_simulation_differences_finies():
    at = lancer("vues/2_Simulation.py").run()
    at.radio[0].set_value("differences_finies").run()
    assert not at.exception
    assert any("Comparaison des modèles" in i.value for i in at.info)


def test_choix_modele_conserve_entre_pages():
    # Revue finale #2 : le modèle choisi page 4 doit survivre aux interactions sur les autres pages
    at = lancer("Accueil.py").run()
    at.switch_page("vues/4_Metamodeles.py").run()
    at.selectbox(key="nom_reg").set_value("Forêt aléatoire").run()
    at.switch_page("vues/5_Prediction.py").run()
    at.run()  # une interaction sur la page Prédiction
    assert not at.exception
    assert any("Forêt aléatoire" in c.value for c in at.caption)


@pytest.mark.parametrize("mission", [replace(MISSION_LEO), replace(MISSION_LUNAIRE, m_c=12_000.0),
                                     replace(MISSION_LUNAIRE, d_min=2.0)])
def test_optimisation_avertit_hors_domaine(mission):  # Revue finale #3
    at = lancer("vues/6_Optimisation.py")
    at.session_state["mission"] = mission
    at.run()
    assert not at.exception
    assert any("domaine" in w.value for w in at.warning)


def test_optimisation_d_min_maximal_sans_plantage():  # Revue finale #4
    at = lancer("vues/6_Optimisation.py")
    at.session_state["mission"] = replace(MISSION_LUNAIRE, d_min=5.0)
    at.run()
    at.button[0].click().run()
    assert not at.exception
    assert at.error


def test_verification_affiche_ecarts_et_respect():  # Revue finale (spec §7.5)
    at = lancer("vues/6_Optimisation.py").run()
    at.button[0].click().run()
    colonnes = list(at.table[0].value.columns)
    assert "Écart" in colonnes and "Respectée" in colonnes


def test_pas_de_parametre_streamlit_obsolete():
    # use_container_width est obsolète (supprimé après 2025-12-31) : il casserait les graphiques
    fichiers = [RACINE / "Accueil.py", *sorted((RACINE / "vues").glob("*.py"))]
    fautifs = [f.name for f in fichiers if "use_container_width" in f.read_text(encoding="utf-8")]
    assert fautifs == []


def test_mission_formulaire_appliquer():
    # Bug signalé en ligne : « Appliquer » levait StreamlitWidgetAlreadyInstantiatedError
    at = lancer("vues/1_Mission_et_capsule.py").run()
    at.number_input[1].set_value(6000.0)          # masse hors bouclier
    at.button[0].click().run()                    # bouton « Appliquer » du formulaire
    assert not at.exception
    assert at.session_state["mission"].m_c == 6000.0


def test_mission_formulaire_appliquer_deux_fois():
    # Bug n° 2 : le second « Appliquer » ignorait les champs modifiés
    at = lancer("vues/1_Mission_et_capsule.py").run()
    at.radio[0].set_value("Orbite basse")
    at.button[0].click().run()
    assert at.session_state["mission"].nom == "Orbite basse"
    assert at.session_state["mission"].v_entree == 7800.0
    at.radio[0].set_value("Retour lunaire")
    at.number_input[1].set_value(6500.0)
    at.button[0].click().run()
    assert not at.exception
    m = at.session_state["mission"]
    assert (m.nom, m.v_entree, m.m_c) == ("Retour lunaire", 11000.0, 6500.0)


def test_mission_formulaire_apres_aller_retour():
    at = lancer("Accueil.py").run()
    at.switch_page("vues/1_Mission_et_capsule.py").run()
    at.radio[0].set_value("Orbite basse")
    at.button[0].click().run()
    at.switch_page("vues/2_Simulation.py").run()
    at.switch_page("vues/1_Mission_et_capsule.py").run()
    assert not at.exception
    assert at.radio[0].value == "Orbite basse"
    assert at.number_input[0].value == 7800.0


def test_tableaux_optimisation_lisibles():
    at = lancer("vues/6_Optimisation.py").run()
    at.button[0].click().run()
    limites = at.table[0].value["Limite de la mission"].tolist()
    assert not any(str(v).lstrip().startswith(">") for v in limites)  # « > » = citation Markdown
    at.button[1].click().run()
    colonnes = list(at.dataframe[0].value.columns)
    assert "γ_E [°]" in colonnes and "gamma_deg" not in colonnes
