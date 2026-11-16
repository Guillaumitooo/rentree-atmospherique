"""Génère le manuel d'utilisation PDF à partir des captures de l'application déployée.

Usage (outil de documentation, non nécessaire à l'application) :
    pip install reportlab pillow
    python docs/manuel/generer_manuel.py
Produit docs/manuel/manuel_utilisation.pdf.
"""
from pathlib import Path

from PIL import Image as ImagePIL
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (Image, KeepTogether, ListFlowable, ListItem, PageBreak, Paragraph,
                                SimpleDocTemplate, Spacer, Table, TableStyle)

ICI = Path(__file__).resolve().parent
CAPTURES = ICI / "captures"
SORTIE = ICI / "manuel_utilisation.pdf"
URL_APP = "https://rentree-atmospherique-dcy7sh25krunm468r2prcd.streamlit.app"
URL_GIT = "https://github.com/Guillaumitooo/rentree-atmospherique"

# --- Polices (Windows) : Segoe UI couvre γ, ≤, √, ² ; Consolas pour les commandes ---------------
POLICES = Path("C:/Windows/Fonts")
pdfmetrics.registerFont(TTFont("Texte", POLICES / "segoeui.ttf"))
pdfmetrics.registerFont(TTFont("Texte-Gras", POLICES / "segoeuib.ttf"))
pdfmetrics.registerFont(TTFont("Texte-Italique", POLICES / "segoeuii.ttf"))
pdfmetrics.registerFont(TTFont("Code", POLICES / "consola.ttf"))
pdfmetrics.registerFontFamily("Texte", normal="Texte", bold="Texte-Gras", italic="Texte-Italique",
                              boldItalic="Texte-Gras")

BLEU = colors.HexColor("#1f3b73")
GRIS = colors.HexColor("#5b6270")
FOND = colors.HexColor("#eef2f8")

S = {
    "titre": ParagraphStyle("titre", fontName="Texte-Gras", fontSize=26, leading=32, textColor=BLEU,
                            alignment=TA_CENTER, spaceAfter=10),
    "soustitre": ParagraphStyle("soustitre", fontName="Texte", fontSize=14, leading=19, textColor=GRIS,
                                alignment=TA_CENTER, spaceAfter=6),
    "h1": ParagraphStyle("h1", fontName="Texte-Gras", fontSize=17, leading=22, textColor=BLEU,
                         spaceBefore=6, spaceAfter=8, keepWithNext=1),
    "h2": ParagraphStyle("h2", fontName="Texte-Gras", fontSize=13, leading=17, textColor=BLEU,
                         spaceBefore=10, spaceAfter=5, keepWithNext=1),
    "corps": ParagraphStyle("corps", fontName="Texte", fontSize=10.2, leading=14.5, spaceAfter=6),
    "legende": ParagraphStyle("legende", fontName="Texte-Italique", fontSize=9, leading=12,
                              textColor=GRIS, alignment=TA_CENTER, spaceBefore=3, spaceAfter=10),
    "code": ParagraphStyle("code", fontName="Code", fontSize=9.2, leading=12.5, backColor=FOND,
                           borderPadding=5, leftIndent=6, rightIndent=6, spaceBefore=4, spaceAfter=8),
    "cellule": ParagraphStyle("cellule", fontName="Texte", fontSize=9, leading=11.5),
    "cellule_g": ParagraphStyle("cellule_g", fontName="Texte-Gras", fontSize=9, leading=11.5),
    "encadre": ParagraphStyle("encadre", fontName="Texte", fontSize=10, leading=14, backColor=FOND,
                              borderPadding=7, leftIndent=8, rightIndent=8, spaceBefore=6, spaceAfter=10),
}


def p(texte, style="corps"):
    return Paragraph(texte, S[style])


def puces(elements):
    return ListFlowable([ListItem(p(e), leftIndent=12, value="•") for e in elements], bulletType="bullet",
                        start="•", leftIndent=14, bulletFontName="Texte", spaceAfter=6)


def etapes(elements):
    return ListFlowable([ListItem(p(e), leftIndent=14) for e in elements], bulletType="1",
                        leftIndent=16, bulletFontName="Texte-Gras", spaceAfter=6)


def tableau(lignes, largeurs, entete=True):
    donnees = [[p(str(c), "cellule_g" if (entete and i == 0) else "cellule") for c in ligne]
               for i, ligne in enumerate(lignes)]
    t = Table(donnees, colWidths=[l * cm for l in largeurs], repeatRows=1 if entete else 0)
    style = [("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#c9cfda")),
             ("VALIGN", (0, 0), (-1, -1), "TOP"),
             ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]
    if entete:
        style.append(("BACKGROUND", (0, 0), (-1, 0), FOND))
    t.setStyle(TableStyle(style))
    return t


def figure(nom, legende, largeur_max=16.5, hauteur_max=17.5):
    """Capture redimensionnée pour tenir dans la page, avec sa légende."""
    chemin = CAPTURES / f"{nom}.png"
    l, h = ImagePIL.open(chemin).size
    echelle = min(largeur_max * cm / l, hauteur_max * cm / h)
    img = Image(str(chemin), width=l * echelle, height=h * echelle)
    img.hAlign = "CENTER"
    return KeepTogether([img, p(legende, "legende")])


def pied_de_page(canvas, doc):
    canvas.saveState()
    canvas.setFont("Texte", 8)
    canvas.setFillColor(GRIS)
    canvas.drawString(2 * cm, 1.2 * cm, "Manuel d'utilisation — Capsule de rentrée atmosphérique")
    canvas.drawRightString(A4[0] - 2 * cm, 1.2 * cm, f"page {doc.page}")
    canvas.restoreState()


def contenu():
    c = []
    # --- Page de titre ---------------------------------------------------------------------------
    c += [Spacer(1, 3 * cm), p("Manuel d'utilisation", "soustitre"),
          p("Conception d'une capsule de rentrée atmosphérique", "titre"),
          p("Retour lunaire : enfiler l'aiguille à 11 km/s", "soustitre"), Spacer(1, 1 * cm),
          figure("01_accueil", "Page d'accueil de l'application", hauteur_max=9), Spacer(1, 0.8 * cm),
          p("Projet GM5 « Optimisation de la conception avec l'IA » — INSA Strasbourg, 2026-2027", "soustitre"),
          p("Guillaume Vicario", "soustitre"), Spacer(1, 0.6 * cm),
          tableau([["Application en ligne", f'<link href="{URL_APP}" color="blue">{URL_APP}</link>'],
                   ["Code source", f'<link href="{URL_GIT}" color="blue">{URL_GIT}</link>']],
                  [4, 12.5], entete=False),
          PageBreak()]

    # --- 1. Présentation -------------------------------------------------------------------------
    c += [p("1. Présentation", "h1"),
          p("<b>Question technique.</b> Une capsule habitée revient de la Lune à 11 km/s. Elle doit entrer "
            "dans l'atmosphère avec le bon angle : <b>trop rasante, elle rebondit</b> sur l'atmosphère et repart "
            "dans l'espace ; <b>trop raide, l'équipage dépasse 10 g</b>. Entre les deux se trouve un couloir "
            "d'environ 0,5°. Quel est le <b>bouclier thermique le plus léger</b> qui garde la structure sous "
            "250 °C, pour une capsule de 5 t hors bouclier ?"),
          p("L'application suit la démarche du module : un <b>simulateur physique</b> produit des essais "
            "numériques, des <b>métamodèles</b> apprennent à les reproduire instantanément, un "
            "<b>optimiseur</b> cherche la meilleure conception sur ces métamodèles, et chaque solution est "
            "<b>vérifiée par simulation</b>. L'IA propose, la physique vérifie, l'ingénieur décide."),
          p("Paramètres d'action (ce que l'on conçoit)", "h2"),
          tableau([["Paramètre", "Domaine étudié", "Rôle"],
                   ["Angle d'entrée γ_E", "−7° à −4,5°", "trajectoire (guidage)"],
                   ["Diamètre D", "2,5 à 5 m", "géométrie ; D ≥ D_min habitable (3 m)"],
                   ["Émoussement R_n/D", "0,5 à 1,5", "forme du bouclier ; borne haute = stabilité"],
                   ["Épaisseur d'ablateur e", "1 à 6 cm", "dimensionnement thermique"],
                   ["Masse hors bouclier m_c", "3 à 8 t", "paramètre de mission (5 t, fixé en optimisation)"]],
                  [4.3, 3.2, 9]),
          p("Paramètres d'évaluation (ce que l'on mesure)", "h2"),
          tableau([["Grandeur", "Usage"],
                   ["Rebond hors de l'atmosphère", "contrainte : aucun rebond"],
                   ["Décélération maximale n_max", "contrainte ≤ 10 g ; second objectif du front de Pareto"],
                   ["Flux thermique maximal, chaleur reçue Q", "analyse ; Q dimensionne l'ablation"],
                   ["Épaisseur résiduelle e_res", "contrainte : positive (pas de percement)"],
                   ["Température de structure T_s", "contrainte ≤ 250 °C"],
                   ["Masse du bouclier m_b", "objectif à minimiser"]],
                  [6.5, 10])]

    # --- 2. Accès et navigation ------------------------------------------------------------------
    c += [p("2. Accès et navigation", "h1"),
          puces([f"Ouvrir l'application à l'adresse <b>{URL_APP}</b> (aucune installation requise).",
                 "Si l'application dormait (pas de visite depuis plusieurs jours), Streamlit Cloud affiche un "
                 "bouton <b>« Yes, get this app back up! »</b> : cliquer et patienter environ une minute.",
                 "Le <b>menu de gauche</b> donne accès aux sept pages, dans l'ordre de la démarche.",
                 "Les réglages de la capsule se font dans la <b>barre latérale</b> (pages Simulation et Prédiction).",
                 "La <b>mission</b> choisie page 1 s'applique à toutes les pages ; les <b>modèles</b> choisis "
                 "page 4 sont utilisés par les pages Prédiction et Optimisation.",
                 "Au premier passage sur les pages Prédiction ou Optimisation, les métamodèles s'entraînent "
                 "(environ 15 s, indiqué à l'écran). Les visites suivantes sont instantanées."]),
          p("3. Les pages de l'application", "h1"),
          p("3.1 Mission et capsule", "h2"),
          p("Cette page présente le système étudié : tableaux des paramètres d'action et d'évaluation, et "
            "schéma de la capsule (bouclier en rouge) que l'on peut déformer avec les deux curseurs « Diamètre » "
            "et « R_n/D ». En bas, le formulaire <b>Paramètres de la mission</b> permet de modifier :"),
          puces(["le type de mission (retour lunaire ou orbite basse, qui sert de cas de validation) ;",
                 "la vitesse d'entrée, la masse hors bouclier, le diamètre minimal habitable ;",
                 "les limites de décélération et de température de structure."]),
          p("Cliquer sur <b>Appliquer</b> : un message confirme la mise à jour et la ligne « Mission "
            "courante » résume les valeurs actives. Changer de type de mission remet sa vitesse d'entrée par "
            "défaut. Une masse hors de 3 à 8 t déclenche un avertissement : les métamodèles devraient extrapoler."),
          figure("02_mission", "Figure 1 — Page Mission et capsule : paramètres, schéma et formulaire de mission",
                 hauteur_max=15),
          ]

    c += [p("3.2 Simulation", "h2"),
          p("La page simule <b>une rentrée</b> pour la capsule réglée dans la barre latérale (angle d'entrée, "
            "diamètre, émoussement, épaisseur d'ablateur ; la masse est celle de la mission). Elle affiche :"),
          puces(["un <b>bandeau de verdict</b> : faisable (vert), rebond ou percement (rouge), contrainte "
                 "violée (orange) ;",
                 "les <b>indicateurs</b> : décélération maximale, flux maximal, chaleur reçue, épaisseur "
                 "ablatée, température de structure et masse du bouclier ;",
                 "quatre <b>courbes</b> : altitude en fonction de la vitesse, décélération (limite en pointillés "
                 "rouges), flux thermique au point d'arrêt et trajectoire ;",
                 "le choix du <b>modèle thermique</b> du bouclier : analytique (milieu semi-infini) ou "
                 "différences finies 1D, avec une comparaison des deux températures obtenues."]),
          figure("03_simulation", "Figure 2 — Rentrée de référence (γ_E = −5,8°, D = 3 m, R_n/D = 1,2, e = 3 cm) : "
                 "faisable, 6,9 g, 138 °C, bouclier de 214 kg", hauteur_max=19),
          p("L'onglet <b>Validation (orbite basse)</b> compare le simulateur aux formules analytiques "
            "d'Allen-Eggers sur des entrées d'orbite basse de −1° à −7°. L'accord est bon pour les entrées "
            "raides (écart de l'ordre de 10 % à −6°) et se dégrade pour les entrées rasantes, où la gravité "
            "compte : c'est la justification du simulateur, d'autant que ces formules se trompent d'un facteur "
            "3 à 5 à 11 km/s."),
          figure("04_validation", "Figure 3 — Validation du simulateur par les formules d'Allen-Eggers",
                 hauteur_max=13),
          ]

    c += [p("3.3 Plan d'expériences", "h2"),
          p("Les essais physiques sont remplacés par <b>2 000 simulations</b> réparties par Latin Hypercube "
            "dans le domaine étudié. Les quatre compteurs classent les points : 265 faisables (13,2 %), 715 "
            "rebonds (35,8 %), 876 au-delà de 10 g (43,8 %) et 144 au bouclier insuffisant (7,2 %). Les "
            "onglets proposent :"),
          puces(["<b>Couloir d'entrée</b> : chaque capsule simulée dans le plan (angle, diamètre). La bande "
                 "verte étroite est le couloir : à droite la capsule rebondit, à gauche la décélération est "
                 "trop forte. Le couloir se décale vers les angles rasants quand le diamètre augmente ;",
                 "<b>Distributions</b>, <b>Corrélations</b> et <b>Tableau</b> pour explorer les données ;",
                 "le bouton <b>Télécharger les données (CSV)</b> ;",
                 "l'option <b>Petit plan personnalisé</b> : générer et simuler 20 à 200 points pour la mission "
                 "courante (utile pour l'orbite basse)."]),
          figure("05_plan_experiences", "Figure 4 — Plan d'expériences : le couloir d'entrée apparaît en vert",
                 hauteur_max=14),
          ]

    c += [p("3.4 Métamodèles", "h2"),
          p("Un métamodèle répond en quelques millisecondes au lieu de ~25 ms par simulation. Les données "
            "sont séparées en 80 % d'apprentissage et 20 % de test : les scores sont mesurés sur des points "
            "jamais vus."),
          etapes(["Choisir la <b>grandeur à prédire</b> (décélération, flux, chaleur reçue, durée de chauffe, "
                  "température) et le <b>modèle</b> (polynôme de degré 2 ou 3, forêt aléatoire, processus "
                  "gaussien).",
                  "Lire les scores (R², RMSE, MAE, erreur maximale), le <b>graphe de parité</b> (points proches "
                  "de la diagonale = bonnes prédictions) et l'<b>importance des variables</b>.",
                  "Cliquer sur <b>Comparer sur cette grandeur</b> pour classer les quatre modèles.",
                  "Onglet <b>Classification du rebond</b> : choisir le classifieur et lire l'exactitude et la "
                  "matrice de confusion."]),
          p("Les modèles choisis ici sont ceux qu'utilisent les pages Prédiction et Optimisation. Par défaut : "
            "processus gaussien (R² = 0,9992 sur la décélération) et régression logistique (99,75 % "
            "d'exactitude sur le rebond). La température de structure finale provient d'un <b>modèle hybride</b> : "
            "le métamodèle prédit la chaleur reçue et la durée de chauffe, puis la formule physique du bouclier "
            "calcule la température (plus précis près de la limite de 250 °C)."),
          figure("06_metamodeles", "Figure 5 — Processus gaussien sur la décélération maximale : parité et "
                 "importance des variables (l'angle d'entrée domine)", hauteur_max=13.5),
          figure("07_classification", "Figure 6 — Classifieur du rebond : 99,75 % d'exactitude sur le jeu de test",
                 hauteur_max=8),
          ]

    c += [p("3.5 Prédiction", "h2"),
          p("Régler la capsule dans la barre latérale : la page affiche côte à côte la <b>prédiction du "
            "métamodèle</b> et le <b>résultat du simulateur</b> pour le même point, avec l'écart et les temps "
            "de calcul. Un avertissement apparaît si le point ou la mission sort du domaine du plan "
            "d'expériences : la prédiction n'est alors pas fiable et seule la simulation fait foi."),
          figure("08_prediction", "Figure 7 — Prédiction contre simulation pour la capsule de référence : "
                 "écarts de 0,11 g et 1 °C", hauteur_max=9),
          p("3.6 Optimisation", "h2"),
          p("L'optimiseur cherche sur le métamodèle, puis chaque solution est re-simulée. L'optimum se situe "
            "toujours sur les limites : on règle donc d'abord deux <b>marges de sécurité</b> (par défaut 0,5 g "
            "et 20 °C) que l'optimiseur doit respecter en plus des limites de la mission."),
          etapes(["Onglet <b>Masse minimale</b> : cliquer sur <b>Lancer l'optimisation</b> (quelques "
                  "secondes). La page affiche la conception optimale, puis le tableau <b>Vérification par "
                  "simulation</b> : valeur prédite, valeur simulée, écart, limite et respect de chaque "
                  "contrainte. Un bandeau vert confirme la solution ; un bandeau rouge l'invalide.",
                  "Onglet <b>Front de Pareto</b> : cliquer sur <b>Calculer le front de Pareto</b>. L'algorithme "
                  "génétique NSGA-II trace les compromis entre masse du bouclier et décélération ; cinq points "
                  "répartis sur le front sont re-simulés (cercles verts s'ils sont validés)."]),
          figure("09_optimisation_masse", "Figure 8 — Masse minimale : 185 kg, confirmée par la simulation "
                 "(9,53 g et 228 °C)", hauteur_max=15),
          p("Le message « Optimum en butée » explique deux résultats normaux : le diamètre est à son minimum "
            "habitable (la masse du bouclier croît comme D²) et l'émoussement à son maximum (le flux décroît "
            "comme 1/√R_n), la borne traduisant la limite de stabilité de la capsule."),
          figure("10_pareto", "Figure 9 — Front de Pareto masse du bouclier / décélération, avec cinq points "
                 "re-simulés", hauteur_max=16),
          ]

    # --- 4. Exemple reproductible ----------------------------------------------------------------
    c += [PageBreak(), p("4. Exemple complet reproductible", "h1"),
          p("Cet exemple reprend les captures de ce manuel. Partir d'une session neuve (recharger la page) pour "
            "avoir les réglages par défaut. Les valeurs obtenues doivent correspondre à l'arrondi près."),
          etapes(["Page <b>1. Mission et capsule</b> : laisser la mission par défaut (retour lunaire, "
                  "11 000 m/s, 5 000 kg, D_min = 3 m, 10 g, 250 °C).",
                  "Page <b>2. Simulation</b> : garder les curseurs par défaut (γ_E = −5,8°, D = 3 m, "
                  "R_n/D = 1,2, e = 3 cm) et le modèle thermique analytique.",
                  "Page <b>3. Plan d'expériences</b> : constater le couloir vert entre −6° et −5,4° environ.",
                  "Page <b>4. Métamodèles</b> : laisser « Décélération max » et « Processus gaussien ».",
                  "Page <b>5. Prédiction</b> : comparer prédiction et simulation pour la même capsule.",
                  "Page <b>6. Optimisation</b> : marges par défaut, cliquer sur « Lancer l'optimisation », puis "
                  "calculer le front de Pareto."]),
          tableau([["Étape", "Grandeur", "Valeur attendue"],
                   ["2. Simulation", "verdict", "rentrée faisable"],
                   ["", "décélération max / flux max", "6,9 g / 2,12 MW/m²"],
                   ["", "chaleur reçue / ablation", "205 MJ/m² / 1,34 cm"],
                   ["", "température de structure / masse du bouclier", "138 °C / 214 kg"],
                   ["3. Plan d'expériences", "points faisables / rebonds", "265 (13,2 %) / 715 (35,8 %)"],
                   ["4. Métamodèles", "R² décélération (processus gaussien)", "0,9992"],
                   ["", "exactitude du classifieur (régression logistique)", "99,75 %"],
                   ["5. Prédiction", "décélération prédite / simulée", "7,06 g / 6,95 g"],
                   ["", "température prédite / simulée", "136 °C / 138 °C"],
                   ["6. Optimisation", "γ_E / D / R_n/D / e", "−5,97° / 3,00 m / 1,50 / 2,18 cm"],
                   ["", "masse du bouclier", "185 kg"],
                   ["", "vérification : décélération / température", "9,53 g / 228 °C, confirmée"]],
                  [3.6, 7.2, 5.7]),
          Spacer(1, 0.3 * cm),
          p("<b>Ce que montre l'exemple.</b> La capsule de référence est faisable mais lourde (214 kg). "
            "L'optimisation descend à 185 kg (−14 %) en rendant l'entrée plus raide (−5,97°), juste sous la "
            "limite de décélération avec sa marge, en réduisant l'épaisseur d'ablateur à 2,18 cm et en "
            "émoussant le bouclier au maximum. La simulation confirme toutes les contraintes.", "encadre"),
          ]

    # --- 5. Limites et bonnes pratiques ----------------------------------------------------------
    c += [p("5. Limites du modèle et bonnes pratiques", "h1"),
          puces(["Point matériel, Terre sphérique non tournante, atmosphère exponentielle, rentrée "
                 "balistique (sans portance), coefficient de traînée constant.",
                 "Flux convectif au point d'arrêt (Sutton-Graves) ; le flux radiatif, non négligeable à 11 km/s, "
                 "est ignoré.",
                 "Bouclier : ablation par chaleur effective et conduction en milieu semi-infini. Le modèle par "
                 "différences finies (face arrière adiabatique, plus prudent) donne des températures nettement "
                 "plus élevées : avec lui, l'optimum à 185 kg dépasserait 250 °C et il faudrait environ 2,7 cm "
                 "d'ablateur. Le choix du modèle thermique est donc une décision d'ingénieur à justifier.",
                 "Les métamodèles ne sont valables que dans le domaine du plan d'expériences (retour lunaire, "
                 "plages du tableau de la section 1) : l'application avertit dès qu'on en sort.",
                 "Une solution n'est retenue que si la <b>vérification par simulation</b> la confirme. En cas "
                 "de refus, augmenter les marges de sécurité."]),
          p("Annexe — Lancer l'application en local", "h1"),
          p("Le code complet est disponible sur GitHub. Avec Python 3.12 ou plus récent :"),
          p(f"git clone {URL_GIT}.git<br/>cd rentree-atmospherique<br/>python -m venv .venv<br/>"
            ".venv\\Scripts\\activate<br/>pip install -r requirements.txt<br/>streamlit run Accueil.py", "code"),
          p("La suite de tests (physique, IA, optimisation et pages) se lance avec <font name='Code'>pytest</font> "
            "et le plan d'expériences se régénère avec <font name='Code'>python scripts/generer_doe.py</font>."),
          ]
    return c


if __name__ == "__main__":
    doc = SimpleDocTemplate(str(SORTIE), pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm,
                            topMargin=1.8 * cm, bottomMargin=2 * cm,
                            title="Manuel d'utilisation — Capsule de rentrée atmosphérique",
                            author="Guillaume Vicario", subject="Projet GM5 — INSA Strasbourg")
    doc.build(contenu(), onFirstPage=pied_de_page, onLaterPages=pied_de_page)
    print(f"Manuel généré : {SORTIE}")
