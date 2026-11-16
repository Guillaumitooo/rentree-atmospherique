"""Génère le plan d'expériences de référence (2 000 points) dans data/doe_reference.csv.

Usage : python scripts/generer_doe.py
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.constantes import MISSION_LUNAIRE  # noqa: E402
from core.doe import CHEMIN_DOE, simuler_plan, tirer_lhs  # noqa: E402

N_POINTS = 2000

if __name__ == "__main__":
    debut = time.perf_counter()
    df = simuler_plan(tirer_lhs(N_POINTS), MISSION_LUNAIRE)
    CHEMIN_DOE.parent.mkdir(exist_ok=True)
    df.to_csv(CHEMIN_DOE, index=False)
    print(f"{len(df)} points en {time.perf_counter() - debut:.0f} s -> {CHEMIN_DOE}")
    print(f"rebond : {df['rebond'].mean():.1%}   percement : {df['percement'].mean():.1%}   "
          f"faisable : {df['faisable'].mean():.1%}")
