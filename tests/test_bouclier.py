"""Tests du modèle de bouclier thermique (spec §6.3)."""
import numpy as np
import pytest
from scipy.special import erfc

from core.constantes import MATERIAU
from core.bouclier import masse_bouclier, temperature_structure, evaluer_bouclier


def test_masse_bouclier():
    # (rho_b * e + m_sup) * pi D²/4  ≈ 214,2 kg
    assert masse_bouclier(3.0, 0.03) == pytest.approx((510 * 0.03 + 15) * np.pi * 9 / 4)


def test_temperature_structure_formule():
    r = temperature_structure(Q=1e8, t_ch=300.0, e=0.04)
    e_abl = 1e8 / (510 * 30e6)
    attendu = 300 + 600 * erfc((0.04 - e_abl) / (2 * np.sqrt(MATERIAU.alpha * 300))) - 273.15
    assert r["e_abl"] == pytest.approx(e_abl)
    assert r["T_s_C"] == pytest.approx(attendu)  # ≈ 44 °C
    assert r["percement"] is False


def test_temperature_decroit_avec_epaisseur():
    ts = [temperature_structure(2e8, 300.0, e)["T_s_C"] for e in (0.02, 0.03, 0.05)]
    assert ts[0] > ts[1] > ts[2]


def test_percement():  # Review Focus 4
    r = temperature_structure(Q=2e8, t_ch=300.0, e=0.005)
    assert r["percement"] is True
    assert np.isnan(r["T_s_C"])
    assert r["e_res"] <= 0


def test_evaluer_bouclier_integre_et_duree():
    t = np.linspace(0, 100, 1001)
    q = np.where((t >= 20) & (t <= 60), 1e6, 0.0)  # créneau de 40 s à 1 MW/m²
    r = evaluer_bouclier(t, q, 0.04)
    assert r["Q"] == pytest.approx(4e7, rel=0.01)
    assert r["t_ch"] == pytest.approx(40.0, abs=0.2)
