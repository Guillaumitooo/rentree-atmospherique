"""Optimisation de la capsule sur le métamodèle, puis vérification par simulation (spec §7.5).

Variables : γ_E, D, R_n/D, e. La masse hors bouclier m_c est imposée par la mission.
Contraintes (toutes écrites « ≥ 0 ») :
  1. pas de rebond      : 0,05 − P(rebond) ≥ 0
  2. décélération       : n_lim − n_max ≥ 0
  3. température        : T_lim − T_s ≥ 0
  4. pas de percement   : e_res − 0,5 mm ≥ 0
"""
from dataclasses import dataclass

import numpy as np
import pandas as pd
from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.core.problem import Problem
from pymoo.optimize import minimize as pymoo_minimize
from scipy.optimize import minimize
from scipy.stats import qmc

from core.bouclier import masse_bouclier
from core.constantes import Capsule, Mission
from core.doe import est_faisable
from core.trajectoire import simuler

VARIABLES = ["gamma_deg", "D", "rn_sur_d", "e"]
D_MAX = 5.0               # diamètre maximal (coiffe du lanceur) [m]
P_REBOND_MAX = 0.05
E_RES_MIN = 5e-4          # marge minimale d'ablateur restant [m]
N_CRIBLAGE = 2000         # points tirés pour trouver de bons points de départ
TOLERANCE_RELATIVE = 1e-3 # dépassement toléré sur les contraintes normalisées en fin de SLSQP


@dataclass
class ResultatOptim:
    succes: bool
    x: dict
    m_b: float
    predit: dict
    message: str


def bornes_optim(mission: Mission) -> list[tuple]:
    return [(-7.0, -4.5), (mission.d_min, D_MAX), (0.5, 1.5), (0.01, 0.06)]


def bornes_valides(mission: Mission) -> bool:
    """Le domaine de recherche existe-t-il ? (D_min doit rester sous le diamètre maximal)"""
    return mission.d_min < D_MAX - 1e-6


def _entrees(X: np.ndarray, mission: Mission) -> pd.DataFrame:
    """Tableau de variables → DataFrame des 5 paramètres d'action (m_c de la mission)."""
    df = pd.DataFrame(np.atleast_2d(X), columns=VARIABLES)
    df["m_c"] = mission.m_c
    return df


def _contraintes_tableau(sortie: pd.DataFrame, mission: Mission) -> np.ndarray:
    """Contraintes (n points × 4), positives quand elles sont respectées."""
    ts = sortie["T_s_C"].to_numpy(dtype=float)
    c_ts = np.where(np.isnan(ts), -1e3, mission.ts_lim_c - ts)   # NaN = bouclier percé
    return np.column_stack([
        P_REBOND_MAX - sortie["p_rebond"].to_numpy(),
        mission.n_lim - sortie["n_max"].to_numpy(),
        c_ts,
        sortie["e_res"].to_numpy() - E_RES_MIN,
    ])


def contraintes(x, pred, mission: Mission) -> np.ndarray:
    """Valeurs des 4 contraintes pour un point x = [γ_E, D, R_n/D, e]."""
    return _contraintes_tableau(pred.predire(_entrees(x, mission)), mission)[0]


def _masse(x) -> float:
    return masse_bouclier(x[1], x[3])


def optimiser_slsqp(pred, mission: Mission, n_departs: int = 10, graine: int = 0) -> ResultatOptim:
    """Masse de bouclier minimale.

    1. Criblage : on évalue 2 000 points tirés au hasard avec le métamodèle (instantané).
    2. Affinage : SLSQP part des n_departs meilleurs points faisables.
    On garde la meilleure solution faisable rencontrée.
    """
    if not bornes_valides(mission):
        return ResultatOptim(False, {}, float("nan"), {},
                             f"Le diamètre minimal ({mission.d_min:.1f} m) ne laisse aucune marge "
                             f"sous le diamètre maximal ({D_MAX:.1f} m)")
    bornes = bornes_optim(mission)
    bas = np.array([b[0] for b in bornes])
    haut = np.array([b[1] for b in bornes])

    tirage = qmc.scale(qmc.LatinHypercube(d=4, seed=graine).random(N_CRIBLAGE), bas, haut)
    c_tirage = _contraintes_tableau(pred.predire(_entrees(tirage, mission)), mission)
    faisables = tirage[(c_tirage >= 0).all(axis=1)]
    if len(faisables) == 0:
        return ResultatOptim(False, {}, float("nan"), {},
                             "Aucune solution ne respecte les contraintes de la mission")

    masses = np.array([_masse(x) for x in faisables])
    departs = faisables[np.argsort(masses)[:n_departs]]
    meilleur, m_meilleur = departs[0], _masse(departs[0])

    # SLSQP travaille sur des variables normalisées entre 0 et 1 (mieux conditionné)
    def vers_x(u):
        return bas + u * (haut - bas)

    echelle = np.array([P_REBOND_MAX, mission.n_lim, mission.ts_lim_c, 0.01])
    for x0 in departs:
        res = minimize(
            lambda u: _masse(vers_x(u)) / 100.0,
            (x0 - bas) / (haut - bas),
            method="SLSQP",
            bounds=[(0.0, 1.0)] * 4,
            constraints=[{"type": "ineq", "fun": lambda u: contraintes(vers_x(u), pred, mission) / echelle}],
            options={"maxiter": 100, "ftol": 1e-6},
        )
        x = vers_x(np.clip(res.x, 0.0, 1.0))
        # SLSQP s'arrête « sur » les contraintes actives, à une précision numérique près :
        # on accepte un dépassement de 0,1 % de chaque limite (négligeable devant les marges).
        if (contraintes(x, pred, mission) / echelle >= -TOLERANCE_RELATIVE).all() and _masse(x) < m_meilleur:
            meilleur, m_meilleur = x, _masse(x)

    predit = pred.predire(_entrees(meilleur, mission)).iloc[0].to_dict()
    return ResultatOptim(True, dict(zip(VARIABLES, map(float, meilleur))), float(m_meilleur), predit,
                         "Solution trouvée sur le métamodèle : à vérifier par simulation")


class _ProblemeCapsule(Problem):
    """Problème bi-objectif pour pymoo : minimiser (m_b, n_max) sous les 4 contraintes."""

    def __init__(self, pred, mission: Mission):
        bornes = bornes_optim(mission)
        super().__init__(n_var=4, n_obj=2, n_ieq_constr=4,
                         xl=np.array([b[0] for b in bornes]), xu=np.array([b[1] for b in bornes]))
        self.pred, self.mission = pred, mission

    def _evaluate(self, X, out, *args, **kwargs):
        sortie = self.pred.predire(_entrees(X, self.mission))
        out["F"] = np.column_stack([sortie["m_b"].to_numpy(), sortie["n_max"].to_numpy()])
        out["G"] = -_contraintes_tableau(sortie, self.mission)   # pymoo attend G ≤ 0


def optimiser_nsga2(pred, mission: Mission, pop: int = 80, generations: int = 60,
                    graine: int = 0) -> pd.DataFrame:
    """Front de Pareto masse du bouclier / décélération (algorithme génétique NSGA-II)."""
    if not bornes_valides(mission):
        return pd.DataFrame(columns=VARIABLES + ["m_b", "n_max"])
    res = pymoo_minimize(_ProblemeCapsule(pred, mission), NSGA2(pop_size=pop),
                         ("n_gen", generations), seed=graine, verbose=False)
    if res.X is None:
        return pd.DataFrame(columns=VARIABLES + ["m_b", "n_max"])
    front = pd.DataFrame(np.atleast_2d(res.X), columns=VARIABLES)
    F = np.atleast_2d(res.F)
    front["m_b"], front["n_max"] = F[:, 0], F[:, 1]
    return front.drop_duplicates().sort_values("m_b").reset_index(drop=True)


def verifier(points: pd.DataFrame, mission: Mission) -> pd.DataFrame:
    """Re-simule chaque point et compare au métamodèle (« la physique vérifie »)."""
    lignes = []
    for _, p in points.iterrows():
        r = simuler(Capsule(p["gamma_deg"], p["D"], p["rn_sur_d"], p["e"], mission.m_c), mission)
        sim = r.resume()
        ligne = {**{v: p[v] for v in VARIABLES},
                 "n_max_sim": sim["n_max"], "T_s_C_sim": sim["T_s_C"], "e_res_sim": sim["e_res"],
                 "rebond_sim": sim["rebond"], "m_b": sim["m_b"]}
        ligne["ecart_n_max_pct"] = (100 * (p["n_max"] - sim["n_max"]) / sim["n_max"]
                                    if "n_max" in p else float("nan"))
        ligne["ecart_T_s_C"] = p["T_s_C"] - sim["T_s_C"] if "T_s_C" in p else float("nan")
        ligne["respecte"] = est_faisable(sim, mission)
        lignes.append(ligne)
    return pd.DataFrame(lignes)
