# Conception d'une capsule de rentrée atmosphérique (retour lunaire) — document de conception

*Projet GM5 « Optimisation de la conception avec l'IA » — INSA Strasbourg, 2026-2027*
*Rédigé le 2026-11-16 · Étudiant seul · 3 séances de 3 h*
*Statut : version 2 (après relecture et vérification numérique), **validée par l'étudiant le 2026-11-16***

---

## 1. Intention et pourquoi

Projet de module GM5 (enseignant : H. Chibane), évalué sur quatre livrables : application Streamlit fonctionnelle, manuel d'utilisation PDF, **URL de l'application en ligne**, présentation orale avec démonstration (voir `Projet_IA.pdf`).

L'étudiant veut un sujet **qui paraisse ambitieux mais reste rapide à réaliser seul** : le thème spatial donne l'effet « waouh », la physique reste volontairement simple (point matériel + corrélations classiques), et toute la démarche attendue par le module est démontrée :

> simulateur physique → plan d'expériences → métamodèles IA → prédiction → optimisation → **vérification physique** → décision de l'ingénieur

C'est la chaîne du TD1 (application multipage usinage) et du Cours 3 (poutre encastrée : métamodèle + SLSQP + contrôle ingénieur), transposée à un objet spatial.

**Cadrage génie mécanique** (choisi par l'étudiant) : on **dimensionne une capsule** — géométrie et bouclier thermique — pour une **mission imposée**. Le bouclier rattache le sujet au transfert thermique (lien GM4 cité par le sujet).

**Le fil rouge de la soutenance** (choisi par l'étudiant : retour lunaire) : « enfiler l'aiguille ». À 11 km/s, la capsule doit entrer dans un **couloir de ~0,5°** : trop rasante, elle rebondit sur l'atmosphère et repart dans l'espace ; trop raide, l'équipage dépasse 10 g. Et il faut le bouclier le plus léger possible qui survive.

## 2. Le système étudié

**Mission imposée** : retour d'une **capsule habitée (3 personnes) depuis la Lune**. Entrée à **120 km** d'altitude à **11,0 km/s**, rentrée **balistique** (sans portance). Fin de la phase étudiée à l'ouverture des parachutes, détectée par **V < 250 m/s** (cette condition survient toujours avant h = 10 km, la vitesse terminale y étant ~150 m/s).

Paramètres de mission (imposés, modifiables dans la page Mission) : vitesse d'entrée V_E = 11 km/s, masse de la capsule hors bouclier m_c = 5 000 kg, diamètre minimal habitable D_min = 3 m, limites n ≤ 10 g et T_s ≤ 250 °C.

### Paramètres d'action (PA) et plages du plan d'expériences

| PA | Symbole | Plage DOE | Bornes en optimisation | Rôle |
|---|---|---|---|---|
| Angle d'entrée | γ_E | −4,5° à −7° | idem | trajectoire (guidage) |
| Diamètre | D | 2,5 à 5 m | **D_min (3 m)** à 5 m | géométrie ; borne basse = volume habitable, borne haute = coiffe du lanceur |
| Émoussement du bouclier | R_n/D | 0,5 à 1,5 | idem | R_n = (R_n/D)·D ; borne basse = calotte géométriquement possible, borne haute = stabilité statique (Apollo ≈ 1,2) |
| Épaisseur d'ablateur | e | 1 à 6 cm | idem | dimensionnement thermique |
| Masse capsule hors bouclier | m_c | 3 à 8 t | **fixée** (5 t) | paramètre de mission |

m_c et D descendent sous les valeurs de mission dans le DOE pour que le métamodèle reste valable si l'utilisateur change la mission dans l'application.

### Paramètres d'évaluation (PE)

| PE | Symbole | Usage |
|---|---|---|
| Rebond hors de l'atmosphère | booléen | contrainte : **aucun rebond** |
| Décélération maximale | n_max (g) | contrainte **≤ 10 g** ; 2ᵉ objectif du Pareto |
| Flux thermique max au point d'arrêt | q̇_max (MW/m²) | analyse |
| Chaleur totale reçue | Q (MJ/m²) | dimensionne l'ablation |
| Épaisseur résiduelle après ablation | e_res | contrainte **> 0** (pas de percement) |
| Température de la structure | T_s (°C) | contrainte **≤ 250 °C** |
| Masse du bouclier | m_b (kg) | **objectif à minimiser** |
| Durée de rentrée, portée, durée de chauffe | t, s, t_ch | information |

### Ce que la vérification numérique a montré (ordres de grandeur, m_c = 5 t, R_n/D = 1,2)

| D | Rebond si γ_E au-dessus de | Couloir n ≤ 10 g | m_b le long du couloir |
|---|---|---|---|
| 3,0 m | −5,4° | −5,5° → −6,0° | 290 → 189 kg (5,5 → 3,6 %) |
| 3,9 m | −5,3° | −5,4° → −5,8° | 344 → 295 kg |
| 5,0 m | −5,1° | −5,2° → −5,7° | 565 → 455 kg |

Lectures attendues, toutes à faire apparaître dans l'application :
- **Le couloir est étroit (~0,5°) et se décale avec D** (capsule plus grande → coefficient balistique plus faible → freine plus haut → peut entrer plus rasante).
- **En bordure du rebond**, la capsule « ricoche » partiellement : la chauffe dure très longtemps (t_ch > 1 000 s) et l'épaisseur nécessaire double. Le bord rasant du couloir est donc coûteux en bouclier, le bord raide coûteux en g.
- **m_b ∝ D²** : l'optimum tend vers D = D_min ; **R_n/D** tend vers sa borne haute (q̇ ∝ 1/√R_n). Ces optimums **en butée** sont des résultats d'ingénieur normaux, à expliquer (contraintes de volume habitable et de stabilité saturées).
- **Front de Pareto m_b / n_max** : à D = D_min, de ~6,5 g pour ~203 kg à ~10 g pour ~189 kg. Amplitude modeste (~7 % sur la masse) mais réelle ; le message est « chaque gramme gagné se paie en g pour l'équipage ».

## 3. Objectifs, non-objectifs, anti-objectifs

**Objectifs**
1. Une application Streamlit en ligne qui montre toute la chaîne de la section 1, utilisable par l'enseignant sans aide.
2. Un simulateur **validé** contre une solution analytique de référence (Allen-Eggers, sur un cas d'orbite basse — voir §6.4).
3. Des métamodèles comparés honnêtement (jeu de test, R², RMSE, MAE, graphe de parité), y compris un **classifieur du rebond**.
4. Une solution optimale **re-vérifiée par la simulation**, avec l'écart métamodèle / simulation affiché.
5. Un socle complet **à la fin de la séance 2**, la séance 3 étant réservée au déploiement, au manuel, à la soutenance et aux extensions.

**Non-objectifs**
- Réalisme industriel : pas de Terre en rotation, atmosphère exponentielle (pas d'US76), pas de chimie hors équilibre, **pas de flux radiatif** (non négligeable à 11 km/s — limite à citer), pas de CFD ni d'éléments finis.
- Rentrée portante, guidage, précision d'atterrissage (au mieux en extension).

**Anti-objectifs** (échec même si « ça marche »)
- Des résultats non validés présentés comme vrais.
- Une application qui ne s'ouvre pas à l'URL le jour de la remise, ou qui recalcule pendant plusieurs minutes au démarrage.
- **Du code que l'étudiant ne sait pas expliquer** : le module l'exige. Code simple, commenté en français, sans bibliothèque lourde (pas de TensorFlow/PyTorch).
- Un métamodèle qui extrapole hors du domaine du plan d'expériences sans avertissement, ou un optimum proposé dans la zone de rebond sans que la vérification le signale.

## 4. Contraintes

- **Temps** : 9 h en séance, un seul étudiant (travail hors séance possible mais non supposé).
- **Pile imposée** : Python + Streamlit (bibliothèques scientifiques libres). Python 3.14, numpy 2.4 et scipy 1.17 sont déjà installés sur le poste.
- **Déploiement** : Streamlit Community Cloud → dépôt GitHub public.
- **Code modulaire** (consigne du sujet) : remplacer un module sans reconstruire l'application — c'est ce qui rend l'extension « conduction » possible.

## 5. Approches considérées

### 5.1 Fidélité du simulateur

| Approche | Principe | Pour | Contre |
|---|---|---|---|
| 1. Tout analytique | Formules d'Allen-Eggers, bouclier déduit de Q | 1 h, zéro risque | Ne voit pas le rebond, faux à 11 km/s (écart ×3 à ×5 constaté), pas de trajectoire à montrer |
| **2. Trajectoire simulée + bouclier analytique** ✅ | ODE 2D (`solve_ivp`), Sutton-Graves, bouclier = ablation + conduction semi-infinie (erfc) | ~150 lignes, capte le rebond, visuels riches, justifie le métamodèle | Modèle de bouclier simplifié, à assumer |
| 3. Option 2 + conduction 1D par différences finies | Température dans le bouclier calculée numériquement | Lien GM4 fort, T_s plus crédible | +2 h, risque numérique ; seul, peut faire déborder la séance 2 |

**Choix de l'étudiant : option 2 en socle, option 3 en première extension.**

### 5.2 Mission imposée

| Mission | Pour | Contre |
|---|---|---|
| Orbite basse (7,8 km/s) | Validation Allen-Eggers directe, très robuste | **Aucun rebond possible sans portance** (V_E < vitesse circulaire), n_max ≥ 8 g partout, D sans effet sur la fenêtre, démonstration plus terne |
| **Retour lunaire (11 km/s)** ✅ | Couloir réel (rebond / 10 g), D déplace le couloir, fort effet en soutenance | Allen-Eggers inapplicable → validation sur un cas orbite basse ; frontière de rebond discontinue à apprendre |

**Choix de l'étudiant : retour lunaire.** L'orbite basse reste présente comme **cas de validation** (même code, seule V_E change).

## 6. Modèle physique (socle)

### 6.1 Trajectoire — point matériel, Terre sphérique non tournante, sans portance

État : altitude h, vitesse V, pente γ (négative en descente), distance au sol s.

```
dV/dt = −D_a/m − g·sin γ
dγ/dt = (V/(R_T+h) − g/V)·cos γ
dh/dt = V·sin γ
ds/dt = V·cos γ · R_T/(R_T+h)

D_a = ½ ρ V² C_D A,   A = π D²/4,   m = m_c + m_b
ρ(h) = ρ0·exp(−h/H),  ρ0 = 1,225 kg/m³,  H = 7 200 m
g(h) = g0·(R_T/(R_T+h))²,  g0 = 9,81 m/s²,  R_T = 6 371 km
C_D = 1,4 (constant)
```

Événements `solve_ivp` (`max_step` ≈ 1 s) :
- **succès** : V < 250 m/s (terminal) ;
- **rebond** : h repasse au-dessus de 121 km avec dh/dt > 0 (terminal, direction +1) ;
- garde-fou : t > 3 000 s.

Grandeurs dérivées : n(t) = D_a/(m·g0), β = m/(C_D·A). Coût mesuré : ~25 ms par simulation.

### 6.2 Flux thermique — Sutton-Graves (point d'arrêt, convectif)

```
q̇ = k·√(ρ/R_n)·V³,   k = 1,7415·10⁻⁴ (SI, air),   R_n = (R_n/D)·D
Q = ∫ q̇ dt
```

### 6.3 Bouclier thermique — ablateur dense type Apollo/Orion (analytique)

Constantes (toutes dans `core/constantes.py`) : ρ_b = 510 kg/m³, k_b = 0,3 W/(m·K), c_p = 1 500 J/(kg·K) → α = k_b/(ρ_b c_p) ; structure support m_sup = 15 kg/m² ; chaleur effective d'ablation H_eff = 30 MJ/kg ; front de pyrolyse T_p = 900 K ; T0 = 300 K.

```
m_b   = (ρ_b·e + m_sup)·A                    bouclier frontal assimilé à un disque de diamètre D
e_abl = Q / (ρ_b · H_eff)                    épaisseur consommée par l'ablation
e_res = e − e_abl                            (≤ 0 → percement → infaisable)
t_ch  = durée pendant laquelle q̇ > 5 % de q̇_max
T_s   = T0 + (T_p − T0)·erfc( e_res / (2√(α·t_ch)) )    conduction en milieu semi-infini
```

Le module expose une interface unique, par exemple `evaluer_bouclier(t, q, e, constantes) → {e_abl, e_res, T_s, m_b}`, pour que l'extension « différences finies » s'y substitue.

Hypothèses **assumées explicitement** dans l'application et le manuel : surface interne à T_p pendant t_ch, milieu semi-infini, pas de « soak » post-rentrée, pas de flux radiatif, bouclier frontal seul (pas de bouclier arrière).

### 6.4 Validation — Allen-Eggers (balistique, γ constant, orbite basse)

```
n_max  = V_E² · |sin γ_E| / (2·e·H·g0)                      (e = nombre d'Euler)
q̇_max  = k · √( β·|sin γ_E| / (3·H·R_n) ) · V_E³ · e^(−1/2)
```

La page Simulation propose un **cas de validation orbite basse** (V_E = 7,8 km/s, γ_E de −1° à −7°) et superpose simulation et formules. Écarts constatés : n_max ~9 % à −6°, ~30 % à −3°, ×3 à −1° ; q̇_max ~5 % aux angles raides. Message : la formule n'est valable que pour les entrées raides et sous-orbitales — pour le retour lunaire, elle se trompe d'un facteur 3 à 5, d'où la nécessité du simulateur.

## 7. Démarche données / IA

1. **Plan d'expériences** : Latin Hypercube (`scipy.stats.qmc`) sur les 5 PA, **≈ 2 000 points** (~1 min de calcul). CSV **pré-généré et versionné** (`data/doe_reference.csv`) pour un démarrage instantané en ligne ; la page permet de régénérer un petit plan.
2. **Analyse** : histogrammes, nuages de points, corrélations ; carte γ_E × D colorée rebond / trop de g / faisable (visualise le couloir) ; taux de faisabilité.
3. **Métamodèles** (scikit-learn), séparation 80/20 :
   - **classification** du rebond sur tous les points (régression logistique vs forêt aléatoire) — matrice de confusion ;
   - **régression** de n_max, q̇_max, Q, t_ch, T_s sur les points sans rebond (m_b est analytique, non appris) ;
   - modèles comparés : polynôme degré 2-3 (surface de réponse, Cours 2), forêt aléatoire, processus gaussien (ou MLP) ;
   - indicateurs : R², RMSE, MAE, erreur max, graphe de parité, importance des variables.
4. **Prédiction** : curseurs → prédiction instantanée (probabilité de rebond + PE), à côté du simulateur pour le même point, avec alerte hors domaine.
5. **Optimisation** (m_c fixée, D ≥ D_min), contraintes : P(rebond) prédite ≤ 0,05, n_max ≤ 10 g, T_s ≤ 250 °C, e_res > 0 :
   - **mono-objectif** min m_b — SLSQP (comme le Cours 3) avec plusieurs points de départ ; la frontière de rebond étant discontinue, la probabilité du classifieur sert de contrainte lisse ;
   - **multi-objectif** min (m_b, n_max) — NSGA-II (`pymoo`), qui gère bien les zones infaisables → front de Pareto ;
   - **vérification** : l'optimum et des points du front sont re-simulés ; affichage de l'écart métamodèle / simulation et du respect réel des contraintes (dont le rebond). Décision finale argumentée par l'ingénieur.

## 8. Application Streamlit (multipage, sur le modèle du TD1)

```
rentree-atmospherique/
├── app.py                        Accueil : sujet, démarche, navigation
├── pages/
│   ├── 1_Mission_et_capsule.py   système, schéma, PA/PE, paramètres de mission
│   ├── 2_Simulation.py           une rentrée : h(t), V(t), n(t), q̇(t), T_s ; onglet validation orbite basse
│   ├── 3_Plan_d_experiences.py   chargement/génération du DOE, exploration, carte du couloir
│   ├── 4_Metamodeles.py          classifieur rebond + régressions, comparaison, parité, importance
│   ├── 5_Prediction.py           curseurs → métamodèle vs simulateur
│   └── 6_Optimisation.py         SLSQP, Pareto NSGA-II, vérification
├── core/
│   ├── constantes.py             constantes physiques, matériau, missions (lunaire, orbite basse)
│   ├── trajectoire.py            atmosphère, équations, simuler(params, mission) → résultats
│   ├── bouclier.py               modèle thermique (interface unique, remplaçable)
│   ├── validation.py             formules d'Allen-Eggers
│   ├── doe.py                    LHS + simulation en lot
│   ├── metamodeles.py            entraînement / évaluation
│   └── optimisation.py           SLSQP + NSGA-II + vérification
├── data/doe_reference.csv
├── tests/                        pytest sur la physique
└── requirements.txt              streamlit, numpy, scipy, pandas, plotly, scikit-learn, pymoo
```

Graphiques Plotly. Calculs lourds mis en cache (`st.cache_data` / `st.cache_resource`).

**Tests minimaux de la physique** :
- la vitesse décroît globalement ;
- orbite basse γ_E = −6° : n_max à moins de 15 % d'Allen-Eggers ;
- orbite basse γ_E = −1° : pas de rebond ; lunaire γ_E = −4,5° : rebond ; lunaire γ_E = −6,5° : pas de rebond ;
- T_s décroît quand e augmente ; m_b = (ρ_b·e + m_sup)·A ;
- lunaire D = 3 m, R_n/D = 1,2, γ_E = −5,8° : n_max entre 5 et 10 g (ordre de grandeur du §2).

## 9. Périmètre : socle et extensions

### Socle (obligatoire)

| Séance | Contenu | Point de contrôle en fin de séance |
|---|---|---|
| **S1** | `constantes`, `trajectoire`, `bouclier`, `validation` + tests ; page Simulation ; génération du DOE de référence | Une rentrée lunaire simulée s'affiche, le cas orbite basse est validé ; CSV de 2 000 points produit |
| **S2** | Pages Plan d'expériences, Métamodèles, Prédiction, Optimisation ; Accueil et Mission | Chaîne complète jusqu'à l'optimum vérifié, en local |
| **S3 (début)** | Dépôt GitHub, déploiement Streamlit Cloud, captures, manuel PDF, support de présentation | URL fonctionnelle, exemples du manuel reproductibles |

### Extensions (S3 ou hors séance, par ordre de priorité)

1. **Conduction 1D par différences finies** (option 3) : remplace la formule erfc dans `bouclier.py`, flux q̇(t) réel en condition limite ; comparaison des deux modèles.
2. **Corridor et robustesse** : Monte-Carlo sur γ_E ± incertitude de guidage → probabilité de succès ; marge de l'optimum vis-à-vis du rebond et des 10 g.
3. **Menu de missions** : orbite basse (déjà codée pour la validation), entrée martienne (ρ0 ≈ 0,02 kg/m³, H ≈ 11,1 km, constante de Sutton-Graves martienne).
4. **Analyse de sensibilité** (importance par permutation, SHAP ou indices de Sobol).
5. **Rentrée portante** (L/D ≈ 0,3, comme Apollo) : élargit le couloir, baisse n_max, nouveau PA.
6. **Visualisation 3D / animation** de la trajectoire autour de la Terre.

## 10. Décisions prises par Claude (à vérifier par l'étudiant)

- Capsule **habitée, 3 personnes** ; m_c = 5 t ; D_min = 3 m ; limite 10 g.
- R_n paramétré par le rapport **R_n/D ∈ [0,5 ; 1,5]** (borne haute = stabilité).
- **Ablateur dense type Apollo/Orion** + 15 kg/m² de structure support ; bouclier frontal seul, assimilé à un disque.
- C_D = 1,4 constant ; limite structure 250 °C (composite) ; fin de phase à V < 250 m/s.
- Contrainte de rebond via la **probabilité du classifieur ≤ 0,05**.
- ~2 000 points LHS, CSV versionné ; trois familles de métamodèles.
- Pareto sur m_b et n_max.
- Code dans `rentree-atmospherique/` à la racine du dossier projet, versionné avec git et poussé sur GitHub. *Le dossier projet est synchronisé (Teams/OneDrive) : si la synchronisation gêne git, déplacer le code hors de ce dossier.*

## 11. Laissé au constructeur

- Nombre exact de points du DOE et réglages des modèles (démarrage de l'appli < 10 s en ligne).
- Choix entre processus gaussien et MLP comme troisième métamodèle.
- Mise en forme des pages, palette, schéma de la capsule.
- Tolérances de `solve_ivp`, gestion des cas dégénérés.
- Structure exacte du manuel PDF et de la présentation.
