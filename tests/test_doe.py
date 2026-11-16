"""Tests du plan d'expériences (spec §7.1)."""
from core.constantes import BORNES_DOE, PA
from core.doe import COLONNES_PE, simuler_plan, tirer_lhs


def test_lhs_bornes_et_colonnes():
    p = tirer_lhs(200)
    assert list(p.columns) == PA
    assert len(p) == 200
    for c, (lo, hi) in BORNES_DOE.items():
        assert p[c].between(lo, hi).all()


def test_simuler_plan_petit():
    df = simuler_plan(tirer_lhs(30, graine=1))
    assert set(PA + COLONNES_PE + ["faisable"]) <= set(df.columns)
    assert df["rebond"].any() and (~df["rebond"]).any()  # les deux classes existent
    assert not (df["faisable"] & df["rebond"]).any()
