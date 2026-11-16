"""Modèle du bouclier thermique (spec §6.3).

Le bouclier est un disque de diamètre D composé :
  - d'une couche d'ablateur d'épaisseur e, qui se consomme en absorbant la chaleur ;
  - d'une structure support de masse surfacique m_sup.
La chaleur qui traverse l'ablateur restant est estimée par la solution de la
conduction en milieu semi-infini (fonction erfc).

Ce module expose une interface unique (`evaluer_bouclier`) pour pouvoir le
remplacer par un calcul de conduction par différences finies (modele="differences_finies").
"""
import numpy as np
from scipy.linalg import solve_banded
from scipy.special import erfc

MODELES_THERMIQUES = ["erfc", "differences_finies"]

from core.constantes import MATERIAU, Materiau


def masse_bouclier(D: float, e: float, mat: Materiau = MATERIAU) -> float:
    """Masse du bouclier frontal [kg] : (rho·e + m_sup) × aire du disque."""
    aire = np.pi * D**2 / 4
    return (mat.rho * e + mat.m_sup) * aire


def temperature_differences_finies(e_res: float, t_ch: float, mat: Materiau = MATERIAU,
                                   n_noeuds: int = 50, n_pas: int = 400) -> float:
    """Température de la face froide [K] par conduction 1D, schéma d'Euler implicite.

    Face chaude (x = 0) maintenue à T_pyro pendant t_ch ; face froide (x = e_res) adiabatique.
    Le schéma implicite est stable quel que soit le pas de temps.
    """
    dx = e_res / (n_noeuds - 1)
    dt = max(t_ch, 1e-9) / n_pas
    r = mat.alpha * dt / dx**2
    # Matrice tridiagonale au format « bandes » de scipy : lignes = sur-, diagonale, sous-diagonale
    bandes = np.zeros((3, n_noeuds))
    bandes[0, 1:] = -r
    bandes[1, :] = 1 + 2 * r
    bandes[2, :-1] = -r
    bandes[1, 0], bandes[0, 1] = 1.0, 0.0      # nœud 0 : température imposée
    bandes[2, -2] = -2 * r                      # dernier nœud : flux nul (nœud fantôme symétrique)
    T = np.full(n_noeuds, mat.t0)
    for _ in range(n_pas):
        second_membre = T.copy()
        second_membre[0] = mat.t_pyro
        T = solve_banded((1, 1), bandes, second_membre)
    return float(T[-1])


def temperature_structure(Q: float, t_ch: float, e: float, mat: Materiau = MATERIAU,
                          modele: str = "erfc", n_noeuds: int = 50) -> dict:
    """Ablation et température de la structure à partir de la chaleur reçue.

    Q      : chaleur totale reçue au point d'arrêt [J/m²]
    t_ch   : durée de la chauffe [s]
    e      : épaisseur initiale d'ablateur [m]
    modele : "erfc" (milieu semi-infini, analytique) ou "differences_finies" (conduction 1D numérique)
    """
    e_abl = Q / (mat.rho * mat.h_eff)       # épaisseur consommée par l'ablation
    e_res = e - e_abl                         # épaisseur qui reste pour isoler
    percement = bool(e_res <= 0)
    if percement:
        T_s_C = float("nan")                  # bouclier percé : température sans objet
    elif modele == "differences_finies":
        T_s_C = temperature_differences_finies(e_res, t_ch, mat, n_noeuds) - 273.15
    elif modele == "erfc":
        profondeur = 2 * np.sqrt(mat.alpha * max(t_ch, 1e-9))
        T_s = mat.t0 + (mat.t_pyro - mat.t0) * erfc(e_res / profondeur)
        T_s_C = float(T_s - 273.15)
    else:
        raise ValueError(f"Modèle thermique inconnu : {modele}")
    return {"e_abl": float(e_abl), "e_res": float(e_res), "T_s_C": T_s_C, "percement": percement}


def evaluer_bouclier(t: np.ndarray, q: np.ndarray, e: float, mat: Materiau = MATERIAU,
                     modele: str = "erfc") -> dict:
    """Bilan thermique d'une rentrée à partir de l'historique du flux q(t) [W/m²]."""
    Q = float(np.trapezoid(q, t))
    chauffe = q > 0.05 * q.max()              # instants où le flux dépasse 5 % du maximum
    t_ch = float(t[chauffe][-1] - t[chauffe][0]) if chauffe.any() else 0.0
    return {"Q": Q, "t_ch": t_ch, **temperature_structure(Q, t_ch, e, mat, modele)}
