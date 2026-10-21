"""
Module de peuplement (Seed) des Patronymes (Jamu) et Prénoms du Mali.

Règle éditoriale : on n'écrit QUE ce qui est attesté par la tradition orale
reconnue (griots, épopée de Soundiata) ou par l'histoire documentée.
- Quand une étymologie est une explication populaire, elle est présentée comme telle.
- Quand le sens d'un nom n'est pas établi, on le dit clairement au lieu d'inventer.
- Les champs `totem` (tana) et `senankouya` restent vides s'il n'existe pas
  d'information fiable et générale (ils varient souvent selon les lignages).
"""

import json
import logging
from datetime import UTC, datetime

from backend.src.db.models import CultureNom
from sqlalchemy.orm import Session

logger = logging.getLogger("AlternIA.NomsSeed")

SENS_NON_ETABLI = "Son sens littéral n'est pas établi de façon fiable."
PACTE_PEULS_FORGERONS = (
    "Les forgerons (numu : Kanté, Doumbia, Fané…), selon le grand pacte de "
    "cousinage à plaisanterie entre Peuls et forgerons."
)
PACTE_FORGERONS_PEULS = (
    "Les Peuls (Diallo, Diakité, Sidibé, Sangaré…), selon le grand pacte de "
    "cousinage à plaisanterie entre forgerons et Peuls."
)


NOMS_DATA = [
    # ══════════════════════════════════════════════════════════════════════════
    # 1. PATRONYMES (JAMU)
    # ══════════════════════════════════════════════════════════════════════════
    {
        "id": "nom_keita",
        "nom": "Keïta",
        "nom_normalise": "keita",
        "type": "nom",
        "ethnie_ou_region": "Mandé (Niani, Kangaba, Kita) — Malinké",
        "signification": (
            "Selon l'explication la plus répandue chez les griots, Keïta viendrait de "
            "« kè ita » : « prendre l'héritage », c'est-à-dire « celui qui a reçu l'héritage »."
        ),
        "clan_role": "Lignée royale du Mandé : la dynastie des Mansa de l'Empire du Mali (Soundiata Keïta, Mansa Moussa).",
        "totem": "",
        "senankouya": "Coulibaly (le pacte Keïta–Coulibaly est l'un des plus connus du Mali).",
        "devise_ou_louange": "« Keïta, descendants de Soundiata, le lion du Mandé ! »",
        "anecdote": (
            "Soundiata Keïta, fils de Naré Maghan Kon Fatta et de Sogolon Kédjou, vainquit Soumaoro Kanté "
            "à Kirina (vers 1235) et fonda l'Empire du Mali ; la tradition lui attribue la Charte de Kouroukan Fouga. "
            "Depuis Balla Fasséké, les griots Kouyaté sont les griots attitrés des Keïta."
        ),
        "variantes": ["Keita", "Keïta", "Kéita", "Keyta"],
    },
    {
        "id": "nom_traore",
        "nom": "Traoré",
        "nom_normalise": "traore",
        "type": "nom",
        "ethnie_ou_region": "Mandé, Kénédougou (Sikasso) et tout l'espace mandingue",
        "signification": (
            "Traoré est la forme francisée de Tarawele. Une étymologie populaire rapportée par les griots "
            "y voit « tara wele » (« va l'appeler »), en souvenir du guerrier qu'on allait chercher dans les "
            "moments de péril ; ce sens reste une tradition, pas une certitude."
        ),
        "clan_role": (
            "Clan noble guerrier du Mandé, issu selon l'épopée de Tiramakan Traoré, général de Soundiata. "
            "Au XIXe siècle, des Traoré régnèrent sur le royaume du Kénédougou (Sikasso)."
        ),
        "totem": "",
        "senankouya": "Diarra (le pacte Traoré–Diarra est l'un des plus célèbres du Mali).",
        "devise_ou_louange": "« Tarawele, descendants de Tiramakan ! »",
        "anecdote": (
            "Après Kirina, Tiramakan Traoré mena la conquête de l'ouest, jusqu'au Kaabu. "
            "En 1898, à Sikasso, le roi Babemba Traoré préféra la mort à la reddition face aux troupes coloniales ; "
            "on lui prête la parole « Plutôt la mort que la honte »."
        ),
        "variantes": ["Traore", "Traoré", "Tarawele", "Tarawally"],
    },
    {
        "id": "nom_coulibaly",
        "nom": "Coulibaly",
        "nom_normalise": "coulibaly",
        "type": "nom",
        "ethnie_ou_region": "Ségou, Kaarta et Bélédougou — Bambara",
        "signification": "« Sans pirogue », du bambara « kulun » (pirogue) et « bali » (sans, absence de).",
        "clan_role": "Fondateurs du royaume bambara de Ségou (Biton Coulibaly, début du XVIIIe siècle) et du royaume du Kaarta (les Massassi).",
        "totem": "Le silure (poisson-chat), qui selon la légende fit traverser le fleuve aux ancêtres du clan.",
        "senankouya": "Keïta.",
        "devise_ou_louange": None,
        "anecdote": (
            "La légende raconte que deux frères ancêtres du clan, Niangolo et Baramangolo, poursuivis par leurs ennemis, "
            "arrivèrent au bord du Niger sans pirogue. Un silure les fit traverser : d'où le nom « sans pirogue » "
            "et l'interdit de manger ce poisson. Plus tard, Biton Coulibaly transforma l'association des jeunes (ton) "
            "en armée et fit de Ségou un royaume puissant."
        ),
        "variantes": ["Coulibaly", "Koulibaly", "Kulibali"],
    },
    {
        "id": "nom_diakite",
        "nom": "Diakité",
        "nom_normalise": "diakite",
        "type": "nom",
        "ethnie_ou_region": "Wassoulou, Macina et Mandé — famille d'origine peule",
        "signification": (
            "Nom d'origine peule porté par des familles intégrées au monde mandingue ; la tradition le rattache "
            "au clan peul des Diallo. " + SENS_NON_ETABLI
        ),
        "clan_role": "Avec les Diallo, Sidibé et Sangaré, les Diakité forment dans la tradition du Wassoulou les « quatre frères » peuls.",
        "totem": "",
        "senankouya": PACTE_PEULS_FORGERONS,
        "devise_ou_louange": None,
        "anecdote": (
            "Au Wassoulou, Peuls et Malinké se sont tant mêlés que les Diakité, Sidibé et Sangaré parlent "
            "le malinké ou le bambara tout en revendiquant fièrement leur ascendance peule."
        ),
        "variantes": ["Diakite", "Diakité", "Diakhité", "Jakite"],
    },
    {
        "id": "nom_diallo",
        "nom": "Diallo",
        "nom_normalise": "diallo",
        "type": "nom",
        "ethnie_ou_region": "Macina, Sahel et toute l'Afrique de l'Ouest — Peul",
        "signification": "Forme de « Jallo », l'un des grands clans peuls (Jallube), aux côtés des Bâ, Sow et Barry. " + SENS_NON_ETABLI,
        "clan_role": "Clan peul parmi les plus répandus, du Macina au Fouta-Djalon.",
        "totem": "",
        "senankouya": PACTE_PEULS_FORGERONS,
        "devise_ou_louange": None,
        "anecdote": (
            "Les Diallo, comme tous les Peuls, se réfèrent au pulaaku, le code de conduite peul fondé sur "
            "la retenue (semteende), la patience (munyal) et la sagesse (hakkille)."
        ),
        "variantes": ["Diallo", "Jallo", "Djallo"],
    },
    {
        "id": "nom_toure",
        "nom": "Touré",
        "nom_normalise": "toure",
        "type": "nom",
        "ethnie_ou_region": "Boucle du Niger (Tombouctou, Gao), pays soninké et mandingue",
        "signification": "Patronyme d'origine soninké et mandingue. " + SENS_NON_ETABLI,
        "clan_role": "Nombreuses familles maraboutiques et commerçantes ; la tradition nomme Mohammed Touré le fondateur de la dynastie des Askia.",
        "totem": "",
        "senankouya": "Cissé (selon plusieurs traditions).",
        "devise_ou_louange": None,
        "anecdote": (
            "Askia Mohammed, appelé Mohammed Touré par la tradition, prit le pouvoir dans l'Empire songhaï en 1493. "
            "Sous son règne, Tombouctou et ses mosquées-universités (Sankoré, Djingareyber) connurent un grand rayonnement intellectuel."
        ),
        "variantes": ["Toure", "Touré", "Ture"],
    },
    {
        "id": "nom_cisse",
        "nom": "Cissé",
        "nom_normalise": "cisse",
        "type": "nom",
        "ethnie_ou_region": "Ancien Ghana / Wagadou (Nara, Nioro, Kayes) — Soninké",
        "signification": "Patronyme soninké lié à l'ancien royaume du Wagadou. " + SENS_NON_ETABLI,
        "clan_role": "Selon la tradition soninké, les Cissé (Cissé Tounkara) fournissaient les rois du Wagadou, l'ancien Ghana.",
        "totem": "",
        "senankouya": "Touré (selon plusieurs traditions).",
        "devise_ou_louange": None,
        "anecdote": (
            "Selon la légende du Wagadou, la prospérité du royaume dépendait du serpent Bida, à qui l'on offrait "
            "chaque année une jeune fille. Quand Mamadi le Taciturne tua le serpent pour sauver sa fiancée Sia Yatabaré, "
            "la pluie d'or cessa, le Wagadou déclina et les Soninké se dispersèrent."
        ),
        "variantes": ["Cisse", "Cissé", "Sissé", "Cissey"],
    },
    {
        "id": "nom_diarra",
        "nom": "Diarra",
        "nom_normalise": "diarra",
        "type": "nom",
        "ethnie_ou_region": "Ségou, Kaarta et Bélédougou — Bambara",
        "signification": "« Le lion », du bambara « jara ».",
        "clan_role": "Dynastie qui régna sur le royaume bambara de Ségou après les Coulibaly, fondée par Ngolo Diarra vers 1766.",
        "totem": "",
        "senankouya": "Traoré.",
        "devise_ou_louange": "« Diarra, jara : le lion ! »",
        "anecdote": (
            "Ngolo Diarra, ancien captif de la cour de Biton Coulibaly, prit le pouvoir à Ségou. Son fils Monzon Diarra, "
            "puis son petit-fils Da Monzon Diarra, portèrent le royaume à son apogée au tournant du XIXe siècle."
        ),
        "variantes": ["Diarra", "Jara", "Jarra"],
    },
    {
        "id": "nom_camara",
        "nom": "Camara",
        "nom_normalise": "camara",
        "type": "nom",
        "ethnie_ou_region": "Mandé (Siby, Tabon, Kita) — Malinké",
        "signification": "Patronyme mandingue parmi les plus anciens. " + SENS_NON_ETABLI,
        "clan_role": "Clan noble du Mandé, réputé pour ses chasseurs ; les Camara de Siby et de Tabon figurent parmi les alliés de Soundiata.",
        "totem": "",
        "senankouya": "",
        "devise_ou_louange": None,
        "anecdote": (
            "Dans l'épopée, Kamandjan Camara, roi de Siby, rejoint Soundiata contre Soumaoro. "
            "Près de Siby, l'arche de pierre naturelle porte son nom : l'Arche de Kamandjan."
        ),
        "variantes": ["Camara", "Kamara"],
    },
    {
        "id": "nom_maiga",
        "nom": "Maïga",
        "nom_normalise": "maiga",
        "type": "nom",
        "ethnie_ou_region": "Gao, Bourem, Ansongo, Tombouctou — Songhaï",
        "signification": "Grand patronyme songhaï. " + SENS_NON_ETABLI,
        "clan_role": "Patronyme emblématique du pays songhaï, berceau de l'Empire de Gao.",
        "totem": "",
        "senankouya": "",
        "devise_ou_louange": None,
        "anecdote": "L'Empire songhaï, dont Gao était la capitale, domina la boucle du Niger aux XVe et XVIe siècles, sous Sonni Ali Ber puis les Askia.",
        "variantes": ["Maiga", "Maïga", "Mayga"],
    },
    {
        "id": "nom_sidibe",
        "nom": "Sidibé",
        "nom_normalise": "sidibe",
        "type": "nom",
        "ethnie_ou_region": "Wassoulou (Yanfolila, Bougouni) — famille d'origine peule",
        "signification": "Nom peul du Wassoulou, souvent considéré comme l'équivalent mandingue du patronyme peul Sow. " + SENS_NON_ETABLI,
        "clan_role": "L'un des « quatre frères » peuls du Wassoulou, avec les Diallo, Diakité et Sangaré.",
        "totem": "",
        "senankouya": PACTE_PEULS_FORGERONS,
        "devise_ou_louange": None,
        "anecdote": "Le Wassoulou, terre des Sidibé, Diakité et Sangaré, a donné naissance à la musique wassoulou, portée par des chanteuses comme Coumba Sidibé.",
        "variantes": ["Sidibe", "Sidibé"],
    },
    {
        "id": "nom_sangare",
        "nom": "Sangaré",
        "nom_normalise": "sangare",
        "type": "nom",
        "ethnie_ou_region": "Wassoulou, Macina — famille d'origine peule",
        "signification": "Nom peul, souvent rapproché du patronyme Barry ; on le retrouve sous les formes Sankara (Burkina Faso) ou Shagari (Nigeria). " + SENS_NON_ETABLI,
        "clan_role": "L'un des « quatre frères » peuls du Wassoulou, avec les Diallo, Diakité et Sidibé.",
        "totem": "",
        "senankouya": PACTE_PEULS_FORGERONS,
        "devise_ou_louange": None,
        "anecdote": "Oumou Sangaré, grande voix du Wassoulou, a fait connaître dans le monde entier la musique de cette région.",
        "variantes": ["Sangare", "Sangaré", "Sankare"],
    },
    {
        "id": "nom_samake",
        "nom": "Samaké",
        "nom_normalise": "samake",
        "type": "nom",
        "ethnie_ou_region": "Mandé et région de Bamako — Bambara",
        "signification": "Généralement expliqué par le bambara « sama » (éléphant) et « kɛ » (mâle) : « l'éléphant mâle ».",
        "clan_role": "Patronyme bambara du Mandé.",
        "totem": "",
        "senankouya": "",
        "devise_ou_louange": None,
        "anecdote": "L'éléphant, que le nom évoque, est dans les contes mandingues le symbole de la force tranquille.",
        "variantes": ["Samake", "Samaké"],
    },
    {
        "id": "nom_kouyate",
        "nom": "Kouyaté",
        "nom_normalise": "kouyate",
        "type": "nom",
        "ethnie_ou_region": "Mandé (Niagassola, Kita, Kangaba) — griots malinké",
        "signification": "Selon la tradition, le nom signifierait « il y a un secret entre nous », parole liée au lien unissant Balla Fasséké à son roi.",
        "clan_role": "Première lignée de griots (jeli) du Mandé, descendants de Balla Fasséké, griot de Soundiata ; griots attitrés des Keïta.",
        "totem": "",
        "senankouya": "",
        "devise_ou_louange": None,
        "anecdote": (
            "Balla Fasséké, captif chez Soumaoro Kanté, joua du Sosso-Bala, le balafon sacré du roi du Sosso. "
            "Ce balafon est aujourd'hui gardé par les Kouyaté à Niagassola (Guinée) et inscrit au patrimoine immatériel de l'UNESCO."
        ),
        "variantes": ["Kouyate", "Kouyaté", "Kuyate", "Kuyateh"],
    },
    {
        "id": "nom_diabate",
        "nom": "Diabaté",
        "nom_normalise": "diabate",
        "type": "nom",
        "ethnie_ou_region": "Mandé (Kéla, Kangaba, Kita) — griots malinké",
        "signification": "Grande lignée de griots. Plusieurs étymologies populaires circulent, mais aucune n'est établie.",
        "clan_role": "Griots (jeli) : les Diabaté de Kéla récitent l'histoire du Mandé lors du Kamablon de Kangaba.",
        "totem": "",
        "senankouya": "",
        "devise_ou_louange": None,
        "anecdote": (
            "Tous les sept ans, à Kangaba, on refait le toit de la case sacrée Kamablon ; les griots Diabaté de Kéla "
            "y récitent l'histoire du Mandé. Cette cérémonie est inscrite au patrimoine immatériel de l'UNESCO (2009). "
            "Le joueur de kora Toumani Diabaté est issu de cette tradition."
        ),
        "variantes": ["Diabate", "Diabaté", "Jobarteh"],
    },
    {
        "id": "nom_doumbia",
        "nom": "Doumbia",
        "nom_normalise": "doumbia",
        "type": "nom",
        "ethnie_ou_region": "Mandé, Bélédougou, Wassoulou — Malinké et Bambara",
        "signification": SENS_NON_ETABLI,
        "clan_role": (
            "Patronyme souvent associé aux forgerons (numu) ; la tradition rattache des Doumbia à Fakoli, "
            "neveu de Soumaoro Kanté devenu général de Soundiata."
        ),
        "totem": "",
        "senankouya": PACTE_FORGERONS_PEULS,
        "devise_ou_louange": None,
        "anecdote": "Selon l'épopée, Fakoli abandonna son oncle Soumaoro, qui lui avait pris son épouse Kéléya, et rejoignit Soundiata avec ses guerriers.",
        "variantes": ["Doumbia", "Dumbia", "Dumbuya"],
    },
    {
        "id": "nom_konate",
        "nom": "Konaté",
        "nom_normalise": "konate",
        "type": "nom",
        "ethnie_ou_region": "Mandé (Niani, Kangaba) — Malinké",
        "signification": SENS_NON_ETABLI,
        "clan_role": "Lignée royale ancienne du Mandé, étroitement liée aux Keïta : la tradition rattache aux Konaté le père de Soundiata, Naré Maghan Kon Fatta.",
        "totem": "",
        "senankouya": "",
        "devise_ou_louange": None,
        "anecdote": "Les Konaté et les Keïta partagent une même souche dans la tradition : avant de devenir la marque de la dynastie impériale, les ancêtres de Soundiata sont aussi désignés comme Konaté.",
        "variantes": ["Konate", "Konaté"],
    },
    {
        "id": "nom_dembele",
        "nom": "Dembélé",
        "nom_normalise": "dembele",
        "type": "nom",
        "ethnie_ou_region": "Centre et sud du Mali — Bambara, Minianka",
        "signification": SENS_NON_ETABLI,
        "clan_role": "Patronyme répandu chez les Bambara et les Minianka.",
        "totem": "",
        "senankouya": "",
        "devise_ou_louange": None,
        "anecdote": "",
        "variantes": ["Dembele", "Dembélé"],
    },
    {
        "id": "nom_sacko",
        "nom": "Sacko",
        "nom_normalise": "sacko",
        "type": "nom",
        "ethnie_ou_region": "Région de Kayes — Soninké et Khassonké",
        "signification": SENS_NON_ETABLI,
        "clan_role": "Patronyme soninké et khassonké de la région de Kayes.",
        "totem": "",
        "senankouya": "",
        "devise_ou_louange": None,
        "anecdote": "",
        "variantes": ["Sacko", "Sakho", "Sako"],
    },
    {
        "id": "nom_haidara",
        "nom": "Haïdara",
        "nom_normalise": "haidara",
        "type": "nom",
        "ethnie_ou_region": "Tombouctou, Djenné, Gao — familles chérifiennes",
        "signification": "De l'arabe « Haydar », « le lion », surnom d'Ali, gendre du Prophète.",
        "clan_role": "Familles chérifiennes (se réclamant de la descendance du Prophète) et lettrées, gardiennes de bibliothèques de manuscrits.",
        "totem": "",
        "senankouya": "",
        "devise_ou_louange": None,
        "anecdote": "En 2012-2013, Abdel Kader Haïdara organisa l'évacuation clandestine de centaines de milliers de manuscrits de Tombouctou vers Bamako pour les sauver de la destruction.",
        "variantes": ["Haidara", "Haïdara", "Haydara"],
    },
    {
        "id": "nom_kone",
        "nom": "Koné",
        "nom_normalise": "kone",
        "type": "nom",
        "ethnie_ou_region": "Sud du Mali, Côte d'Ivoire, Burkina Faso — Bambara, Malinké, Sénoufo",
        "signification": SENS_NON_ETABLI,
        "clan_role": "Patronyme très répandu chez les Bambara, les Malinké et les Sénoufo.",
        "totem": "",
        "senankouya": "",
        "devise_ou_louange": None,
        "anecdote": "",
        "variantes": ["Kone", "Koné"],
    },
    {
        "id": "nom_fofana",
        "nom": "Fofana",
        "nom_normalise": "fofana",
        "type": "nom",
        "ethnie_ou_region": "Pays soninké et mandingue",
        "signification": SENS_NON_ETABLI,
        "clan_role": "Patronyme soninké et mandingue.",
        "totem": "",
        "senankouya": "",
        "devise_ou_louange": None,
        "anecdote": "",
        "variantes": ["Fofana"],
    },
    {
        "id": "nom_bagayoko",
        "nom": "Bagayoko",
        "nom_normalise": "bagayoko",
        "type": "nom",
        "ethnie_ou_region": "Mandé, Tombouctou — Bambara et familles lettrées",
        "signification": SENS_NON_ETABLI,
        "clan_role": "Patronyme mandingue, porté aussi par une célèbre lignée de savants de Tombouctou.",
        "totem": "",
        "senankouya": "",
        "devise_ou_louange": None,
        "anecdote": "Au XVIe siècle, le savant Mohammed Bagayogo (1523-1594) enseignait à Tombouctou ; il fut le maître du grand érudit Ahmed Baba.",
        "variantes": ["Bagayoko", "Bagayogo", "Bakayoko"],
    },
    {
        "id": "nom_sissoko",
        "nom": "Sissoko",
        "nom_normalise": "sissoko",
        "type": "nom",
        "ethnie_ou_region": "Khasso (Kayes), Kita, Mandé — Malinké et Khassonké",
        "signification": SENS_NON_ETABLI,
        "clan_role": "Patronyme porté à la fois par des familles nobles et par des lignées de griots.",
        "totem": "",
        "senankouya": "",
        "devise_ou_louange": None,
        "anecdote": "Le joueur de kora Ballaké Sissoko perpétue aujourd'hui l'art des griots mandingues.",
        "variantes": ["Sissoko", "Cissoko", "Cissokho"],
    },
    {
        "id": "nom_guindo",
        "nom": "Guindo",
        "nom_normalise": "guindo",
        "type": "nom",
        "ethnie_ou_region": "Pays dogon (falaise de Bandiagara, Bankass, Koro)",
        "signification": "Patronyme dogon. " + SENS_NON_ETABLI,
        "clan_role": "L'un des patronymes dogon les plus répandus, avec Dolo, Togo, Ongoïba ou Kassogué.",
        "totem": "",
        "senankouya": "Les Bozo (pacte Dogon–Bozo).",
        "devise_ou_louange": None,
        "anecdote": (
            "Dogon et Bozo sont liés par un pacte ancien : ils se doivent assistance, ne peuvent se faire de mal "
            "et, selon la tradition, ne se marient pas entre eux. Une légende dit qu'en temps de famine, l'un nourrit l'autre de sa propre chair."
        ),
        "variantes": ["Guindo", "Gindo"],
    },
    {
        "id": "nom_thiero",
        "nom": "Thiéro",
        "nom_normalise": "thiero",
        "type": "nom",
        "ethnie_ou_region": "Région de Mopti et delta intérieur du Niger",
        "signification": "Son sens et son rattachement ethnique précis ne sont pas documentés de façon fiable.",
        "clan_role": "Patronyme présent dans la région de Mopti.",
        "totem": "",
        "senankouya": "",
        "devise_ou_louange": None,
        "anecdote": "",
        "variantes": ["Thiero", "Thiéro", "Tiero"],
    },

    # ══════════════════════════════════════════════════════════════════════════
    # 2. PRÉNOMS
    #    (clan_role = usage du prénom ; pas de tana ni de senankouya pour un prénom)
    # ══════════════════════════════════════════════════════════════════════════
    {
        "id": "prenom_mamadou",
        "nom": "Mamadou",
        "nom_normalise": "mamadou",
        "type": "prenom",
        "ethnie_ou_region": "Tout le Mali (Bambara, Peuls, Soninké, Songhaï…)",
        "signification": "Forme ouest-africaine de Muhammad, de l'arabe : « le loué », « celui qui est digne de louanges ».",
        "clan_role": "Prénom donné en hommage au Prophète de l'islam ; diminutifs courants : Madou, Mady.",
        "totem": "",
        "senankouya": "",
        "devise_ou_louange": None,
        "anecdote": "",
        "variantes": ["Mamadou", "Mahamadou", "Madou"],
    },
    {
        "id": "prenom_fatoumata",
        "nom": "Fatoumata",
        "nom_normalise": "fatoumata",
        "type": "prenom",
        "ethnie_ou_region": "Tout le Mali",
        "signification": "Forme ouest-africaine de Fatima, de l'arabe : « celle qui sèvre (son enfant) ».",
        "clan_role": "Prénom donné en hommage à Fatima, fille du Prophète ; diminutifs courants : Fatou, Fanta.",
        "totem": "",
        "senankouya": "",
        "devise_ou_louange": None,
        "anecdote": "",
        "variantes": ["Fatoumata", "Fatimata", "Fatou", "Fanta"],
    },
    {
        "id": "prenom_soundiata",
        "nom": "Soundiata",
        "nom_normalise": "soundiata",
        "type": "prenom",
        "ethnie_ou_region": "Mandé — prénom historique",
        "signification": "Contraction de « Sogolon Jara », « le lion de Sogolon », du nom de sa mère et du mot bambara/malinké « jara » (lion).",
        "clan_role": "Prénom du fondateur de l'Empire du Mali, aussi appelé Mari Djata.",
        "totem": "",
        "senankouya": "",
        "devise_ou_louange": None,
        "anecdote": (
            "Selon l'épopée, l'enfant ne pouvait pas marcher et était moqué. Un jour, humilié pour sa mère, "
            "il se leva en s'appuyant sur une barre de fer forgée, puis arracha un jeune baobab pour en offrir les feuilles à Sogolon."
        ),
        "variantes": ["Soundiata", "Sundiata", "Sunjata", "Soundjata"],
    },
    {
        "id": "prenom_awa",
        "nom": "Awa",
        "nom_normalise": "awa",
        "type": "prenom",
        "ethnie_ou_region": "Tout le Mali",
        "signification": "Forme de Hawwa, Ève en arabe, nom généralement compris comme « la vivante », « celle qui donne la vie ».",
        "clan_role": "Prénom donné en hommage à la première femme de la tradition biblique et coranique.",
        "totem": "",
        "senankouya": "",
        "devise_ou_louange": None,
        "anecdote": "Aoua Keïta, sage-femme et militante, fut en 1959 la première femme élue députée au Soudan français, futur Mali.",
        "variantes": ["Awa", "Hawa", "Aoua"],
    },
    {
        "id": "prenom_modibo",
        "nom": "Modibo",
        "nom_normalise": "modibo",
        "type": "prenom",
        "ethnie_ou_region": "Tout le Mali (d'origine peule)",
        "signification": "Du peul « moodibbo » : « le savant, le lettré » (en sciences islamiques).",
        "clan_role": "Titre d'érudit devenu prénom.",
        "totem": "",
        "senankouya": "",
        "devise_ou_louange": None,
        "anecdote": "Modibo Keïta fut le premier président du Mali indépendant, proclamé le 22 septembre 1960.",
        "variantes": ["Modibo", "Moodibo"],
    },
    {
        "id": "prenom_aminata",
        "nom": "Aminata",
        "nom_normalise": "aminata",
        "type": "prenom",
        "ethnie_ou_region": "Tout le Mali",
        "signification": "Forme ouest-africaine d'Amina, de l'arabe : « digne de confiance, fidèle ».",
        "clan_role": "Prénom donné en hommage à Amina, mère du Prophète.",
        "totem": "",
        "senankouya": "",
        "devise_ou_louange": None,
        "anecdote": "L'essayiste Aminata Dramane Traoré fut ministre de la Culture du Mali de 1997 à 2000.",
        "variantes": ["Aminata", "Aminatou", "Amina"],
    },
    {
        "id": "prenom_sekou",
        "nom": "Sékou",
        "nom_normalise": "sekou",
        "type": "prenom",
        "ethnie_ou_region": "Tout le Mali",
        "signification": "Forme mandingue de Cheikh, de l'arabe : « l'ancien », « le maître (spirituel) ».",
        "clan_role": "Prénom de respect, lié au savoir religieux.",
        "totem": "",
        "senankouya": "",
        "devise_ou_louange": None,
        "anecdote": "Sékou Amadou (Cheikou Amadou Barry) fonda en 1818 la Diina, l'État peul du Macina, avec Hamdallaye pour capitale.",
        "variantes": ["Sekou", "Sékou", "Seykou", "Cheickou"],
    },
    {
        "id": "prenom_tenin",
        "nom": "Tênin",
        "nom_normalise": "tenin",
        "type": "prenom",
        "ethnie_ou_region": "Bambara et Malinké",
        "signification": "Du bambara « tɛnɛn » : « lundi ». Prénom donné à une fille née un lundi.",
        "clan_role": "Fait partie des prénoms liés au jour de naissance.",
        "totem": "",
        "senankouya": "",
        "devise_ou_louange": None,
        "anecdote": "",
        "variantes": ["Tenin", "Tênin", "Ténin"],
    },
    {
        "id": "prenom_bintou",
        "nom": "Bintou",
        "nom_normalise": "bintou",
        "type": "prenom",
        "ethnie_ou_region": "Tout le Mali",
        "signification": "Généralement rattaché à l'arabe « bint » : « la fille ».",
        "clan_role": "Prénom féminin courant ; variante : Binta.",
        "totem": "",
        "senankouya": "",
        "devise_ou_louange": None,
        "anecdote": "",
        "variantes": ["Bintou", "Binta"],
    },
    {
        "id": "prenom_boubacar",
        "nom": "Boubacar",
        "nom_normalise": "boubacar",
        "type": "prenom",
        "ethnie_ou_region": "Tout le Mali",
        "signification": "Forme ouest-africaine d'Abou Bakr, de l'arabe : « le père du jeune chameau ».",
        "clan_role": "Prénom donné en hommage à Abou Bakr, compagnon du Prophète et premier calife ; formes mandingues : Bakary, Bocar.",
        "totem": "",
        "senankouya": "",
        "devise_ou_louange": None,
        "anecdote": "",
        "variantes": ["Boubacar", "Bakary", "Bocar", "Aboubacar"],
    },
    {
        "id": "prenom_sogolon",
        "nom": "Sogolon",
        "nom_normalise": "sogolon",
        "type": "prenom",
        "ethnie_ou_region": "Mandé — prénom historique",
        "signification": "Nom de la mère de Soundiata, Sogolon Kédjou (Sogolon Condé). Son sens littéral n'est pas établi.",
        "clan_role": "Prénom porté en hommage à la mère du fondateur de l'Empire du Mali.",
        "totem": "",
        "senankouya": "",
        "devise_ou_louange": None,
        "anecdote": (
            "Selon l'épopée, deux chasseurs vainquirent la femme-buffle du pays de Dô et reçurent en récompense "
            "Sogolon, jeune femme bossue et laide, qu'ils conduisirent au roi Naré Maghan. Elle devint la mère de Soundiata."
        ),
        "variantes": ["Sogolon"],
    },
    {
        "id": "prenom_kadiatou",
        "nom": "Kadiatou",
        "nom_normalise": "kadiatou",
        "type": "prenom",
        "ethnie_ou_region": "Tout le Mali",
        "signification": "Forme ouest-africaine de Khadija, de l'arabe : « née avant terme », « la prématurée ».",
        "clan_role": "Prénom donné en hommage à Khadija, première épouse du Prophète ; diminutifs : Kadia, Kadidia.",
        "totem": "",
        "senankouya": "",
        "devise_ou_louange": None,
        "anecdote": "",
        "variantes": ["Kadiatou", "Kadidiatou", "Kadia", "Kadidia"],
    },
]


def _apply(rec: CultureNom, item: dict) -> None:
    rec.nom = item["nom"]
    rec.nom_normalise = item["nom_normalise"]
    rec.type = item["type"]
    rec.ethnie_ou_region = item["ethnie_ou_region"]
    rec.signification = item["signification"]
    rec.clan_role = item["clan_role"]
    rec.totem = item.get("totem") or ""
    rec.senankouya = item.get("senankouya") or ""
    rec.devise_ou_louange = item.get("devise_ou_louange")
    rec.anecdote = item.get("anecdote") or ""
    rec.variantes_json = json.dumps(item.get("variantes", [item["nom"]]), ensure_ascii=False)


def seed_noms_data(db: Session, force: bool = False):
    """
    Synchronise la base des noms et prénoms du Mali.
    Ce sont des données de référence : les lignes existantes sont TOUJOURS mises à jour
    pour que les corrections éditoriales soient propagées (le paramètre `force` est conservé
    pour compatibilité).
    """
    try:
        inserted = 0
        updated = 0

        for item in NOMS_DATA:
            rec = db.query(CultureNom).filter(CultureNom.id == item["id"]).first()
            if not rec:
                rec = CultureNom(id=item["id"], date_creation=datetime.now(UTC))
                _apply(rec, item)
                db.add(rec)
                inserted += 1
            else:
                _apply(rec, item)
                updated += 1

        db.commit()
        logger.info(f"Seed Noms terminé : {inserted} insérés, {updated} synchronisés.")
        print(f"[OK] Noms du Mali : {len(NOMS_DATA)} patronymes et prenoms synchronises en BDD.")
    except Exception as exc:
        db.rollback()
        logger.error(f"Erreur lors du seed des patronymes : {exc}")
        print(f"[WARN] Erreur seed patronymes : {exc}")
