"""Plan d'expériences numérique : tirage Latin Hypercube + simulation en lot (spec §7.1)."""
from pathlib import Path

import pandas as pd
from scipy.stats import qmc

from core.constantes import BORNES_DOE, MISSION_LUNAIRE, PA, Capsule, Mission
from core.trajectoire import simuler

# Colonnes produites par Resultat.resume()
COLONNES_PE = ["rebond", "n_max", "q_max_MW", "Q_MJ", "t_ch", "e_abl", "e_res",
               "T_s_C", "percement", "m_b", "duree", "portee_km"]

CHEMIN_DOE = Path(__file__).resolve().parent.parent / "data" / "doe_reference.csv"


def tirer_lhs(n: int, bornes: dict = BORNES_DOE, graine: int = 42) -> pd.DataFrame:
    """Tire n points répartis uniformément dans le domaine (Latin Hypercube)."""
    tirage = qmc.LatinHypercube(d=len(PA), seed=graine).random(n)
    bas = [bornes[c][0] for c in PA]
    haut = [bornes[c][1] for c in PA]
    return pd.DataFrame(qmc.scale(tirage, bas, haut), columns=PA)


def est_faisable(ligne, mission: Mission) -> bool:
    """Un point est faisable s'il ne rebondit pas, n'est pas percé et respecte les limites."""
    return bool(
        not ligne["rebond"]
        and not ligne["percement"]
        and ligne["n_max"] <= mission.n_lim
        and ligne["T_s_C"] <= mission.ts_lim_c
    )


def simuler_plan(plan: pd.DataFrame, mission: Mission = MISSION_LUNAIRE) -> pd.DataFrame:
    """Simule chaque point du plan et ajoute les paramètres d'évaluation."""
    lignes = []
    for _, p in plan.iterrows():
        resultat = simuler(Capsule(**{c: float(p[c]) for c in PA}), mission)
        lignes.append({**{c: p[c] for c in PA}, **resultat.resume()})
    df = pd.DataFrame(lignes)
    df["faisable"] = df.apply(est_faisable, axis=1, mission=mission)
    return df
