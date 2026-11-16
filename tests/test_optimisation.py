"""Tests de l'optimisation et de la vérification (spec §7.5)."""
from dataclasses import replace

import pandas as pd
import pytest

from core.constantes import MISSION_LUNAIRE
from core.doe import CHEMIN_DOE
from core.metamodeles import entrainer_predicteur
from core.optimisation import optimiser_nsga2, optimiser_slsqp, verifier


@pytest.fixture(scope="module")
def pred():
    return entrainer_predicteur(pd.read_csv(CHEMIN_DOE), "Forêt aléatoire", "Forêt aléatoire")


def test_slsqp_respecte_bornes(pred):
    r = optimiser_slsqp(pred, MISSION_LUNAIRE)
    assert r.succes
    assert r.x["D"] >= MISSION_LUNAIRE.d_min - 1e-6
    assert -7.0 <= r.x["gamma_deg"] <= -4.5
    assert r.predit["n_max"] <= 10.0 + 1e-3


def test_slsqp_infaisable(pred):  # Review Focus 5
    r = optimiser_slsqp(pred, replace(MISSION_LUNAIRE, n_lim=2.0))
    assert r.succes is False
    assert r.message


def test_nsga2_front_non_domine(pred):
    f = optimiser_nsga2(pred, MISSION_LUNAIRE, pop=40, generations=20)
    assert len(f) >= 3
    for _, a in f.iterrows():
        domine = (f.m_b <= a.m_b) & (f.n_max <= a.n_max) & ((f.m_b < a.m_b) | (f.n_max < a.n_max))
        assert not domine.any()


def test_verifier_signale_rebond():  # Review Focus 2
    pts = pd.DataFrame([dict(gamma_deg=-4.6, D=3.0, rn_sur_d=1.2, e=0.03)])
    v = verifier(pts, MISSION_LUNAIRE)
    assert v.loc[0, "rebond_sim"]
    assert not v.loc[0, "respecte"]
