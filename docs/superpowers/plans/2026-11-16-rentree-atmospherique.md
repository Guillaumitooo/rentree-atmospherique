# Capsule de rentrée (retour lunaire) — plan de réalisation

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal :** une application Streamlit multipage, déployée en ligne, qui dimensionne la capsule et le bouclier thermique d'un retour lunaire balistique. Elle enchaîne simulateur physique → plan d'expériences → métamodèles → prédiction → optimisation → vérification.

**Architecture :** un paquet `core/` de fonctions pures sans Streamlit (physique, plan d'expériences, IA, optimisation), testé avec pytest. Une couche `interface/` fournit l'état partagé et le cache. Les pages Streamlit restent minces et ne font qu'afficher. Le plan d'expériences de référence est pré-calculé dans un CSV versionné pour que l'application en ligne démarre vite.

**Tech Stack :** Python (3.12 sur Streamlit Cloud, 3.14 en local), streamlit, numpy, scipy, pandas, plotly, scikit-learn, pymoo, pytest.

**Spec :** `docs/superpowers/specs/2026-11-16-rentree-atmospherique-design.md`. L'exécutant lit la spec et ce plan ensemble.

## Global Constraints

- Code dans `rentree-atmospherique/` à la racine du dossier projet. Toutes les commandes ci-dessous se lancent depuis ce dossier.
- **Toutes les constantes physiques, matériau et mission sont dans `core/constantes.py`, et nulle part ailleurs.**
- Unités SI dans `core/` : e en mètres, q̇ en W/m², Q en J/m². La conversion en cm, MW/m² ou MJ/m² se fait seulement dans les colonnes du plan d'expériences et à l'affichage.
- Noms des PA, identiques partout : `gamma_deg`, `D`, `rn_sur_d`, `e`, `m_c`.
- Commentaires et docstrings en français. Le code doit rester assez simple pour être expliqué par l'étudiant (anti-objectif de la spec §3).
- Pas de TensorFlow ni de PyTorch. Les dépendances de `requirements.txt` sont données avec une version minimale, sans version figée.
- L'application en ligne démarre en moins de 10 s : aucune simulation en lot au chargement, le CSV de référence est lu.
- Messages de commit en anglais, conventionnels (`feat:`, `test:`, `docs:`), terminés par la ligne `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.

## Review Focus

1. **Point hors du domaine du plan d'expériences** (par exemple m_c = 10 t saisie sur la page Mission) : la page Prédiction affiche un avertissement visible, et le simulateur continue de répondre. Test ajouté à la Tâche 5 (`hors_domaine`) et à la Tâche 8 (avertissement sur la page).
2. **Optimum prédit faisable qui rebondit en réalité** : `verifier()` le marque comme non respecté sans planter, et la page l'affiche en rouge. Test ajouté à la Tâche 6.
3. **Point à la frontière du rebond** (γ ≈ −5,45°, chauffe très longue) : la simulation se termine en moins de 2 s avec des valeurs finies. Test ajouté à la Tâche 2.
4. **Bouclier percé** (e = 5 mm) : `percement=True` et `T_s_C=NaN`. Le CSV, les graphiques et l'entraînement l'acceptent, et les lignes NaN sont exclues de la régression. Tests ajoutés aux Tâches 1, 2 et 5.
5. **Mission sans solution** (n_lim = 2 g) : l'optimisation renvoie `succes=False` et la page affiche un message clair au lieu d'une exception. Test ajouté à la Tâche 6.

## Structure des fichiers

```
rentree-atmospherique/
├── requirements.txt, .gitignore, pytest.ini, README.md
├── core/
│   ├── __init__.py
│   ├── constantes.py     Materiau, Mission, Capsule, constantes, BORNES_DOE
│   ├── bouclier.py       masse et thermique du bouclier (interface remplaçable)
│   ├── trajectoire.py    simuler() → Resultat
│   ├── validation.py     Allen-Eggers
│   ├── doe.py            LHS + simulation en lot
│   ├── metamodeles.py    régressions, classifieur, PredicteurCapsule
│   └── optimisation.py   SLSQP, NSGA-II, vérification
├── interface/commun.py   mission courante, cache du DOE et du prédicteur
├── app.py                Accueil
├── pages/1_Mission_et_capsule.py … 6_Optimisation.py
├── scripts/generer_doe.py
├── data/doe_reference.csv
└── tests/test_*.py
```

Correspondance avec les séances (spec §9) :
- **S1** : Tâches 1 à 4 et 7
- **S2** : Tâches 5, 6, 8 et 9
- **S3** : Tâches 10 et 11, puis Tâche 12 (extension)

---

### Tâche 1 : Mise en place, constantes et modèle de bouclier

**Files :**
- Create : `requirements.txt`, `.gitignore`, `pytest.ini`, `core/__init__.py`, `core/constantes.py`, `core/bouclier.py`
- Test : `tests/test_bouclier.py`

**Interfaces :**
- Produces (`core/constantes.py`) :
  - constantes `RT = 6_371e3`, `G0 = 9.81`, `RHO0 = 1.225`, `H_ECHELLE = 7_200.0`, `K_SG = 1.7415e-4`, `CD = 1.4`, `V_FIN = 250.0`, `T_MAX = 3_000.0`
  - `@dataclass(frozen=True) Materiau(rho=510.0, k=0.3, cp=1500.0, m_sup=15.0, h_eff=30e6, t_pyro=900.0, t0=300.0)` avec une propriété `alpha = k/(rho*cp)` ; instance `MATERIAU`
  - `@dataclass(frozen=True) Mission(nom: str, v_entree: float, h_entree=120e3, m_c=5000.0, d_min=3.0, n_lim=10.0, ts_lim_c=250.0)` ; instances `MISSION_LUNAIRE = Mission("Retour lunaire", 11_000.0)` et `MISSION_LEO = Mission("Orbite basse", 7_800.0)`
  - `@dataclass(frozen=True) Capsule(gamma_deg, D, rn_sur_d, e, m_c)` avec une propriété `rn = rn_sur_d * D`
  - `PA = ["gamma_deg", "D", "rn_sur_d", "e", "m_c"]`
  - `BORNES_DOE = {"gamma_deg": (-7.0, -4.5), "D": (2.5, 5.0), "rn_sur_d": (0.5, 1.5), "e": (0.01, 0.06), "m_c": (3000.0, 8000.0)}`
- Produces (`core/bouclier.py`) :
  - `masse_bouclier(D: float, e: float, mat=MATERIAU) -> float`
  - `temperature_structure(Q: float, t_ch: float, e: float, mat=MATERIAU) -> dict` avec les clés `e_abl`, `e_res`, `T_s_C`, `percement`
  - `evaluer_bouclier(t: np.ndarray, q: np.ndarray, e: float, mat=MATERIAU) -> dict` avec les clés `Q`, `t_ch`, `e_abl`, `e_res`, `T_s_C`, `percement`

- [ ] **Étape 1 : mise en place.** Créer le dossier et lancer `git init`. Créer un environnement virtuel `.venv`. Écrire `requirements.txt` (`streamlit>=1.40`, `numpy>=1.26`, `scipy>=1.12`, `pandas>=2.1`, `plotly>=5.20`, `scikit-learn>=1.4`, `pymoo>=0.6.1`, `pytest>=8`). Écrire `.gitignore` (`.venv/`, `__pycache__/`, `.pytest_cache/`). Écrire `pytest.ini` avec `pythonpath = .`. Installer avec `pip install -r requirements.txt`.
  - Vérification : `python -c "import streamlit, sklearn, pymoo, plotly; print('ok')"` affiche `ok`.
  - Si `pymoo` ne s'installe pas sous Python 3.14, le noter et appliquer la solution de repli de la Tâche 6.

- [ ] **Étape 2 : écrire les tests qui échouent**

```python
import numpy as np, pytest
from scipy.special import erfc
from core.constantes import MATERIAU
from core.bouclier import masse_bouclier, temperature_structure, evaluer_bouclier

def test_masse_bouclier():
    assert masse_bouclier(3.0, 0.03) == pytest.approx((510*0.03 + 15) * np.pi * 9 / 4)  # ≈ 214,2 kg

def test_temperature_structure_formule():
    r = temperature_structure(Q=1e8, t_ch=300.0, e=0.04)
    e_abl = 1e8 / (510 * 30e6)
    attendu = 300 + 600 * erfc((0.04 - e_abl) / (2 * np.sqrt(MATERIAU.alpha * 300))) - 273.15
    assert r["e_abl"] == pytest.approx(e_abl)
    assert r["T_s_C"] == pytest.approx(attendu)      # ≈ 44 °C
    assert r["percement"] is False

def test_temperature_decroit_avec_epaisseur():
    ts = [temperature_structure(2e8, 300.0, e)["T_s_C"] for e in (0.02, 0.03, 0.05)]
    assert ts[0] > ts[1] > ts[2]

def test_percement():                                  # Review Focus 4
    r = temperature_structure(Q=2e8, t_ch=300.0, e=0.005)
    assert r["percement"] is True and np.isnan(r["T_s_C"]) and r["e_res"] <= 0

def test_evaluer_bouclier_integre_et_duree():
    t = np.linspace(0, 100, 1001)
    q = np.where((t >= 20) & (t <= 60), 1e6, 0.0)     # créneau de 40 s à 1 MW/m²
    r = evaluer_bouclier(t, q, 0.04)
    assert r["Q"] == pytest.approx(4e7, rel=0.01)
    assert r["t_ch"] == pytest.approx(40.0, abs=0.2)
```

- [ ] **Étape 3 : vérifier que les tests échouent.** `pytest tests/test_bouclier.py -v` doit échouer avec `ModuleNotFoundError`.
- [ ] **Étape 4 : implémenter `core/constantes.py` et `core/bouclier.py`** selon les formules de la spec §6.3.
  - `t_ch` = temps du dernier point où q > 0,05·max(q) moins temps du premier.
  - `Q` est calculé avec `np.trapezoid`.
  - `percement` vaut `e_res <= 0`, et dans ce cas `T_s_C = nan`.
- [ ] **Étape 5 : vérifier que les tests passent.** `pytest tests/test_bouclier.py -v` affiche 5 passed.
- [ ] **Étape 6 : commit.** `git add -A && git commit -m "feat: constants and heat shield model"`

### Tâche 2 : Simulateur de trajectoire

**Files :** Create `core/trajectoire.py` · Test `tests/test_trajectoire.py`

**Interfaces :**
- Consumes : constantes, `Capsule`, `Mission`, `MATERIAU`, `masse_bouclier`, `evaluer_bouclier`
- Produces :
  - `@dataclass Resultat` avec :
    - des tableaux `t, V, gamma, h, s, n, q`
    - des scalaires `rebond: bool, n_max, q_max, Q, t_ch, e_abl, e_res, T_s_C, percement: bool, m_b, duree, portee`
    - une méthode `resume() -> dict`, qui renvoie les colonnes PE du plan d'expériences : `rebond, n_max, q_max_MW, Q_MJ, t_ch, e_abl, e_res, T_s_C, percement, m_b, duree, portee_km`
  - `simuler(capsule: Capsule, mission: Mission = MISSION_LUNAIRE, mat=MATERIAU) -> Resultat`

- [ ] **Étape 1 : écrire les tests qui échouent**

```python
import time, numpy as np
from core.constantes import Capsule, MISSION_LUNAIRE, MISSION_LEO
from core.trajectoire import simuler

REF = dict(D=3.0, rn_sur_d=1.2, e=0.03, m_c=5000.0)

def test_rebond_lunaire_rasant():
    assert simuler(Capsule(-4.5, **REF), MISSION_LUNAIRE).rebond is True

def test_pas_de_rebond_lunaire_raide():
    r = simuler(Capsule(-6.5, **REF), MISSION_LUNAIRE)
    assert r.rebond is False and r.V[-1] < 260

def test_pas_de_rebond_leo():
    assert simuler(Capsule(-1.0, **REF), MISSION_LEO).rebond is False

def test_vitesse_decroit():
    r = simuler(Capsule(-6.0, **REF), MISSION_LUNAIRE)
    assert r.V[-1] < r.V[0] and r.h[-1] < r.h[0]

def test_ordre_de_grandeur_couloir():                 # spec §2
    r = simuler(Capsule(-5.8, **REF), MISSION_LUNAIRE)
    assert 5.0 < r.n_max < 10.0 and 1.5e6 < r.q_max < 3e6

def test_frontiere_rebond_rapide_et_finie():          # Review Focus 3
    t0 = time.perf_counter()
    r = simuler(Capsule(-5.45, **REF), MISSION_LUNAIRE)
    assert time.perf_counter() - t0 < 2.0
    assert np.isfinite(r.n_max) and np.isfinite(r.Q)

def test_percement_propage():                         # Review Focus 4
    r = simuler(Capsule(-5.6, 3.0, 1.2, 0.005, 5000.0), MISSION_LUNAIRE)
    assert r.percement is True and np.isnan(r.resume()["T_s_C"])
```

- [ ] **Étape 2 : vérifier que les tests échouent.** `pytest tests/test_trajectoire.py -v` doit échouer.
- [ ] **Étape 3 : implémenter `simuler`** avec les équations et les événements de la spec §6.1 : `solve_ivp`, `max_step=1.0`, `rtol=1e-7`, `atol=1e-6`.
  - Événement de fin : `V − V_FIN`, terminal.
  - Événement de rebond : `h − (h_entree + 1)`, terminal, `direction=+1`.
  - Garde-fou : intervalle d'intégration `(0, T_MAX)`.
  - `n` et `q` sont recalculés sur la solution, puis le bouclier est évalué avec `evaluer_bouclier`.
  - Les valeurs thermiques sont calculées même en cas de rebond.
- [ ] **Étape 4 : vérifier que les tests passent.** `pytest tests/test_trajectoire.py -v` affiche 7 passed.
- [ ] **Étape 5 : commit.** `feat: 2D ballistic entry simulator with skip detection`

### Tâche 3 : Validation par Allen-Eggers

**Files :** Create `core/validation.py` · Test `tests/test_validation.py`

**Interfaces :**
- Produces : `n_max_allen_eggers(v_e: float, gamma_deg: float) -> float` (en g) et `q_max_allen_eggers(v_e: float, gamma_deg: float, beta: float, rn: float) -> float` (en W/m²), formules de la spec §6.4

- [ ] **Étape 1 : écrire les tests**

```python
import pytest
from core.constantes import Capsule, MISSION_LEO, CD
from core.trajectoire import simuler
from core.validation import n_max_allen_eggers, q_max_allen_eggers
import numpy as np

def test_formule_n_max():
    assert n_max_allen_eggers(7800.0, -6.0) == pytest.approx(16.6, rel=0.02)

def test_accord_simulation_leo_raide():
    c = Capsule(-6.0, 3.0, 1.0, 0.04, 3000.0)
    r = simuler(c, MISSION_LEO)
    assert r.n_max == pytest.approx(n_max_allen_eggers(7800.0, -6.0), rel=0.15)
    beta = (c.m_c + r.m_b) / (CD * np.pi * c.D**2 / 4)
    assert r.q_max == pytest.approx(q_max_allen_eggers(7800.0, -6.0, beta, c.rn), rel=0.10)
```

- [ ] **Étape 2 : vérifier que les tests échouent.** Lancer `pytest tests/test_validation.py -v`.
- [ ] **Étape 3 : implémenter les deux fonctions.**
- [ ] **Étape 4 : vérifier que les tests passent.** 2 passed.
- [ ] **Étape 5 : commit.** `feat: Allen-Eggers reference formulas`

### Tâche 4 : Plan d'expériences et CSV de référence

**Files :** Create `core/doe.py`, `scripts/generer_doe.py`, `data/doe_reference.csv` · Test `tests/test_doe.py`

**Interfaces :**
- Produces :
  - `tirer_lhs(n: int, bornes=BORNES_DOE, graine: int = 42) -> pd.DataFrame`, avec les colonnes `PA`
  - `simuler_plan(plan: pd.DataFrame, mission=MISSION_LUNAIRE) -> pd.DataFrame`, qui renvoie les colonnes PA, puis les colonnes de `Resultat.resume()`, puis `faisable`
  - `est_faisable(ligne, mission) -> bool` : vrai si la capsule ne rebondit pas, n'est pas percée, respecte `n_max <= n_lim` et respecte `T_s_C <= ts_lim_c`
  - `COLONNES_PE: list[str]`
  - `CHEMIN_DOE = Path("data/doe_reference.csv")`

- [ ] **Étape 1 : écrire les tests**

```python
from core.constantes import PA, BORNES_DOE
from core.doe import tirer_lhs, simuler_plan, COLONNES_PE

def test_lhs_bornes_et_colonnes():
    p = tirer_lhs(200)
    assert list(p.columns) == PA and len(p) == 200
    for c, (lo, hi) in BORNES_DOE.items():
        assert p[c].between(lo, hi).all()

def test_simuler_plan_petit():
    df = simuler_plan(tirer_lhs(30, graine=1))
    assert set(PA + COLONNES_PE + ["faisable"]) <= set(df.columns)
    assert df["rebond"].any() and (~df["rebond"]).any()   # les deux classes existent
    assert not (df["faisable"] & df["rebond"]).any()
```

- [ ] **Étape 2 : vérifier que les tests échouent.** Lancer `pytest tests/test_doe.py -v`.
- [ ] **Étape 3 : implémenter.**
  - `tirer_lhs` utilise `scipy.stats.qmc.LatinHypercube(d=5, seed=graine)` puis `qmc.scale`.
  - `simuler_plan` fait une boucle simple sur les lignes.
  - `scripts/generer_doe.py` tire 2 000 points, les simule, écrit `CHEMIN_DOE` et affiche le taux de rebond et le taux de faisabilité.
- [ ] **Étape 4 : vérifier que les tests passent.** 2 passed.
- [ ] **Étape 5 : générer le CSV.** `python scripts/generer_doe.py` termine en moins de 3 min.
  - Le CSV doit avoir 2 000 lignes.
  - Le taux de rebond doit être compris entre 15 % et 60 %.
  - Au moins 3 % des points doivent être faisables.
  - Si ce n'est pas le cas, s'arrêter et le signaler : les bornes de la spec seraient à revoir.
- [ ] **Étape 6 : commit (CSV inclus).** `feat: LHS design of experiments and reference dataset`

### Tâche 5 : Métamodèles

**Files :** Create `core/metamodeles.py` · Test `tests/test_metamodeles.py`

**Interfaces :**
- Consumes : un DataFrame au format `simuler_plan`, et `temperature_structure`
- Produces :
  - `CIBLES = ["n_max", "q_max_MW", "Q_MJ", "t_ch", "T_s_C"]`
  - `NOMS_REGRESSION = ["Polynôme degré 2", "Polynôme degré 3", "Forêt aléatoire", "Processus gaussien"]`
  - `NOMS_CLASSIFIEUR = ["Régression logistique", "Forêt aléatoire"]`
  - `@dataclass ResultatModele(modele, metriques: dict, y_test, y_pred)` : pour la régression, `metriques` contient `R2, RMSE, MAE, erreur_max` ; pour le classifieur, `exactitude, matrice_confusion`
  - `entrainer_regression(df, cible: str, nom: str, graine=42) -> ResultatModele` : apprend sur les lignes sans rebond et sans NaN dans la cible, avec un découpage 80/20
  - `entrainer_classifieur(df, nom: str, graine=42) -> ResultatModele` : cible `rebond`, apprise sur toutes les lignes
  - `class PredicteurCapsule` :
    - construit avec `(classifieur, regresseurs: dict[str, modèle], mat=MATERIAU)`
    - méthode `predire(X: pd.DataFrame) -> pd.DataFrame`, qui renvoie `p_rebond, n_max, q_max_MW, Q_MJ, t_ch, e_abl, e_res, T_s_C, m_b`
  - `entrainer_predicteur(df, nom_reg="Processus gaussien", nom_clf="Forêt aléatoire") -> PredicteurCapsule`
  - `hors_domaine(X: pd.DataFrame, bornes=BORNES_DOE) -> np.ndarray[bool]`
- **Décision du plan (modèle hybride, Cours 1 et 3) :** dans `PredicteurCapsule.predire`, les grandeurs `e_abl`, `e_res` et `T_s_C` ne viennent pas de la régression directe de T_s. Elles sont **calculées par `temperature_structure`** à partir de Q et t_ch prédits, et `m_b` vient de `masse_bouclier`. La régression directe de T_s reste montrée sur la page Métamodèles pour comparaison.

- [ ] **Étape 1 : écrire les tests** (fixture de module : lire `data/doe_reference.csv`)

```python
def test_regression_n_max_precise(doe):
    r = entrainer_regression(doe, "n_max", "Forêt aléatoire")
    assert r.metriques["R2"] > 0.90

def test_classifieur_rebond(doe):
    assert entrainer_classifieur(doe, "Forêt aléatoire").metriques["exactitude"] > 0.95

def test_regression_ignore_nan(doe):                  # Review Focus 4
    r = entrainer_regression(doe, "T_s_C", "Polynôme degré 2")
    assert np.isfinite(r.y_pred).all()

def test_predicteur_colonnes_et_hybride(doe):
    p = entrainer_predicteur(doe, "Forêt aléatoire", "Forêt aléatoire")
    out = p.predire(doe[PA].head(5))
    assert {"p_rebond", "T_s_C", "m_b"} <= set(out.columns)
    assert out["p_rebond"].between(0, 1).all()

def test_hors_domaine():                              # Review Focus 1
    X = pd.DataFrame([dict(gamma_deg=-6, D=3, rn_sur_d=1.2, e=0.03, m_c=10_000)])
    assert hors_domaine(X)[0]
```

- [ ] **Étape 2 : vérifier que les tests échouent.** Lancer `pytest tests/test_metamodeles.py -v`.
- [ ] **Étape 3 : implémenter.** Chaque modèle est un `Pipeline` scikit-learn qui commence par `StandardScaler`.
  - Polynômes : `PolynomialFeatures` suivi de `Ridge(alpha=1e-3)`.
  - Forêt aléatoire : `RandomForestRegressor(n_estimators=200)`.
  - Processus gaussien : `GaussianProcessRegressor` avec un noyau `ConstantKernel*RBF(length_scale=[1]*5)+WhiteKernel`, `normalize_y=True`.
  - Classifieurs : `LogisticRegression(max_iter=1000)` et `RandomForestClassifier(n_estimators=200)`.
- [ ] **Étape 4 : vérifier que les tests passent.** 5 passed, en moins de 60 s.
- [ ] **Étape 5 : commit.** `feat: surrogate models and hybrid capsule predictor`

### Tâche 6 : Optimisation et vérification

**Files :** Create `core/optimisation.py` · Test `tests/test_optimisation.py`

**Interfaces :**
- Consumes : `PredicteurCapsule`, `simuler`, `masse_bouclier`, `Mission`
- Produces :
  - `VARIABLES = ["gamma_deg", "D", "rn_sur_d", "e"]` (m_c est fixée à `mission.m_c`)
  - `bornes_optim(mission) -> list[tuple]` : `[(-7.0, -4.5), (mission.d_min, 5.0), (0.5, 1.5), (0.01, 0.06)]`
  - `contraintes(x, pred, mission) -> np.ndarray` : tableau de valeurs qui doivent toutes être ≥ 0, `[0.05 − p_rebond, n_lim − n_max, ts_lim_c − T_s_C, e_res − 5e-4]`. Un `T_s_C` NaN compte comme −1e3 (contrainte violée).
  - `@dataclass ResultatOptim(succes: bool, x: dict, m_b: float, predit: dict, message: str)`
  - `optimiser_slsqp(pred, mission, n_departs=10, graine=0) -> ResultatOptim`
  - `optimiser_nsga2(pred, mission, pop=80, generations=60, graine=0) -> pd.DataFrame` : colonnes `VARIABLES + ["m_b", "n_max"]`, front non dominé
  - `verifier(points: pd.DataFrame, mission) -> pd.DataFrame` : re-simule chaque point. Ajoute les colonnes `*_sim` (n_max, T_s_C, e_res, rebond), les écarts `ecart_n_max_pct` et `ecart_T_s_C`, et `respecte: bool`.

- [ ] **Étape 1 : écrire les tests** (fixture : `entrainer_predicteur(doe, "Forêt aléatoire", "Forêt aléatoire")`)

```python
def test_slsqp_respecte_bornes(pred):
    r = optimiser_slsqp(pred, MISSION_LUNAIRE)
    assert r.succes and r.x["D"] >= MISSION_LUNAIRE.d_min - 1e-6
    assert -7.0 <= r.x["gamma_deg"] <= -4.5 and r.predit["n_max"] <= 10.0 + 1e-3

def test_slsqp_infaisable(pred):                      # Review Focus 5
    r = optimiser_slsqp(pred, replace(MISSION_LUNAIRE, n_lim=2.0))
    assert r.succes is False and r.message

def test_nsga2_front_non_domine(pred):
    f = optimiser_nsga2(pred, MISSION_LUNAIRE, pop=40, generations=20)
    assert len(f) >= 3
    for _, a in f.iterrows():
        assert not ((f.m_b <= a.m_b) & (f.n_max <= a.n_max) & ((f.m_b < a.m_b) | (f.n_max < a.n_max))).any()

def test_verifier_signale_rebond():                   # Review Focus 2
    pts = pd.DataFrame([dict(gamma_deg=-4.6, D=3.0, rn_sur_d=1.2, e=0.03)])
    v = verifier(pts, MISSION_LUNAIRE)
    assert v.loc[0, "rebond_sim"] and not v.loc[0, "respecte"]
```

- [ ] **Étape 2 : vérifier que les tests échouent.** Lancer `pytest tests/test_optimisation.py -v`.
- [ ] **Étape 3 : implémenter.**
  - SLSQP : `scipy.optimize.minimize(method="SLSQP")` sur `m_b(x)`, avec des contraintes `ineq`, depuis `n_departs` points LHS tirés dans `bornes_optim`. On garde le meilleur résultat faisable. Si aucun départ n'aboutit, renvoyer `succes=False` avec le message `"Aucune solution ne respecte les contraintes de la mission"`.
  - NSGA-II : `pymoo` `ElementwiseProblem` avec `n_obj=2` et `n_ieq_constr=4` (pymoo attend des contraintes G ≤ 0, donc passer `−contraintes`).
  - **Repli si pymoo est indisponible :** méthode ε-contrainte, c'est-à-dire `optimiser_slsqp` répété avec `n_lim` ∈ `linspace(6.5, 10, 8)`, puis filtrage des points non dominés. Même signature, même test.
- [ ] **Étape 4 : vérifier que les tests passent.** 4 passed.
- [ ] **Étape 5 : commit.** `feat: SLSQP and NSGA-II optimisation with physical verification`

### Tâche 7 : Socle de l'interface, Accueil, Mission et Simulation

**Files :** Create `interface/__init__.py`, `interface/commun.py`, `app.py`, `pages/1_Mission_et_capsule.py`, `pages/2_Simulation.py` · Test `tests/test_pages.py`

**Interfaces :**
- Produces (`interface/commun.py`) :
  - `mission_courante() -> Mission` : lue dans `st.session_state["mission"]`, `MISSION_LUNAIRE` par défaut
  - `definir_mission(m: Mission)`
  - `charger_doe() -> pd.DataFrame` : `@st.cache_data`, lit `CHEMIN_DOE`
  - `predicteur(nom_reg: str, nom_clf: str) -> PredicteurCapsule` : `@st.cache_resource`
  - `curseurs_capsule(cle: str, m_c_fixe: float | None = None) -> Capsule` : curseurs de la barre latérale, aux bornes de `BORNES_DOE`, avec `e` affichée en cm

Contenu des pages :
- **Accueil** : titre, question technique, schéma de la démarche (les 6 étapes en colonnes) et rappel des limites du modèle (spec §6.3 et §3, non-objectifs).
- **Page 1** : tableaux des PA et des PE, schéma de la capsule (SVG en ligne : calotte de rayon R_n, diamètre D), formulaire des paramètres de mission (V_E, m_c, D_min, n_lim, ts_lim_c) qui appelle `definir_mission`, et choix « Retour lunaire / Orbite basse ».
- **Page 2** : curseurs, puis `simuler`. Quatre graphiques Plotly : h(V), n(t), q̇(t), h(s). Une ligne de métriques : n_max, q̇_max, Q, T_s, m_b, avec un badge rebond / percement / faisable. Un onglet « Validation » balaie γ de −1° à −7° en orbite basse et superpose simulation et Allen-Eggers (n_max et q̇_max).

- [ ] **Étape 1 : écrire les tests de fumée**

```python
from streamlit.testing.v1 import AppTest
import pytest

PAGES = ["app.py", "pages/1_Mission_et_capsule.py", "pages/2_Simulation.py"]

@pytest.mark.parametrize("page", PAGES)
def test_page_sans_erreur(page):
    at = AppTest.from_file(page, default_timeout=60).run()
    assert not at.exception
```

- [ ] **Étape 2 : vérifier que les tests échouent.** Lancer `pytest tests/test_pages.py -v`.
- [ ] **Étape 3 : implémenter `interface/commun.py` et les trois pages.**
- [ ] **Étape 4 : vérifier que les tests passent, puis contrôler l'affichage.**
  - `pytest tests/test_pages.py -v` doit passer.
  - Lancer `streamlit run app.py` : la page Simulation affiche une rentrée à γ = −5,8° sans rebond et une rentrée à −4,8° avec rebond.
- [ ] **Étape 5 : commit.** `feat: home, mission and simulation pages`

### Tâche 8 : Pages Plan d'expériences, Métamodèles et Prédiction

**Files :** Create `pages/3_Plan_d_experiences.py`, `pages/4_Metamodeles.py`, `pages/5_Prediction.py` · Modify `tests/test_pages.py` (ajouter ces pages à `PAGES`)

Contenu des pages :
- **Page 3** : lecture de `charger_doe()`, avec téléchargement du CSV. Un bouton « Régénérer un petit plan » (n ≤ 200, mission courante). Histogrammes et matrice de corrélation. **Carte du couloir** : nuage γ_E × D coloré en trois classes (rebond / n > n_lim / faisable). Taux de faisabilité.
- **Page 4** : choix d'une cible et d'un modèle, puis `entrainer_regression` : métriques, graphe de parité, importance des variables par permutation (`sklearn.inspection.permutation_importance`). Un tableau compare les 4 modèles sur la cible choisie. Une section classifieur montre la matrice de confusion. Les choix sont mémorisés dans `st.session_state["nom_reg"]` et `["nom_clf"]`.
- **Page 5** : `curseurs_capsule`, puis `predicteur(...).predire` et `simuler` côte à côte. Tableau prédit / simulé / écart. `st.warning` si `hors_domaine`.

- [ ] **Étape 1 : ajouter les tests**
  - Ajouter les 3 pages à `PAGES`.
  - Ajouter un test qui met la page Prédiction hors domaine (Review Focus 1) : `at = AppTest.from_file("pages/5_Prediction.py"); at.session_state["mission"] = replace(MISSION_LUNAIRE, m_c=10_000.0); at.run()`, puis `assert at.warning`. Pour cela, `curseurs_capsule` utilise `m_c` de la mission courante comme valeur par défaut.
- [ ] **Étape 2 : vérifier que les tests échouent.** Lancer `pytest tests/test_pages.py -v`.
- [ ] **Étape 3 : implémenter les trois pages.**
- [ ] **Étape 4 : vérifier que les tests passent**, puis contrôler à l'œil dans `streamlit run app.py` que la carte du couloir montre une bande faisable étroite.
- [ ] **Étape 5 : commit.** `feat: DOE, surrogate and prediction pages`

### Tâche 9 : Page Optimisation

**Files :** Create `pages/6_Optimisation.py` · Modify `tests/test_pages.py`

Contenu de la page :
- **Onglet « Masse minimale »** : un bouton lance `optimiser_slsqp`. Si `succes` est faux, afficher `message` avec `st.error`. Sinon :
  - afficher la solution (γ_E, D, R_n/D, e en cm, m_b) ;
  - afficher `verifier` sur cette solution : prédit / simulé / écart, contraintes en vert ou rouge ;
  - signaler par une note les bornes atteintes (D = D_min, R_n/D = 1,5), avec l'explication de la spec §2.
- **Onglet « Pareto »** : `optimiser_nsga2`, puis un nuage m_b × n_max. Les 5 points du front les plus espacés sont re-simulés avec `verifier` et affichés en surimpression (marqueurs creux). Un tableau accompagne le graphique.
- Les calculs sont mis en cache par clé (mission, modèles), et les calculs coûteux ne se lancent que sur clic.

- [ ] **Étape 1 : ajouter les tests**
  - Ajouter la page à `PAGES`.
  - Ajouter un test (Review Focus 5) qui fixe `session_state["mission"]` avec `n_lim=2.0`, clique le bouton d'optimisation (`at.button[0].click().run()`), puis vérifie `assert at.error` et `assert not at.exception`.
- [ ] **Étape 2 : vérifier que les tests échouent.**
- [ ] **Étape 3 : implémenter la page.**
- [ ] **Étape 4 : vérifier.**
  - `pytest -v` : toute la suite passe.
  - Dans le navigateur, l'optimum se situe vers γ ≈ −5,8 à −6,0°, D = 3 m, avec une vérification verte.
- [ ] **Étape 5 : commit.** `feat: optimisation page with Pareto front and verification`

### Tâche 10 : Déploiement en ligne (séance 3)

**Files :** Create `README.md`

- [ ] **Étape 1 : écrire le `README.md`** : objet, lancement local (`pip install -r requirements.txt` puis `streamlit run app.py`), lancement des tests, structure des dossiers, limites du modèle.
- [ ] **Étape 2 : vérification finale en local.** `pytest -v` passe entièrement. `streamlit run app.py` ouvre les 7 pages sans erreur.
- [ ] **Étape 3 : publier sur GitHub. ⚠️ Action de l'étudiant** (son compte) : créer le dépôt public `rentree-atmospherique`, puis `git remote add origin …` et `git push -u origin main`.
- [ ] **Étape 4 : déployer sur Streamlit Community Cloud. ⚠️ Action de l'étudiant** : sur share.streamlit.io, « New app », choisir le dépôt, `app.py` comme fichier principal et Python 3.12 dans les réglages avancés.
- [ ] **Étape 5 : vérifier l'URL** dans une fenêtre privée. Démarrage en moins de 10 s, les 6 pages s'ouvrent, l'optimisation aboutit. Noter l'URL dans le README, puis commit `docs: README and deployment URL`.

### Tâche 11 : Manuel d'utilisation (PDF) et support de présentation

**Files :** Create `docs/manuel/manuel_utilisation.md` (puis exporté en PDF) et `docs/manuel/captures/*.png`

- [ ] **Étape 1 : faire les captures** de chaque page sur l'application déployée, avec les mêmes réglages que les exemples du manuel. Exemple de référence : mission lunaire par défaut, γ = −5,8°, D = 3 m, R_n/D = 1,2, e = 3 cm.
- [ ] **Étape 2 : rédiger le manuel.**
  - Introduction : sujet et démarche.
  - Une section par page : à quoi elle sert, étapes d'utilisation, capture commentée.
  - Un exemple complet reproductible, de la simulation à l'optimum vérifié.
  - Limites du modèle.
  - Exporter en PDF.
- [ ] **Étape 3 : vérifier la reproductibilité.** Refaire l'exemple du manuel sur l'URL : les valeurs affichées doivent correspondre aux captures, à l'arrondi près.
- [ ] **Étape 4 : préparer le support de présentation.**
  - Démarche, résultats clés : couloir, effet de D, front de Pareto, écart avec Allen-Eggers à 11 km/s.
  - Scénario de démonstration de 3 minutes.
  - Commit `docs: user manual`.

### Tâche 12 (extension 1) : Conduction 1D par différences finies

**Files :** Modify `core/bouclier.py`, `core/trajectoire.py` (paramètre `modele_thermique`), `pages/2_Simulation.py` · Test `tests/test_bouclier.py`

**Interfaces :**
- Produces : `evaluer_bouclier(t, q, e, mat=MATERIAU, modele: str = "erfc") -> dict` (mêmes clés). Avec `"differences_finies"`, la conduction 1D est résolue de façon implicite (Euler implicite, 50 nœuds sur `e_res`). Condition à la face chaude : T = T_p tant que q > 5 % de q_max. Face froide adiabatique. T_s = température maximale de la face froide.
- `simuler(..., modele_thermique="erfc")`, transmis tel quel à `evaluer_bouclier`.

- [ ] **Étape 1 : écrire le test.** Pour un créneau de chauffe de 300 s et e = 4 cm, `"differences_finies"` donne un T_s supérieur ou égal à celui de `"erfc"` à 5 °C près. La face adiabatique réchauffe davantage, donc le modèle erfc est le moins conservatif. Ajouter un test de convergence : à 100 nœuds, l'écart avec 50 nœuds est inférieur à 1 °C.
- [ ] **Étape 2 : vérifier que le test échoue.**
- [ ] **Étape 3 : implémenter le schéma implicite.** Matrice tridiagonale, résolue avec `scipy.linalg.solve_banded`.
- [ ] **Étape 4 : vérifier que les tests passent.**
- [ ] **Étape 5 : ajouter un sélecteur de modèle thermique et une comparaison sur la page Simulation**, puis commit `feat: implicit 1D conduction heat shield model`.

Les extensions 2 à 6 de la spec §9 n'ont pas de tâche : elles ne seront planifiées que si la Tâche 12 est terminée.
