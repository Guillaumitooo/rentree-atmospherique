# Capsule de rentrée atmosphérique — retour lunaire

Projet GM5 « Optimisation de la conception avec l'IA » — INSA Strasbourg, 2026-2027.

Application Streamlit qui **dimensionne une capsule habitée et son bouclier thermique** pour un
retour lunaire balistique à 11 km/s. La capsule doit entrer dans un couloir de ~0,5° : trop
rasante, elle rebondit sur l'atmosphère ; trop raide, l'équipage dépasse 10 g. On cherche le
bouclier le plus léger qui garde la structure sous 250 °C.

**Démarche :** simulateur physique → plan d'expériences (2 000 simulations) → métamodèles IA →
prédiction → optimisation (SLSQP, NSGA-II) → **vérification par simulation**.

**Application en ligne :** _à compléter après déploiement_

## Lancer l'application en local

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows (Linux/macOS : source .venv/bin/activate)
pip install -r requirements.txt
streamlit run Accueil.py
```

## Lancer les tests

```bash
pytest
```

(~2 min ; les tests de pages entraînent les métamodèles.)

## Régénérer le plan d'expériences

```bash
python scripts/generer_doe.py
```

Produit `data/doe_reference.csv` (2 000 points, ~1 min).

## Organisation du code

| Dossier / fichier | Rôle |
|---|---|
| `core/constantes.py` | toutes les constantes (Terre, matériau, missions, domaine d'étude) |
| `core/bouclier.py` | masse, ablation et température de structure du bouclier |
| `core/trajectoire.py` | simulateur de rentrée (`solve_ivp`, détection du rebond) |
| `core/validation.py` | formules d'Allen-Eggers (validation) |
| `core/doe.py` | plan d'expériences Latin Hypercube et simulation en lot |
| `core/metamodeles.py` | régressions, classifieur du rebond, prédicteur hybride IA + physique |
| `core/optimisation.py` | masse minimale (criblage + SLSQP), front de Pareto (NSGA-II), vérification |
| `interface/commun.py` | état partagé entre pages, cache |
| `Accueil.py` | point d'entrée et menu |
| `vues/` | les pages de l'application |
| `tests/` | tests pytest (physique, IA, optimisation, pages) |
| `docs/superpowers/` | document de conception et plan de réalisation |

Le cœur de calcul (`core/`) n'utilise pas Streamlit : il se teste et se réutilise seul.

## Limites du modèle

- Point matériel, Terre sphérique non tournante, atmosphère exponentielle.
- Rentrée balistique (sans portance), C_D constant.
- Flux convectif au point d'arrêt (Sutton-Graves) ; flux radiatif ignoré (non négligeable à 11 km/s).
- Bouclier : ablation par chaleur effective, conduction en milieu semi-infini, bouclier frontal seul.
