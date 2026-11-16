"""Formules analytiques d'Allen-Eggers (1958) pour une rentrée balistique (spec §6.4).

Hypothèses : pente gamma constante, gravité négligée devant la traînée.
Valables pour les entrées raides et sous-orbitales : elles servent à valider le
simulateur sur un cas d'orbite basse, et montrent leurs limites à 11 km/s.
"""
import numpy as np

from core.constantes import G0, H_ECHELLE, K_SG


def n_max_allen_eggers(v_e: float, gamma_deg: float) -> float:
    """Décélération maximale [g] : V_E²·|sin γ| / (2·e·H·g0)."""
    return v_e**2 * abs(np.sin(np.radians(gamma_deg))) / (2 * np.e * H_ECHELLE * G0)


def q_max_allen_eggers(v_e: float, gamma_deg: float, beta: float, rn: float) -> float:
    """Flux maximal au point d'arrêt [W/m²] (Sutton-Graves + Allen-Eggers).

    beta : coefficient balistique m/(C_D·A) [kg/m²] ; rn : rayon de nez [m].
    """
    sin_g = abs(np.sin(np.radians(gamma_deg)))
    return K_SG * np.sqrt(beta * sin_g / (3 * H_ECHELLE * rn)) * v_e**3 * np.exp(-0.5)
