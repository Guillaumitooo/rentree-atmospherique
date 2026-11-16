"""Modèle du bouclier thermique (spec §6.3).

Le bouclier est un disque de diamètre D composé :
  - d'une couche d'ablateur d'épaisseur e, qui se consomme en absorbant la chaleur ;
  - d'une structure support de masse surfacique m_sup.
La chaleur qui traverse l'ablateur restant est estimée par la solution de la
conduction en milieu semi-infini (fonction erfc).

Ce module expose une interface unique (`evaluer_bouclier`) pour pouvoir le
remplacer plus tard par un calcul de conduction par différences finies.
"""
import numpy as np
from scipy.special import erfc

from core.constantes import MATERIAU, Materiau


def masse_bouclier(D: float, e: float, mat: Materiau = MATERIAU) -> float:
    """Masse du bouclier frontal [kg] : (rho·e + m_sup) × aire du disque."""
    aire = np.pi * D**2 / 4
    return (mat.rho * e + mat.m_sup) * aire


def temperature_structure(Q: float, t_ch: float, e: float, mat: Materiau = MATERIAU) -> dict:
    """Ablation et température de la structure à partir de la chaleur reçue.

    Q    : chaleur totale reçue au point d'arrêt [J/m²]
    t_ch : durée de la chauffe [s]
    e    : épaisseur initiale d'ablateur [m]
    """
    e_abl = Q / (mat.rho * mat.h_eff)       # épaisseur consommée par l'ablation
    e_res = e - e_abl                         # épaisseur qui reste pour isoler
    percement = bool(e_res <= 0)
    if percement:
        T_s_C = float("nan")                  # bouclier percé : température sans objet
    else:
        profondeur = 2 * np.sqrt(mat.alpha * max(t_ch, 1e-9))
        T_s = mat.t0 + (mat.t_pyro - mat.t0) * erfc(e_res / profondeur)
        T_s_C = float(T_s - 273.15)
    return {"e_abl": float(e_abl), "e_res": float(e_res), "T_s_C": T_s_C, "percement": percement}


def evaluer_bouclier(t: np.ndarray, q: np.ndarray, e: float, mat: Materiau = MATERIAU) -> dict:
    """Bilan thermique d'une rentrée à partir de l'historique du flux q(t) [W/m²]."""
    Q = float(np.trapezoid(q, t))
    chauffe = q > 0.05 * q.max()              # instants où le flux dépasse 5 % du maximum
    t_ch = float(t[chauffe][-1] - t[chauffe][0]) if chauffe.any() else 0.0
    return {"Q": Q, "t_ch": t_ch, **temperature_structure(Q, t_ch, e, mat)}
