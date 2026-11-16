"""Toutes les constantes du projet : physique, matériau du bouclier, missions, domaine d'étude.

Unités SI partout (m, s, kg, K, W/m², J/m²).
"""
from dataclasses import dataclass

# --- Terre et atmosphère ---------------------------------------------------
RT = 6_371e3          # rayon terrestre [m]
G0 = 9.81             # gravité au sol [m/s²]
RHO0 = 1.225          # masse volumique de l'air au sol [kg/m³]
H_ECHELLE = 7_200.0   # hauteur d'échelle de l'atmosphère exponentielle [m]

# --- Aérothermodynamique -----------------------------------------------------
K_SG = 1.7415e-4      # constante de Sutton-Graves pour l'air (SI)
CD = 1.4              # coefficient de traînée de la capsule (constant)

# --- Fin de la simulation ------------------------------------------------------
V_FIN = 250.0         # ouverture des parachutes quand V < V_FIN [m/s]
T_MAX = 3_000.0       # garde-fou sur la durée simulée [s]


@dataclass(frozen=True)
class Materiau:
    """Ablateur dense type Apollo/Orion + structure support."""
    rho: float = 510.0       # masse volumique [kg/m³]
    k: float = 0.3           # conductivité [W/(m·K)]
    cp: float = 1500.0       # capacité thermique [J/(kg·K)]
    m_sup: float = 15.0      # masse surfacique de la structure support [kg/m²]
    h_eff: float = 30e6      # chaleur effective d'ablation [J/kg]
    t_pyro: float = 900.0    # température du front de pyrolyse [K]
    t0: float = 300.0        # température initiale de la structure [K]

    @property
    def alpha(self) -> float:
        """Diffusivité thermique [m²/s]."""
        return self.k / (self.rho * self.cp)


MATERIAU = Materiau()


@dataclass(frozen=True)
class Mission:
    """Paramètres imposés par la mission (non optimisés)."""
    nom: str
    v_entree: float            # vitesse d'entrée [m/s]
    h_entree: float = 120e3    # altitude d'entrée [m]
    m_c: float = 5000.0        # masse de la capsule hors bouclier [kg]
    d_min: float = 3.0         # diamètre minimal habitable [m]
    n_lim: float = 10.0        # décélération maximale admise [g]
    ts_lim_c: float = 250.0    # température maximale de la structure [°C]


MISSION_LUNAIRE = Mission("Retour lunaire", 11_000.0)
MISSION_LEO = Mission("Orbite basse", 7_800.0)


@dataclass(frozen=True)
class Capsule:
    """Un point de conception : les 5 paramètres d'action."""
    gamma_deg: float   # angle d'entrée [°] (négatif = descente)
    D: float           # diamètre [m]
    rn_sur_d: float    # rayon de nez rapporté au diamètre [-]
    e: float           # épaisseur d'ablateur [m]
    m_c: float         # masse hors bouclier [kg]

    @property
    def rn(self) -> float:
        """Rayon de nez [m]."""
        return self.rn_sur_d * self.D


# Paramètres d'action, dans cet ordre partout
PA = ["gamma_deg", "D", "rn_sur_d", "e", "m_c"]

# Domaine du plan d'expériences (spec §2)
BORNES_DOE = {
    "gamma_deg": (-7.0, -4.5),
    "D": (2.5, 5.0),
    "rn_sur_d": (0.5, 1.5),
    "e": (0.01, 0.06),
    "m_c": (3000.0, 8000.0),
}
