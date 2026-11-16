"""Validation du simulateur par les formules d'Allen-Eggers (spec §6.4)."""
import numpy as np
import pytest

from core.constantes import CD, MISSION_LEO, Capsule
from core.trajectoire import simuler
from core.validation import n_max_allen_eggers, q_max_allen_eggers


def test_formule_n_max():
    assert n_max_allen_eggers(7800.0, -6.0) == pytest.approx(16.6, rel=0.02)


def test_accord_simulation_leo_raide():
    c = Capsule(-6.0, 3.0, 1.0, 0.04, 3000.0)
    r = simuler(c, MISSION_LEO)
    assert r.n_max == pytest.approx(n_max_allen_eggers(7800.0, -6.0), rel=0.15)
    beta = (c.m_c + r.m_b) / (CD * np.pi * c.D**2 / 4)
    assert r.q_max == pytest.approx(q_max_allen_eggers(7800.0, -6.0, beta, c.rn), rel=0.10)
