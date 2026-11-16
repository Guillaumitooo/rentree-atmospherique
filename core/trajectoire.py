"""Simulateur de rentrée atmosphérique balistique (spec §6.1 et §6.2).

Modèle : point matériel, Terre sphérique non tournante, atmosphère exponentielle,
sans portance. On intègre l'état (V, gamma, h, s) avec scipy.integrate.solve_ivp.
"""
from dataclasses import dataclass

import numpy as np
from scipy.integrate import solve_ivp

from core.bouclier import evaluer_bouclier, masse_bouclier
from core.constantes import (CD, G0, H_ECHELLE, K_SG, MATERIAU, MISSION_LUNAIRE, RHO0, RT,
                             T_MAX, V_FIN, Capsule, Materiau, Mission)


@dataclass
class Resultat:
    """Historique et bilan d'une rentrée (unités SI)."""
    t: np.ndarray          # temps [s]
    V: np.ndarray          # vitesse [m/s]
    gamma: np.ndarray      # pente de la trajectoire [rad]
    h: np.ndarray          # altitude [m]
    s: np.ndarray          # distance au sol [m]
    n: np.ndarray          # décélération [g]
    q: np.ndarray          # flux thermique au point d'arrêt [W/m²]
    rebond: bool           # la capsule est ressortie de l'atmosphère
    n_max: float
    q_max: float
    Q: float               # chaleur totale reçue [J/m²]
    t_ch: float            # durée de chauffe [s]
    e_abl: float           # épaisseur ablatée [m]
    e_res: float           # épaisseur résiduelle [m]
    T_s_C: float           # température de la structure [°C] (NaN si percement)
    percement: bool
    m_b: float             # masse du bouclier [kg]
    duree: float           # durée simulée [s]
    portee: float          # distance au sol parcourue [m]

    def resume(self) -> dict:
        """Grandeurs scalaires, dans les unités des colonnes du plan d'expériences."""
        return {
            "rebond": self.rebond,
            "n_max": self.n_max,
            "q_max_MW": self.q_max / 1e6,
            "Q_MJ": self.Q / 1e6,
            "t_ch": self.t_ch,
            "e_abl": self.e_abl,
            "e_res": self.e_res,
            "T_s_C": self.T_s_C,
            "percement": self.percement,
            "m_b": self.m_b,
            "duree": self.duree,
            "portee_km": self.portee / 1e3,
        }


def densite(h):
    """Masse volumique de l'air [kg/m³] (atmosphère exponentielle)."""
    return RHO0 * np.exp(-h / H_ECHELLE)


def simuler(capsule: Capsule, mission: Mission = MISSION_LUNAIRE, mat: Materiau = MATERIAU,
            modele_thermique: str = "erfc") -> Resultat:
    """Simule une rentrée et évalue le bouclier thermique (modèle "erfc" ou "differences_finies")."""
    aire = np.pi * capsule.D**2 / 4
    m_b = masse_bouclier(capsule.D, capsule.e, mat)
    m = capsule.m_c + m_b

    def equations(t, y):
        V, gam, h, _s = y
        g = G0 * (RT / (RT + h)) ** 2
        trainee = 0.5 * densite(h) * V**2 * CD * aire
        return [
            -trainee / m - g * np.sin(gam),
            (V / (RT + h) - g / V) * np.cos(gam),
            V * np.sin(gam),
            V * np.cos(gam) * RT / (RT + h),
        ]

    # Succès : la vitesse descend sous le seuil d'ouverture des parachutes
    def parachutes(t, y):
        return y[0] - V_FIN
    parachutes.terminal = True

    # Rebond : la capsule remonte au-dessus de l'altitude d'entrée
    def rebond(t, y):
        return y[2] - (mission.h_entree + 1.0)
    rebond.terminal = True
    rebond.direction = 1

    y0 = [mission.v_entree, np.radians(capsule.gamma_deg), mission.h_entree, 0.0]
    sol = solve_ivp(equations, (0.0, T_MAX), y0, events=[parachutes, rebond],
                    max_step=1.0, rtol=1e-7, atol=1e-6)

    t = sol.t
    V, gam, h, s = sol.y
    rho = densite(h)
    n = 0.5 * rho * V**2 * CD * aire / (m * G0)
    q = K_SG * np.sqrt(rho / capsule.rn) * V**3
    thermique = evaluer_bouclier(t, q, capsule.e, mat, modele_thermique)

    return Resultat(
        t=t, V=V, gamma=gam, h=h, s=s, n=n, q=q,
        rebond=len(sol.t_events[1]) > 0,
        n_max=float(n.max()), q_max=float(q.max()),
        Q=thermique["Q"], t_ch=thermique["t_ch"],
        e_abl=thermique["e_abl"], e_res=thermique["e_res"],
        T_s_C=thermique["T_s_C"], percement=thermique["percement"],
        m_b=float(m_b), duree=float(t[-1]), portee=float(s[-1]),
    )
