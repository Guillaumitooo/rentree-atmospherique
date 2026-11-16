"""Tests des métamodèles (spec §7.3)."""
import numpy as np
import pandas as pd
import pytest

from core.constantes import PA
from core.doe import CHEMIN_DOE
from core.metamodeles import (entrainer_classifieur, entrainer_predicteur, entrainer_regression,
                              hors_domaine)


@pytest.fixture(scope="module")
def doe():
    return pd.read_csv(CHEMIN_DOE)


def test_regression_n_max_precise(doe):
    r = entrainer_regression(doe, "n_max", "Forêt aléatoire")
    assert r.metriques["R2"] > 0.90


def test_classifieur_rebond(doe):
    assert entrainer_classifieur(doe, "Forêt aléatoire").metriques["exactitude"] > 0.95


def test_regression_ignore_nan(doe):  # Review Focus 4
    r = entrainer_regression(doe, "T_s_C", "Polynôme degré 2")
    assert np.isfinite(r.y_pred).all()


def test_predicteur_colonnes_et_hybride(doe):
    p = entrainer_predicteur(doe, "Forêt aléatoire", "Forêt aléatoire")
    out = p.predire(doe[PA].head(5))
    assert {"p_rebond", "T_s_C", "m_b"} <= set(out.columns)
    assert out["p_rebond"].between(0, 1).all()


def test_predicteur_hybride_proche_du_simulateur(doe):
    # Modèle hybride : T_s calculée par la physique à partir de Q et t_ch prédits.
    # Sur des points faisables du plan, l'écart doit rester de l'ordre de quelques dizaines de °C.
    p = entrainer_predicteur(doe, "Forêt aléatoire", "Forêt aléatoire")
    ok = doe[doe["faisable"]].head(20)
    out = p.predire(ok[PA])
    assert np.nanmedian(np.abs(out["T_s_C"].to_numpy() - ok["T_s_C"].to_numpy())) < 40


def test_hors_domaine():  # Review Focus 1
    X = pd.DataFrame([dict(gamma_deg=-6, D=3, rn_sur_d=1.2, e=0.03, m_c=10_000)])
    assert hors_domaine(X)[0]
    X_ok = pd.DataFrame([dict(gamma_deg=-6, D=3, rn_sur_d=1.2, e=0.03, m_c=5_000)])
    assert not hors_domaine(X_ok)[0]
