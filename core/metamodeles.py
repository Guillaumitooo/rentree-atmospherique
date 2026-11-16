"""Métamodèles entraînés sur le plan d'expériences (spec §7.3 et §7.4).

- Régressions : prédire n_max, q̇_max, Q, t_ch (et T_s pour comparaison) sur les points sans rebond.
- Classification : prédire si la capsule rebondit.
- PredicteurCapsule : modèle **hybride IA + physique**. L'IA prédit Q et t_ch, puis la
  température de structure et l'ablation sont recalculées par les formules du bouclier.
"""
from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import RBF, ConstantKernel, WhiteKernel
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.metrics import (accuracy_score, confusion_matrix, mean_absolute_error,
                             mean_squared_error, r2_score)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import PolynomialFeatures, StandardScaler

from core.bouclier import masse_bouclier, temperature_structure
from core.constantes import BORNES_DOE, MATERIAU, PA, Materiau

CIBLES = ["n_max", "q_max_MW", "Q_MJ", "t_ch", "T_s_C"]
CIBLES_PREDICTEUR = ["n_max", "q_max_MW", "Q_MJ", "t_ch"]   # T_s est déduite par la physique
NOMS_REGRESSION = ["Polynôme degré 2", "Polynôme degré 3", "Forêt aléatoire", "Processus gaussien"]
NOMS_CLASSIFIEUR = ["Régression logistique", "Forêt aléatoire"]
N_MAX_PROCESSUS_GAUSSIEN = 800   # le processus gaussien coûte O(n³) : on limite l'apprentissage


@dataclass
class ResultatModele:
    modele: object
    metriques: dict
    y_test: np.ndarray
    y_pred: np.ndarray


def creer_regresseur(nom: str, graine: int = 42):
    """Pipeline scikit-learn : normalisation des entrées puis modèle."""
    if nom == "Polynôme degré 2":
        modele = make_pipeline(PolynomialFeatures(2), Ridge(alpha=1e-3))
    elif nom == "Polynôme degré 3":
        modele = make_pipeline(PolynomialFeatures(3), Ridge(alpha=1e-3))
    elif nom == "Forêt aléatoire":
        modele = RandomForestRegressor(n_estimators=200, random_state=graine, n_jobs=-1)
    elif nom == "Processus gaussien":
        noyau = ConstantKernel() * RBF(length_scale=[1.0] * len(PA)) + WhiteKernel()
        modele = GaussianProcessRegressor(noyau, normalize_y=True, random_state=graine)
    else:
        raise ValueError(f"Modèle de régression inconnu : {nom}")
    return make_pipeline(StandardScaler(), modele)


def creer_classifieur(nom: str, graine: int = 42):
    if nom == "Régression logistique":
        modele = LogisticRegression(max_iter=1000)
    elif nom == "Forêt aléatoire":
        modele = RandomForestClassifier(n_estimators=200, random_state=graine, n_jobs=-1)
    else:
        raise ValueError(f"Classifieur inconnu : {nom}")
    return make_pipeline(StandardScaler(), modele)


def entrainer_regression(df: pd.DataFrame, cible: str, nom: str, graine: int = 42) -> ResultatModele:
    """Apprend `cible` sur les points sans rebond (80 % apprentissage / 20 % test)."""
    donnees = df[~df["rebond"].astype(bool)].dropna(subset=[cible])
    X, y = donnees[PA].to_numpy(), donnees[cible].to_numpy()
    X_app, X_test, y_app, y_test = train_test_split(X, y, test_size=0.2, random_state=graine)
    if nom == "Processus gaussien" and len(X_app) > N_MAX_PROCESSUS_GAUSSIEN:
        X_app, y_app = X_app[:N_MAX_PROCESSUS_GAUSSIEN], y_app[:N_MAX_PROCESSUS_GAUSSIEN]
    modele = creer_regresseur(nom, graine).fit(X_app, y_app)
    y_pred = modele.predict(X_test)
    metriques = {
        "R2": r2_score(y_test, y_pred),
        "RMSE": float(np.sqrt(mean_squared_error(y_test, y_pred))),
        "MAE": mean_absolute_error(y_test, y_pred),
        "erreur_max": float(np.max(np.abs(y_test - y_pred))),
    }
    return ResultatModele(modele, metriques, y_test, y_pred)


def entrainer_classifieur(df: pd.DataFrame, nom: str, graine: int = 42) -> ResultatModele:
    """Apprend à reconnaître les rebonds sur tous les points (80 / 20)."""
    X, y = df[PA].to_numpy(), df["rebond"].astype(bool).to_numpy()
    X_app, X_test, y_app, y_test = train_test_split(X, y, test_size=0.2, random_state=graine, stratify=y)
    modele = creer_classifieur(nom, graine).fit(X_app, y_app)
    y_pred = modele.predict(X_test)
    metriques = {
        "exactitude": accuracy_score(y_test, y_pred),
        "matrice_confusion": confusion_matrix(y_test, y_pred, labels=[False, True]).tolist(),
    }
    return ResultatModele(modele, metriques, y_test, y_pred)


class PredicteurCapsule:
    """Prédiction instantanée de tous les paramètres d'évaluation d'une capsule."""

    def __init__(self, classifieur, regresseurs: dict, mat: Materiau = MATERIAU):
        self.classifieur = classifieur
        self.regresseurs = regresseurs
        self.mat = mat

    def predire(self, X: pd.DataFrame) -> pd.DataFrame:
        entrees = X[PA].to_numpy(dtype=float)
        sortie = pd.DataFrame(index=X.index)
        # Probabilité de la classe « rebond = True »
        classes = list(self.classifieur.classes_)
        sortie["p_rebond"] = self.classifieur.predict_proba(entrees)[:, classes.index(True)]
        for cible, modele in self.regresseurs.items():
            sortie[cible] = modele.predict(entrees)
        # Partie physique du modèle hybride (unités SI : Q en J/m²)
        thermique = [temperature_structure(Q_MJ * 1e6, max(t_ch, 0.0), e, self.mat)
                     for Q_MJ, t_ch, e in zip(sortie["Q_MJ"], sortie["t_ch"], X["e"])]
        for cle in ("e_abl", "e_res", "T_s_C"):
            sortie[cle] = [th[cle] for th in thermique]
        sortie["m_b"] = [masse_bouclier(D, e, self.mat) for D, e in zip(X["D"], X["e"])]
        return sortie


def entrainer_predicteur(df: pd.DataFrame, nom_reg: str = "Processus gaussien",
                         nom_clf: str = "Forêt aléatoire") -> PredicteurCapsule:
    classifieur = entrainer_classifieur(df, nom_clf).modele
    regresseurs = {c: entrainer_regression(df, c, nom_reg).modele for c in CIBLES_PREDICTEUR}
    return PredicteurCapsule(classifieur, regresseurs)


def hors_domaine(X: pd.DataFrame, bornes: dict = BORNES_DOE) -> np.ndarray:
    """Vrai pour chaque ligne qui sort du domaine du plan d'expériences."""
    dehors = np.zeros(len(X), dtype=bool)
    for c, (lo, hi) in bornes.items():
        dehors |= ~X[c].between(lo - 1e-9, hi + 1e-9).to_numpy()
    return dehors
