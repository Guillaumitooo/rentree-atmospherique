"""Tests du simulateur de rentrée (spec §6.1 et §8)."""
import time

import numpy as np

from core.constantes import Capsule, MISSION_LUNAIRE, MISSION_LEO
from core.trajectoire import simuler

REF = dict(D=3.0, rn_sur_d=1.2, e=0.03, m_c=5000.0)


def test_rebond_lunaire_rasant():
    assert simuler(Capsule(-4.5, **REF), MISSION_LUNAIRE).rebond is True


def test_pas_de_rebond_lunaire_raide():
    r = simuler(Capsule(-6.5, **REF), MISSION_LUNAIRE)
    assert r.rebond is False
    assert r.V[-1] < 260


def test_pas_de_rebond_leo():
    assert simuler(Capsule(-1.0, **REF), MISSION_LEO).rebond is False


def test_vitesse_decroit():
    r = simuler(Capsule(-6.0, **REF), MISSION_LUNAIRE)
    assert r.V[-1] < r.V[0]
    assert r.h[-1] < r.h[0]


def test_ordre_de_grandeur_couloir():  # spec §2
    r = simuler(Capsule(-5.8, **REF), MISSION_LUNAIRE)
    assert 5.0 < r.n_max < 10.0
    assert 1.5e6 < r.q_max < 3e6


def test_frontiere_rebond_rapide_et_finie():  # Review Focus 3
    t0 = time.perf_counter()
    r = simuler(Capsule(-5.45, **REF), MISSION_LUNAIRE)
    assert time.perf_counter() - t0 < 2.0
    assert np.isfinite(r.n_max) and np.isfinite(r.Q)


def test_percement_propage():  # Review Focus 4
    r = simuler(Capsule(-5.6, 3.0, 1.2, 0.005, 5000.0), MISSION_LUNAIRE)
    assert r.percement is True
    assert np.isnan(r.resume()["T_s_C"])


def test_modele_thermique_transmis():
    c = Capsule(-5.8, **REF)
    r_erfc = simuler(c, MISSION_LUNAIRE)
    r_df = simuler(c, MISSION_LUNAIRE, modele_thermique="differences_finies")
    assert r_df.Q == r_erfc.Q
    assert r_df.T_s_C >= r_erfc.T_s_C - 5
