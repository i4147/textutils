from re import match, search, subn, IGNORECASE, VERBOSE
from re import split as splitre
from re import error as reerror
from re import sub as resub


class UnknownClassicalModeError(Exception):
    pass


class BadNumValueError(Exception):
    pass


class BadChunkingOptionError(Exception):
    pass


class NumOutOfRangeError(Exception):
    pass


class BadUserDefinedPatternError(Exception):
    pass


class BadRcFileError(Exception):
    pass


class BadGenderError(Exception):
    pass


__version__ = "1.0.1"
STDOUT_ON = False


def print3(txt):
    if STDOUT_ON:
        print(txt)


def enclose(s):
    return "(?:%s)" % s


def joinstem(cutpoint=0, words=""):
    return enclose("|".join(w[:cutpoint] for w in words))


def bysize(words):
    ret = {}
    for w in words:
        if len(w) not in ret:
            ret[len(w)] = set()
        ret[len(w)].add(w)
    return ret


def make_pl_si_lists(lst, plending, siendingsize, dojoinstem=True):
    if siendingsize is not None:
        siendingsize = -siendingsize
    si_list = [w[:siendingsize] + plending for w in lst]
    pl_bysize = bysize(lst)
    si_bysize = bysize(si_list)
    if dojoinstem:
        stem = joinstem(siendingsize, lst)
        return si_list, si_bysize, pl_bysize, stem
    else:
        return si_list, si_bysize, pl_bysize


pl_sb_irregular_s = {
    "corpus": "corpuses|corpora",
    "opus": "opuses|opera",
    "genus": "genera",
    "mythos": "mythoi",
    "penis": "penises|penes",
    "testis": "testes",
    "atlas": "atlases|atlantes",
    "yes": "yeses",
}
pl_sb_irregular = {
    "child": "children",
    "brother": "brothers|brethren",
    "loaf": "loaves",
    "hoof": "hoofs|hooves",
    "beef": "beefs|beeves",
    "thief": "thiefs|thieves",
    "money": "monies",
    "mongoose": "mongooses",
    "ox": "oxen",
    "cow": "cows|kine",
    "graffito": "graffiti",
    "octopus": "octopuses|octopodes",
    "genie": "genies|genii",
    "ganglion": "ganglions|ganglia",
    "trilby": "trilbys",
    "turf": "turfs|turves",
    "numen": "numina",
    "atman": "atmas",
    "occiput": "occiputs|occipita",
    "sabretooth": "sabretooths",
    "sabertooth": "sabertooths",
    "lowlife": "lowlifes",
    "flatfoot": "flatfoots",
    "tenderfoot": "tenderfoots",
    "romany": "romanies",
    "jerry": "jerries",
    "mary": "maries",
    "talouse": "talouses",
    "blouse": "blouses",
    "rom": "roma",
    "carmen": "carmina",
}
pl_sb_irregular.update(pl_sb_irregular_s)
pl_sb_irregular_caps = {
    "Romany": "Romanies",
    "Jerry": "Jerrys",
    "Mary": "Marys",
    "Rom": "Roma",
}
pl_sb_irregular_compound = {
    "prima donna": "prima donnas|prime donne",
}
si_sb_irregular = {v: k for (k, v) in pl_sb_irregular.items()}
keys = list(si_sb_irregular.keys())
for k in keys:
    if "|" in k:
        k1, k2 = k.split("|")
        si_sb_irregular[k1] = si_sb_irregular[k2] = si_sb_irregular[k]
        del si_sb_irregular[k]
si_sb_irregular_caps = {v: k for (k, v) in pl_sb_irregular_caps.items()}
si_sb_irregular_compound = {v: k for (k, v) in pl_sb_irregular_compound.items()}
keys = list(si_sb_irregular_compound.keys())
for k in keys:
    if "|" in k:
        k1, k2 = k.split("|")
        si_sb_irregular_compound[k1] = si_sb_irregular_compound[k2] = si_sb_irregular_compound[k]
        del si_sb_irregular_compound[k]
pl_sb_z_zes_list = (
    "quartz",
    "topaz",
)
pl_sb_z_zes_bysize = bysize(pl_sb_z_zes_list)
pl_sb_ze_zes_list = ("snooze",)
pl_sb_ze_zes_bysize = bysize(pl_sb_ze_zes_list)
pl_sb_C_is_ides_complete = [
    "ephemeris",
    "iris",
    "clitoris",
    "chrysalis",
    "epididymis",
]
pl_sb_C_is_ides_endings = [
    "itis",
]
pl_sb_C_is_ides = joinstem(-2, pl_sb_C_is_ides_complete + [".*%s" % w for w in pl_sb_C_is_ides_endings])
pl_sb_C_is_ides_list = pl_sb_C_is_ides_complete + pl_sb_C_is_ides_endings
(si_sb_C_is_ides_list, si_sb_C_is_ides_bysize, pl_sb_C_is_ides_bysize) = make_pl_si_lists(
    pl_sb_C_is_ides_list, "ides", 2, dojoinstem=False
)
pl_sb_C_a_ata_list = (
    "anathema",
    "bema",
    "carcinoma",
    "charisma",
    "diploma",
    "dogma",
    "drama",
    "edema",
    "enema",
    "enigma",
    "lemma",
    "lymphoma",
    "magma",
    "melisma",
    "miasma",
    "oedema",
    "sarcoma",
    "schema",
    "soma",
    "stigma",
    "stoma",
    "trauma",
    "gumma",
    "pragma",
)
(si_sb_C_a_ata_list, si_sb_C_a_ata_bysize, pl_sb_C_a_ata_bysize, pl_sb_C_a_ata) = make_pl_si_lists(
    pl_sb_C_a_ata_list, "ata", 1
)
pl_sb_U_a_ae_list = ("alumna", "alga", "vertebra", "persona")
(si_sb_U_a_ae_list, si_sb_U_a_ae_bysize, pl_sb_U_a_ae_bysize, pl_sb_U_a_ae) = make_pl_si_lists(
    pl_sb_U_a_ae_list, "e", None
)
pl_sb_C_a_ae_list = (
    "amoeba",
    "antenna",
    "formula",
    "hyperbola",
    "medusa",
    "nebula",
    "parabola",
    "abscissa",
    "hydra",
    "nova",
    "lacuna",
    "aurora",
    "umbra",
    "flora",
    "fauna",
)
(si_sb_C_a_ae_list, si_sb_C_a_ae_bysize, pl_sb_C_a_ae_bysize, pl_sb_C_a_ae) = make_pl_si_lists(
    pl_sb_C_a_ae_list, "e", None
)
pl_sb_C_en_ina_list = (
    "stamen",
    "foramen",
    "lumen",
)
(si_sb_C_en_ina_list, si_sb_C_en_ina_bysize, pl_sb_C_en_ina_bysize, pl_sb_C_en_ina) = make_pl_si_lists(
    pl_sb_C_en_ina_list, "ina", 2
)
pl_sb_U_um_a_list = (
    "bacterium",
    "agendum",
    "desideratum",
    "erratum",
    "stratum",
    "datum",
    "ovum",
    "extremum",
    "candelabrum",
)
(si_sb_U_um_a_list, si_sb_U_um_a_bysize, pl_sb_U_um_a_bysize, pl_sb_U_um_a) = make_pl_si_lists(
    pl_sb_U_um_a_list, "a", 2
)
pl_sb_C_um_a_list = (
    "maximum",
    "minimum",
    "momentum",
    "optimum",
    "quantum",
    "cranium",
    "curriculum",
    "dictum",
    "phylum",
    "aquarium",
    "compendium",
    "emporium",
    "enconium",
    "gymnasium",
    "honorarium",
    "interregnum",
    "lustrum",
    "memorandum",
    "millennium",
    "rostrum",
    "spectrum",
    "speculum",
    "stadium",
    "trapezium",
    "ultimatum",
    "medium",
    "vacuum",
    "velum",
    "consortium",
    "arboretum",
)
(si_sb_C_um_a_list, si_sb_C_um_a_bysize, pl_sb_C_um_a_bysize, pl_sb_C_um_a) = make_pl_si_lists(
    pl_sb_C_um_a_list, "a", 2
)
pl_sb_U_us_i_list = (
    "alumnus",
    "alveolus",
    "bacillus",
    "bronchus",
    "locus",
    "nucleus",
    "stimulus",
    "meniscus",
    "sarcophagus",
)
(si_sb_U_us_i_list, si_sb_U_us_i_bysize, pl_sb_U_us_i_bysize, pl_sb_U_us_i) = make_pl_si_lists(
    pl_sb_U_us_i_list, "i", 2
)
pl_sb_C_us_i_list = (
    "focus",
    "radius",
    "genius",
    "incubus",
    "succubus",
    "nimbus",
    "fungus",
    "nucleolus",
    "stylus",
    "torus",
    "umbilicus",
    "uterus",
    "hippopotamus",
    "cactus",
)
(si_sb_C_us_i_list, si_sb_C_us_i_bysize, pl_sb_C_us_i_bysize, pl_sb_C_us_i) = make_pl_si_lists(
    pl_sb_C_us_i_list, "i", 2
)
pl_sb_C_us_us = (
    "status",
    "apparatus",
    "prospectus",
    "sinus",
    "hiatus",
    "impetus",
    "plexus",
)
pl_sb_C_us_us_bysize = bysize(pl_sb_C_us_us)
pl_sb_U_on_a_list = (
    "criterion",
    "perihelion",
    "aphelion",
    "phenomenon",
    "prolegomenon",
    "noumenon",
    "organon",
    "asyndeton",
    "hyperbaton",
)
(si_sb_U_on_a_list, si_sb_U_on_a_bysize, pl_sb_U_on_a_bysize, pl_sb_U_on_a) = make_pl_si_lists(
    pl_sb_U_on_a_list, "a", 2
)
pl_sb_C_on_a_list = ("oxymoron",)
(si_sb_C_on_a_list, si_sb_C_on_a_bysize, pl_sb_C_on_a_bysize, pl_sb_C_on_a) = make_pl_si_lists(
    pl_sb_C_on_a_list, "a", 2
)
pl_sb_C_o_i = [
    "solo",
    "soprano",
    "basso",
    "alto",
    "contralto",
    "tempo",
    "piano",
    "virtuoso",
]
pl_sb_C_o_i_bysize = bysize(pl_sb_C_o_i)
si_sb_C_o_i_bysize = bysize(["%si" % w[:-1] for w in pl_sb_C_o_i])
pl_sb_C_o_i_stems = joinstem(-1, pl_sb_C_o_i)
pl_sb_U_o_os_complete = {
    "ado",
    "ISO",
    "NATO",
    "NCO",
    "NGO",
    "oto",
}
si_sb_U_o_os_complete = {"%ss" % w for w in pl_sb_U_o_os_complete}
pl_sb_U_o_os_endings = [
    "aficionado",
    "aggro",
    "albino",
    "allegro",
    "ammo",
    "Antananarivo",
    "archipelago",
    "armadillo",
    "auto",
    "avocado",
    "Bamako",
    "Barquisimeto",
    "bimbo",
    "bingo",
    "Biro",
    "bolero",
    "Bolzano",
    "bongo",
    "Boto",
    "burro",
    "Cairo",
    "canto",
    "cappuccino",
    "casino",
    "cello",
    "Chicago",
    "Chimango",
    "cilantro",
    "cochito",
    "coco",
    "Colombo",
    "Colorado",
    "commando",
    "concertino",
    "contango",
    "credo",
    "crescendo",
    "cyano",
    "demo",
    "ditto",
    "Draco",
    "dynamo",
    "embryo",
    "Esperanto",
    "espresso",
    "euro",
    "falsetto",
    "Faro",
    "fiasco",
    "Filipino",
    "flamenco",
    "furioso",
    "generalissimo",
    "Gestapo",
    "ghetto",
    "gigolo",
    "gizmo",
    "Greensboro",
    "gringo",
    "Guaiabero",
    "guano",
    "gumbo",
    "gyro",
    "hairdo",
    "hippo",
    "Idaho",
    "impetigo",
    "inferno",
    "info",
    "intermezzo",
    "intertrigo",
    "Iquico",
    "jumbo",
    "junto",
    "Kakapo",
    "kilo",
    "Kinkimavo",
    "Kokako",
    "Kosovo",
    "Lesotho",
    "libero",
    "libido",
    "libretto",
    "lido",
    "Lilo",
    "limbo",
    "limo",
    "lineno",
    "lingo",
    "lino",
    "livedo",
    "loco",
    "logo",
    "lumbago",
    "macho",
    "macro",
    "mafioso",
    "magneto",
    "magnifico",
    "Majuro",
    "Malabo",
    "manifesto",
    "Maputo",
    "Maracaibo",
    "medico",
    "memo",
    "metro",
    "Mexico",
    "micro",
    "Milano",
    "Monaco",
    "mono",
    "Montenegro",
    "Morocco",
    "Muqdisho",
    "myo",
    "neutrino",
    "Ningbo",
    "octavo",
    "oregano",
    "Orinoco",
    "Orlando",
    "Oslo",
    "panto",
    "Paramaribo",
    "Pardusco",
    "pedalo",
    "photo",
    "pimento",
    "pinto",
    "pleco",
    "Pluto",
    "pogo",
    "polo",
    "poncho",
    "Porto-Novo",
    "Porto",
    "pro",
    "psycho",
    "pueblo",
    "quarto",
    "Quito",
    "rhino",
    "risotto",
    "rococo",
    "rondo",
    "Sacramento",
    "saddo",
    "sago",
    "salvo",
    "Santiago",
    "Sapporo",
    "Sarajevo",
    "scherzando",
    "scherzo",
    "silo",
    "sirocco",
    "sombrero",
    "staccato",
    "sterno",
    "stucco",
    "stylo",
    "sumo",
    "Taiko",
    "techno",
    "terrazzo",
    "testudo",
    "timpano",
    "tiro",
    "tobacco",
    "Togo",
    "Tokyo",
    "torero",
    "Torino",
    "Toronto",
    "torso",
    "tremolo",
    "typo",
    "tyro",
    "ufo",
    "UNESCO",
    "vaquero",
    "vermicello",
    "verso",
    "vibrato",
    "violoncello",
    "Virgo",
    "weirdo",
    "WHO",
    "WTO",
    "Yamoussoukro",
    "yo-yo",
    "zero",
    "Zibo",
] + pl_sb_C_o_i
pl_sb_U_o_os_bysize = bysize(pl_sb_U_o_os_endings)
si_sb_U_o_os_bysize = bysize(["%ss" % w for w in pl_sb_U_o_os_endings])
pl_sb_U_ch_chs_list = ("czech", "eunuch", "stomach")
(si_sb_U_ch_chs_list, si_sb_U_ch_chs_bysize, pl_sb_U_ch_chs_bysize, pl_sb_U_ch_chs) = make_pl_si_lists(
    pl_sb_U_ch_chs_list, "s", None
)
pl_sb_U_ex_ices_list = (
    "codex",
    "murex",
    "silex",
)
(si_sb_U_ex_ices_list, si_sb_U_ex_ices_bysize, pl_sb_U_ex_ices_bysize, pl_sb_U_ex_ices) = make_pl_si_lists(
    pl_sb_U_ex_ices_list, "ices", 2
)
pl_sb_U_ix_ices_list = (
    "radix",
    "helix",
)
(si_sb_U_ix_ices_list, si_sb_U_ix_ices_bysize, pl_sb_U_ix_ices_bysize, pl_sb_U_ix_ices) = make_pl_si_lists(
    pl_sb_U_ix_ices_list, "ices", 2
)
pl_sb_C_ex_ices_list = (
    "vortex",
    "vertex",
    "cortex",
    "latex",
    "pontifex",
    "apex",
    "index",
    "simplex",
)
(si_sb_C_ex_ices_list, si_sb_C_ex_ices_bysize, pl_sb_C_ex_ices_bysize, pl_sb_C_ex_ices) = make_pl_si_lists(
    pl_sb_C_ex_ices_list, "ices", 2
)
pl_sb_C_ix_ices_list = ("appendix",)
(si_sb_C_ix_ices_list, si_sb_C_ix_ices_bysize, pl_sb_C_ix_ices_bysize, pl_sb_C_ix_ices) = make_pl_si_lists(
    pl_sb_C_ix_ices_list, "ices", 2
)
pl_sb_C_i_list = (
    "afrit",
    "afreet",
    "efreet",
)
(si_sb_C_i_list, si_sb_C_i_bysize, pl_sb_C_i_bysize, pl_sb_C_i) = make_pl_si_lists(pl_sb_C_i_list, "i", None)
pl_sb_C_im_list = (
    "goy",
    "seraph",
    "cherub",
)
(si_sb_C_im_list, si_sb_C_im_bysize, pl_sb_C_im_bysize, pl_sb_C_im) = make_pl_si_lists(pl_sb_C_im_list, "im", None)
pl_sb_U_man_mans_list = """
    ataman caiman cayman ceriman
    desman dolman farman harman hetman
    human leman ottoman shaman talisman
""".split()
pl_sb_U_man_mans_caps_list = """
    Alabaman Bahaman Burman German
    Hiroshiman Liman Nakayaman Norman Oklahoman
    Panaman Roman Selman Sonaman Tacoman Yakiman
    Yokohaman Yuman
""".split()
(si_sb_U_man_mans_list, si_sb_U_man_mans_bysize, pl_sb_U_man_mans_bysize) = make_pl_si_lists(
    pl_sb_U_man_mans_list, "s", None, dojoinstem=False
)
(si_sb_U_man_mans_caps_list, si_sb_U_man_mans_caps_bysize, pl_sb_U_man_mans_caps_bysize) = make_pl_si_lists(
    pl_sb_U_man_mans_caps_list, "s", None, dojoinstem=False
)
pl_sb_uninflected_s_complete = [
    "breeches",
    "britches",
    "pajamas",
    "pyjamas",
    "clippers",
    "gallows",
    "hijinks",
    "headquarters",
    "pliers",
    "scissors",
    "testes",
    "herpes",
    "pincers",
    "shears",
    "proceedings",
    "trousers",
    "cantus",
    "coitus",
    "nexus",
    "contretemps",
    "corps",
    "debris",
    "siemens",
    "mumps",
    "diabetes",
    "jackanapes",
    "series",
    "species",
    "subspecies",
    "rabies",
    "chassis",
    "innings",
    "news",
    "mews",
    "haggis",
]
pl_sb_uninflected_s_endings = [
    "ois",
    "measles",
]
pl_sb_uninflected_s = pl_sb_uninflected_s_complete + [".*%s" % w for w in pl_sb_uninflected_s_endings]
pl_sb_uninflected_herd = (
    "wildebeest",
    "swine",
    "eland",
    "bison",
    "buffalo",
    "elk",
    "rhinoceros",
    "zucchini",
    "caribou",
    "dace",
    "grouse",
    "guinea fowl",
    "guinea-fowl",
    "haddock",
    "hake",
    "halibut",
    "herring",
    "mackerel",
    "pickerel",
    "pike",
    "roe",
    "seed",
    "shad",
    "snipe",
    "teal",
    "turbot",
    "water fowl",
    "water-fowl",
)
pl_sb_uninflected_complete = [
    "tuna",
    "salmon",
    "mackerel",
    "trout",
    "bream",
    "sea-bass",
    "sea bass",
    "carp",
    "cod",
    "flounder",
    "whiting",
    "moose",
    "graffiti",
    "djinn",
    "samuri",
    "offspring",
    "pence",
    "quid",
    "hertz",
] + pl_sb_uninflected_s_complete
pl_sb_uninflected_caps = [
    "Portuguese",
    "Amoyese",
    "Borghese",
    "Congoese",
    "Faroese",
    "Foochowese",
    "Genevese",
    "Genoese",
    "Gilbertese",
    "Hottentotese",
    "Kiplingese",
    "Kongoese",
    "Lucchese",
    "Maltese",
    "Nankingese",
    "Niasese",
    "Pekingese",
    "Piedmontese",
    "Pistoiese",
    "Sarawakese",
    "Shavese",
    "Vermontese",
    "Wenchowese",
    "Yengeese",
]
pl_sb_uninflected_endings = [
    "fish",
    "deer",
    "sheep",
    "nese",
    "rese",
    "lese",
    "mese",
    "pox",
    "craft",
] + pl_sb_uninflected_s_endings
pl_sb_uninflected_bysize = bysize(pl_sb_uninflected_endings)
pl_sb_singular_s_complete = [
    "acropolis",
    "aegis",
    "alias",
    "asbestos",
    "bathos",
    "bias",
    "bronchitis",
    "bursitis",
    "caddis",
    "cannabis",
    "canvas",
    "chaos",
    "cosmos",
    "dais",
    "digitalis",
    "epidermis",
    "ethos",
    "eyas",
    "gas",
    "glottis",
    "hubris",
    "ibis",
    "lens",
    "mantis",
    "marquis",
    "metropolis",
    "pathos",
    "pelvis",
    "polis",
    "rhinoceros",
    "sassafras",
    "trellis",
] + pl_sb_C_is_ides_complete
pl_sb_singular_s_endings = [
    "ss",
    "us",
] + pl_sb_C_is_ides_endings
pl_sb_singular_s_bysize = bysize(pl_sb_singular_s_endings)
si_sb_singular_s_complete = ["%ses" % w for w in pl_sb_singular_s_complete]
si_sb_singular_s_endings = ["%ses" % w for w in pl_sb_singular_s_endings]
si_sb_singular_s_bysize = bysize(si_sb_singular_s_endings)
pl_sb_singular_s_es = [
    "[A-Z].*es",
]
pl_sb_singular_s = enclose(
    "|".join(pl_sb_singular_s_complete + [".*%s" % w for w in pl_sb_singular_s_endings] + pl_sb_singular_s_es)
)
si_sb_ois_oi_case = ("Bolshois", "Hanois")
si_sb_uses_use_case = (
    "Betelgeuses",
    "Duses",
    "Meuses",
    "Syracuses",
    "Toulouses",
)
si_sb_uses_use = (
    "abuses",
    "applauses",
    "blouses",
    "carouses",
    "causes",
    "chartreuses",
    "clauses",
    "contuses",
    "douses",
    "excuses",
    "fuses",
    "grouses",
    "hypotenuses",
    "masseuses",
    "menopauses",
    "misuses",
    "muses",
    "overuses",
    "pauses",
    "peruses",
    "profuses",
    "recluses",
    "reuses",
    "ruses",
    "souses",
    "spouses",
    "suffuses",
    "transfuses",
    "uses",
)
si_sb_ies_ie_case = (
    "Addies",
    "Aggies",
    "Allies",
    "Amies",
    "Angies",
    "Annies",
    "Annmaries",
    "Archies",
    "Arties",
    "Aussies",
    "Barbies",
    "Barries",
    "Basies",
    "Bennies",
    "Bernies",
    "Berties",
    "Bessies",
    "Betties",
    "Billies",
    "Blondies",
    "Bobbies",
    "Bonnies",
    "Bowies",
    "Brandies",
    "Bries",
    "Brownies",
    "Callies",
    "Carnegies",
    "Carries",
    "Cassies",
    "Charlies",
    "Cheries",
    "Christies",
    "Connies",
    "Curies",
    "Dannies",
    "Debbies",
    "Dixies",
    "Dollies",
    "Donnies",
    "Drambuies",
    "Eddies",
    "Effies",
    "Ellies",
    "Elsies",
    "Eries",
    "Ernies",
    "Essies",
    "Eugenies",
    "Fannies",
    "Flossies",
    "Frankies",
    "Freddies",
    "Gillespies",
    "Goldies",
    "Gracies",
    "Guthries",
    "Hallies",
    "Hatties",
    "Hetties",
    "Hollies",
    "Jackies",
    "Jamies",
    "Janies",
    "Jannies",
    "Jeanies",
    "Jeannies",
    "Jennies",
    "Jessies",
    "Jimmies",
    "Jodies",
    "Johnies",
    "Johnnies",
    "Josies",
    "Julies",
    "Kalgoorlies",
    "Kathies",
    "Katies",
    "Kellies",
    "Kewpies",
    "Kristies",
    "Laramies",
    "Lassies",
    "Lauries",
    "Leslies",
    "Lessies",
    "Lillies",
    "Lizzies",
    "Lonnies",
    "Lories",
    "Lorries",
    "Lotties",
    "Louies",
    "Mackenzies",
    "Maggies",
    "Maisies",
    "Mamies",
    "Marcies",
    "Margies",
    "Maries",
    "Marjories",
    "Matties",
    "McKenzies",
    "Melanies",
    "Mickies",
    "Millies",
    "Minnies",
    "Mollies",
    "Mounties",
    "Nannies",
    "Natalies",
    "Nellies",
    "Netties",
    "Ollies",
    "Ozzies",
    "Pearlies",
    "Pottawatomies",
    "Reggies",
    "Richies",
    "Rickies",
    "Robbies",
    "Ronnies",
    "Rosalies",
    "Rosemaries",
    "Rosies",
    "Roxies",
    "Rushdies",
    "Ruthies",
    "Sadies",
    "Sallies",
    "Sammies",
    "Scotties",
    "Selassies",
    "Sherries",
    "Sophies",
    "Stacies",
    "Stefanies",
    "Stephanies",
    "Stevies",
    "Susies",
    "Sylvies",
    "Tammies",
    "Terries",
    "Tessies",
    "Tommies",
    "Tracies",
    "Trekkies",
    "Valaries",
    "Valeries",
    "Valkyries",
    "Vickies",
    "Virgies",
    "Willies",
    "Winnies",
    "Wylies",
    "Yorkies",
)
si_sb_ies_ie = (
    "aeries",
    "baggies",
    "belies",
    "biggies",
    "birdies",
    "bogies",
    "bonnies",
    "boogies",
    "bookies",
    "bourgeoisies",
    "brownies",
    "budgies",
    "caddies",
    "calories",
    "camaraderies",
    "cockamamies",
    "collies",
    "cookies",
    "coolies",
    "cooties",
    "coteries",
    "crappies",
    "curies",
    "cutesies",
    "dogies",
    "eyrie",
    "floozies",
    "footsies",
    "freebies",
    "genies",
    "goalies",
    "groupies",
    "hies",
    "jalousies",
    "junkies",
    "kiddies",
    "laddies",
    "lassies",
    "lies",
    "lingeries",
    "magpies",
    "menageries",
    "mommies",
    "movies",
    "neckties",
    "newbies",
    "nighties",
    "oldies",
    "organdies",
    "overlies",
    "pies",
    "pinkies",
    "pixies",
    "potpies",
    "prairies",
    "quickies",
    "reveries",
    "rookies",
    "rotisseries",
    "softies",
    "sorties",
    "species",
    "stymies",
    "sweeties",
    "ties",
    "underlies",
    "unties",
    "veggies",
    "vies",
    "yuppies",
    "zombies",
)
si_sb_oes_oe_case = (
    "Chloes",
    "Crusoes",
    "Defoes",
    "Faeroes",
    "Ivanhoes",
    "Joes",
    "McEnroes",
    "Moes",
    "Monroes",
    "Noes",
    "Poes",
    "Roscoes",
    "Tahoes",
    "Tippecanoes",
    "Zoes",
)
si_sb_oes_oe = (
    "aloes",
    "backhoes",
    "canoes",
    "does",
    "floes",
    "foes",
    "hoes",
    "mistletoes",
    "oboes",
    "pekoes",
    "roes",
    "sloes",
    "throes",
    "tiptoes",
    "toes",
    "woes",
)
si_sb_z_zes = (
    "quartzes",
    "topazes",
)
si_sb_zzes_zz = ("buzzes", "fizzes", "frizzes", "razzes")
si_sb_ches_che_case = (
    "Andromaches",
    "Apaches",
    "Blanches",
    "Comanches",
    "Nietzsches",
    "Porsches",
    "Roches",
)
si_sb_ches_che = (
    "aches",
    "avalanches",
    "backaches",
    "bellyaches",
    "caches",
    "cloches",
    "creches",
    "douches",
    "earaches",
    "fiches",
    "headaches",
    "heartaches",
    "microfiches",
    "niches",
    "pastiches",
    "psyches",
    "quiches",
    "stomachaches",
    "toothaches",
)
si_sb_xes_xe = (
    "annexes",
    "axes",
    "deluxes",
    "pickaxes",
)
si_sb_sses_sse_case = (
    "Hesses",
    "Jesses",
    "Larousses",
    "Matisses",
)
si_sb_sses_sse = (
    "bouillabaisses",
    "crevasses",
    "demitasses",
    "impasses",
    "mousses",
    "posses",
)
si_sb_ves_ve_case = (
    "Clives",
    "Palmolives",
)
si_sb_ves_ve = (
    "interweaves",
    "weaves",
    "olives",
    "bivalves",
    "dissolves",
    "resolves",
    "salves",
    "twelves",
    "valves",
)
plverb_special_s = enclose(
    "|".join(
        [pl_sb_singular_s]
        + pl_sb_uninflected_s
        + list(pl_sb_irregular_s.keys())
        + [
            "(.*[csx])is",
            "(.*)ceps",
            "[A-Z].*s",
        ]
    )
)
pl_sb_postfix_adj = {
    "general": [r"(?!major|lieutenant|brigadier|adjutant|.*star)\S+"],
    "martial": ["court"],
}
for k in list(pl_sb_postfix_adj.keys()):
    pl_sb_postfix_adj[k] = enclose(enclose("|".join(pl_sb_postfix_adj[k])) + "(?=(?:-|\\s+)%s)" % k)
pl_sb_postfix_adj_stems = "(" + "|".join(list(pl_sb_postfix_adj.values())) + ")(.*)"
si_sb_es_is = (
    "amanuenses",
    "amniocenteses",
    "analyses",
    "antitheses",
    "apotheoses",
    "arterioscleroses",
    "atheroscleroses",
    "axes",
    "catalyses",
    "catharses",
    "chasses",
    "cirrhoses",
    "cocces",
    "crises",
    "diagnoses",
    "dialyses",
    "diereses",
    "electrolyses",
    "emphases",
    "exegeses",
    "geneses",
    "halitoses",
    "hydrolyses",
    "hypnoses",
    "hypotheses",
    "hystereses",
    "metamorphoses",
    "metastases",
    "misdiagnoses",
    "mitoses",
    "mononucleoses",
    "narcoses",
    "necroses",
    "nemeses",
    "neuroses",
    "oases",
    "osmoses",
    "osteoporoses",
    "paralyses",
    "parentheses",
    "parthenogeneses",
    "periphrases",
    "photosyntheses",
    "probosces",
    "prognoses",
    "prophylaxes",
    "prostheses",
    "preces",
    "psoriases",
    "psychoanalyses",
    "psychokineses",
    "psychoses",
    "scleroses",
    "scolioses",
    "sepses",
    "silicoses",
    "symbioses",
    "synopses",
    "syntheses",
    "taxes",
    "telekineses",
    "theses",
    "thromboses",
    "tuberculoses",
    "urinalyses",
)
pl_prep_list = """
    about above across after among around at athwart before behind
    below beneath beside besides between betwixt beyond but by
    during except for from in into near of off on onto out over
    since till to under until unto upon with""".split()
pl_prep_list_da = pl_prep_list + ["de", "du", "da"]
pl_prep_bysize = bysize(pl_prep_list_da)
pl_prep = enclose("|".join(pl_prep_list_da))
pl_sb_prep_dual_compound = r"(.*?)((?:-|\s+)(?:" + pl_prep + r")(?:-|\s+))a(?:-|\s+)(.*)"
singular_pronoun_genders = {
    "neuter",
    "feminine",
    "masculine",
    "gender-neutral",
    "feminine or masculine",
    "masculine or feminine",
}
pl_pron_nom = {
    "i": "we",
    "myself": "ourselves",
    "you": "you",
    "yourself": "yourselves",
    "she": "they",
    "herself": "themselves",
    "he": "they",
    "himself": "themselves",
    "it": "they",
    "itself": "themselves",
    "they": "they",
    "themself": "themselves",
    "mine": "ours",
    "yours": "yours",
    "hers": "theirs",
    "his": "theirs",
    "its": "theirs",
    "theirs": "theirs",
}
si_pron = {}
si_pron["nom"] = {v: k for (k, v) in pl_pron_nom.items()}
si_pron["nom"]["we"] = "I"
pl_pron_acc = {
    "me": "us",
    "myself": "ourselves",
    "you": "you",
    "yourself": "yourselves",
    "her": "them",
    "herself": "themselves",
    "him": "them",
    "himself": "themselves",
    "it": "them",
    "itself": "themselves",
    "them": "them",
    "themself": "themselves",
}
pl_pron_acc_keys = enclose("|".join(list(pl_pron_acc.keys())))
pl_pron_acc_keys_bysize = bysize(list(pl_pron_acc.keys()))
si_pron["acc"] = {v: k for (k, v) in pl_pron_acc.items()}
for thecase, plur, gend, sing in (
    ("nom", "they", "neuter", "it"),
    ("nom", "they", "feminine", "she"),
    ("nom", "they", "masculine", "he"),
    ("nom", "they", "gender-neutral", "they"),
    ("nom", "they", "feminine or masculine", "she or he"),
    ("nom", "they", "masculine or feminine", "he or she"),
    ("nom", "themselves", "neuter", "itself"),
    ("nom", "themselves", "feminine", "herself"),
    ("nom", "themselves", "masculine", "himself"),
    ("nom", "themselves", "gender-neutral", "themself"),
    ("nom", "themselves", "feminine or masculine", "herself or himself"),
    ("nom", "themselves", "masculine or feminine", "himself or herself"),
    ("nom", "theirs", "neuter", "its"),
    ("nom", "theirs", "feminine", "hers"),
    ("nom", "theirs", "masculine", "his"),
    ("nom", "theirs", "gender-neutral", "theirs"),
    ("nom", "theirs", "feminine or masculine", "hers or his"),
    ("nom", "theirs", "masculine or feminine", "his or hers"),
    ("acc", "them", "neuter", "it"),
    ("acc", "them", "feminine", "her"),
    ("acc", "them", "masculine", "him"),
    ("acc", "them", "gender-neutral", "them"),
    ("acc", "them", "feminine or masculine", "her or him"),
    ("acc", "them", "masculine or feminine", "him or her"),
    ("acc", "themselves", "neuter", "itself"),
    ("acc", "themselves", "feminine", "herself"),
    ("acc", "themselves", "masculine", "himself"),
    ("acc", "themselves", "gender-neutral", "themself"),
    ("acc", "themselves", "feminine or masculine", "herself or himself"),
    ("acc", "themselves", "masculine or feminine", "himself or herself"),
):
    try:
        si_pron[thecase][plur][gend] = sing
    except TypeError:
        si_pron[thecase][plur] = {}
        si_pron[thecase][plur][gend] = sing
si_pron_acc_keys = enclose("|".join(list(si_pron["acc"].keys())))
si_pron_acc_keys_bysize = bysize(list(si_pron["acc"].keys()))


def get_si_pron(thecase, word, gender):
    try:
        sing = si_pron[thecase][word]
    except KeyError:
        raise
    try:
        return sing[gender]
    except TypeError:
        return sing


plverb_irregular_pres = {
    "am": "are",
    "are": "are",
    "is": "are",
    "was": "were",
    "were": "were",
    "was": "were",
    "have": "have",
    "have": "have",
    "has": "have",
    "do": "do",
    "do": "do",
    "does": "do",
}
plverb_ambiguous_pres = {
    "act": "act",
    "act": "act",
    "acts": "act",
    "blame": "blame",
    "blame": "blame",
    "blames": "blame",
    "can": "can",
    "can": "can",
    "can": "can",
    "must": "must",
    "must": "must",
    "must": "must",
    "fly": "fly",
    "fly": "fly",
    "flies": "fly",
    "copy": "copy",
    "copy": "copy",
    "copies": "copy",
    "drink": "drink",
    "drink": "drink",
    "drinks": "drink",
    "fight": "fight",
    "fight": "fight",
    "fights": "fight",
    "fire": "fire",
    "fire": "fire",
    "fires": "fire",
    "like": "like",
    "like": "like",
    "likes": "like",
    "look": "look",
    "look": "look",
    "looks": "look",
    "make": "make",
    "make": "make",
    "makes": "make",
    "reach": "reach",
    "reach": "reach",
    "reaches": "reach",
    "run": "run",
    "run": "run",
    "runs": "run",
    "sink": "sink",
    "sink": "sink",
    "sinks": "sink",
    "sleep": "sleep",
    "sleep": "sleep",
    "sleeps": "sleep",
    "view": "view",
    "view": "view",
    "views": "view",
}
plverb_ambiguous_pres_keys = enclose("|".join(list(plverb_ambiguous_pres.keys())))
plverb_irregular_non_pres = (
    "did",
    "had",
    "ate",
    "made",
    "put",
    "spent",
    "fought",
    "sank",
    "gave",
    "sought",
    "shall",
    "could",
    "ought",
    "should",
)
plverb_ambiguous_non_pres = enclose(
    "|".join((
        "thought",
        "saw",
        "bent",
        "will",
        "might",
        "cut",
    ))
)
pl_v_oes_oe = ("canoes", "floes", "oboes", "roes", "throes", "woes")
pl_v_oes_oe_endings_size4 = ("hoes", "toes")
pl_v_oes_oe_endings_size5 = "shoes"
pl_count_zero = ("0", "no", "zero", "nil")
pl_count_one = (
    "1",
    "a",
    "an",
    "one",
    "each",
    "every",
    "this",
    "that",
)
pl_adj_special = {
    "a": "some",
    "an": "some",
    "this": "these",
    "that": "those",
}
pl_adj_special_keys = enclose("|".join(list(pl_adj_special.keys())))
pl_adj_poss = {
    "my": "our",
    "your": "your",
    "its": "their",
    "her": "their",
    "his": "their",
    "their": "their",
}
pl_adj_poss_keys = enclose("|".join(list(pl_adj_poss.keys())))
A_abbrev = r"""
(?! FJO | [HLMNS]Y.  | RY[EO] | SQU
  | ( F[LR]? | [HL] | MN? | N | RH? | S[CHKLMNPTVW]? | X(YL)?) [AEIOU])
[FHLMNRSX][A-Z]
"""
A_y_cons = "y(b[lor]|cl[ea]|fere|gg|p[ios]|rou|tt)"
A_explicit_a = enclose(
    "|".join((
        "unabomber",
        "unanimous",
        "US",
    ))
)
A_explicit_an = enclose(
    "|".join((
        "euler",
        "hour(?!i)",
        "heir",
        "honest",
        "hono[ur]",
        "mpeg",
    ))
)
A_ordinal_an = enclose("|".join(("[aefhilmnorsx]-?th",)))
A_ordinal_a = enclose("|".join(("[bcdgjkpqtuvwyz]-?th",)))
nth = {
    0: "th",
    1: "st",
    2: "nd",
    3: "rd",
    4: "th",
    5: "th",
    6: "th",
    7: "th",
    8: "th",
    9: "th",
    11: "th",
    12: "th",
    13: "th",
}
ordinal = dict(
    ty="tieth", one="first", two="second", three="third", five="fifth", eight="eighth", nine="ninth", twelve="twelfth"
)
ordinal_suff = "|".join(list(ordinal.keys()))
unit = ["", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine"]
teen = ["ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen", "seventeen", "eighteen", "nineteen"]
ten = ["", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"]
mill = [
    " ",
    " thousand",
    " million",
    " billion",
    " trillion",
    " quadrillion",
    " quintillion",
    " sextillion",
    " septillion",
    " octillion",
    " nonillion",
    " decillion",
]
def_classical = dict(
    all=False,
    zero=False,
    herd=False,
    names=True,
    persons=False,
    ancient=False,
)
all_classical = {k: True for k in list(def_classical.keys())}
no_classical = {k: False for k in list(def_classical.keys())}


class Inflect:
    def __init__(self):
        self.classical_dict = def_classical.copy()
        self.persistent_count = None
        self.mill_count = 0
        self.pl_sb_user_defined = []
        self.pl_v_user_defined = []
        self.pl_adj_user_defined = []
        self.si_sb_user_defined = []
        self.A_a_user_defined = []
        self.thegender = "neuter"

    deprecated_methods = dict(
        pl="plural",
        plnoun="plural_noun",
        plverb="plural_verb",
        pladj="plural_adj",
        sinoun="single_noun",
        prespart="present_participle",
        numwords="number_to_words",
        plequal="compare",
        plnounequal="compare_nouns",
        plverbequal="compare_verbs",
        pladjequal="compare_adjs",
        wordlist="join",
    )

    def __getattr__(self, meth):
        if meth in self.deprecated_methods:
            print3("{}() deprecated, use {}()".format(meth, self.deprecated_methods[meth]))
            raise DeprecationWarning
        raise AttributeError

    def defnoun(self, singular, plural):
        self.checkpat(singular)
        self.checkpatplural(plural)
        self.pl_sb_user_defined.extend((singular, plural))
        self.si_sb_user_defined.extend((plural, singular))
        return 1

    def defverb(self, s1, p1, s2, p2, s3, p3):
        self.checkpat(s1)
        self.checkpat(s2)
        self.checkpat(s3)
        self.checkpatplural(p1)
        self.checkpatplural(p2)
        self.checkpatplural(p3)
        self.pl_v_user_defined.extend((s1, p1, s2, p2, s3, p3))
        return 1

    def defadj(self, singular, plural):
        self.checkpat(singular)
        self.checkpatplural(plural)
        self.pl_adj_user_defined.extend((singular, plural))
        return 1

    def defa(self, pattern):
        self.checkpat(pattern)
        self.A_a_user_defined.extend((pattern, "a"))
        return 1

    def defan(self, pattern):
        self.checkpat(pattern)
        self.A_a_user_defined.extend((pattern, "an"))
        return 1

    def checkpat(self, pattern):
        if pattern is None:
            return
        try:
            match(pattern, "")
        except reerror:
            print3("\nBad user-defined singular pattern:\n\t%s\n" % pattern)
            raise BadUserDefinedPatternError

    def checkpatplural(self, pattern):
        return

    def ud_match(self, word, wordlist):
        for i in range(len(wordlist) - 2, -2, -2):
            mo = search(r"^%s$" % wordlist[i], word, IGNORECASE)
            if mo:
                if wordlist[i + 1] is None:
                    return None
                pl = resub(r"\$(\d+)", r"\\1", wordlist[i + 1])
                return mo.expand(pl)
        return None

    def classical(self, **kwargs):
        classical_mode = list(def_classical.keys())
        if not kwargs:
            self.classical_dict = all_classical.copy()
            return
        if "all" in kwargs:
            if kwargs["all"]:
                self.classical_dict = all_classical.copy()
            else:
                self.classical_dict = no_classical.copy()
        for k, v in list(kwargs.items()):
            if k in classical_mode:
                self.classical_dict[k] = v
            else:
                raise UnknownClassicalModeError

    def num(self, count=None, show=None):
        if count is not None:
            try:
                self.persistent_count = int(count)
            except ValueError:
                raise BadNumValueError
            if (show is None) or show:
                return str(count)
        else:
            self.persistent_count = None
        return ""

    def gender(self, gender):
        if gender in singular_pronoun_genders:
            self.thegender = gender
        else:
            raise BadGenderError

    def nummo(self, matchobject):
        return self.num(matchobject.group(1), matchobject.group(2))

    def plmo(self, matchobject):
        return self.plural(matchobject.group(1), matchobject.group(3))

    def plnounmo(self, matchobject):
        return self.plural_noun(matchobject.group(1), matchobject.group(3))

    def plverbmo(self, matchobject):
        return self.plural_verb(matchobject.group(1), matchobject.group(3))

    def pladjmo(self, matchobject):
        return self.plural_adj(matchobject.group(1), matchobject.group(3))

    def sinounmo(self, matchobject):
        return self.singular_noun(matchobject.group(1), matchobject.group(3))

    def amo(self, matchobject):
        if matchobject.group(3) is None:
            return self.a(matchobject.group(1))
        return self.a(matchobject.group(1), matchobject.group(3))

    def nomo(self, matchobject):
        return self.no(matchobject.group(1), matchobject.group(3))

    def ordinalmo(self, matchobject):
        return self.ordinal(matchobject.group(1))

    def numwordsmo(self, matchobject):
        return self.number_to_words(matchobject.group(1))

    def prespartmo(self, matchobject):
        return self.present_participle(matchobject.group(1))

    def inflect(self, text):
        save_persistent_count = self.persistent_count
        sections = splitre(r"(num\([^)]*\))", text)
        inflection = []
        for section in sections:
            (section, count) = subn(r"num\(\s*?(?:([^),]*)(?:,([^)]*))?)?\)", self.nummo, section)
            if not count:
                total = -1
                while total:
                    (section, total) = subn(r"(?x)\bplural     \( ([^),]*) (, ([^)]*\)*) )? \)  ", self.plmo, section)
                    (section, count) = subn(
                        r"(?x)\bplural_noun   \( ([^),]*) (, ([^)]*\)*) )? \)  ", self.plnounmo, section
                    )
                    total += count
                    (section, count) = subn(
                        r"(?x)\bplural_verb   \( ([^),]*) (, ([^)]*\)*) )? \)  ", self.plverbmo, section
                    )
                    total += count
                    (section, count) = subn(
                        r"(?x)\bplural_adj \( ([^),]*) (, ([^)]*\)*) )? \)  ", self.pladjmo, section
                    )
                    total += count
                    (section, count) = subn(
                        r"(?x)\bsingular_noun   \( ([^),]*) (, ([^)]*\)*) )? \)  ", self.sinounmo, section
                    )
                    total += count
                    (section, count) = subn(r"(?x)\ban?    \( ([^),]*) (, ([^)]*\)*) )? \)  ", self.amo, section)
                    total += count
                    (section, count) = subn(r"(?x)\bno    \( ([^),]*) (, ([^)]*\)*) )? \)  ", self.nomo, section)
                    total += count
                    (section, count) = subn(
                        r"(?x)\bordinal        \( ([^)]*\)*) \)            ", self.ordinalmo, section
                    )
                    total += count
                    (section, count) = subn(
                        r"(?x)\bnumber_to_words  \( ([^)]*\)*) \)            ", self.numwordsmo, section
                    )
                    total += count
                    (section, count) = subn(
                        r"(?x)\bpresent_participle \( ([^)]*\)*) \)            ", self.prespartmo, section
                    )
                    total += count
            inflection.append(section)
        self.persistent_count = save_persistent_count
        return "".join(inflection)

    def postprocess(self, orig, inflected):
        if "|" in inflected:
            inflected = inflected.split("|")[self.classical_dict["all"]]
        if orig == "I":
            return inflected
        if orig == orig.upper():
            return inflected.upper()
        if orig[0] == orig[0].upper():
            return "{}{}".format(inflected[0].upper(), inflected[1:])
        return inflected

    def partition_word(self, text):
        mo = search(r"\A(\s*)(.+?)(\s*)\Z", text)
        try:
            return mo.group(1), mo.group(2), mo.group(3)
        except AttributeError:
            return "", "", ""

    def plural(self, text, count=None):
        pre, word, post = self.partition_word(text)
        if not word:
            return text
        plural = self.postprocess(
            word,
            self._pl_special_adjective(word, count) or self._pl_special_verb(word, count) or self._plnoun(word, count),
        )
        return "{}{}{}".format(pre, plural, post)

    def plural_noun(self, text, count=None):
        pre, word, post = self.partition_word(text)
        if not word:
            return text
        plural = self.postprocess(word, self._plnoun(word, count))
        return "{}{}{}".format(pre, plural, post)

    def plural_verb(self, text, count=None):
        pre, word, post = self.partition_word(text)
        if not word:
            return text
        plural = self.postprocess(word, self._pl_special_verb(word, count) or self._pl_general_verb(word, count))
        return "{}{}{}".format(pre, plural, post)

    def plural_adj(self, text, count=None):
        pre, word, post = self.partition_word(text)
        if not word:
            return text
        plural = self.postprocess(word, self._pl_special_adjective(word, count) or word)
        return "{}{}{}".format(pre, plural, post)

    def compare(self, word1, word2):
        return (
            self._plequal(word1, word2, self.plural_noun)
            or self._plequal(word1, word2, self.plural_verb)
            or self._plequal(word1, word2, self.plural_adj)
        )

    def compare_nouns(self, word1, word2):
        return self._plequal(word1, word2, self.plural_noun)

    def compare_verbs(self, word1, word2):
        return self._plequal(word1, word2, self.plural_verb)

    def compare_adjs(self, word1, word2):
        return self._plequal(word1, word2, self.plural_adj)

    def singular_noun(self, text, count=None, gender=None):
        pre, word, post = self.partition_word(text)
        if not word:
            return text
        sing = self._sinoun(word, count=count, gender=gender)
        if sing is not False:
            plural = self.postprocess(word, self._sinoun(word, count=count, gender=gender))
            return "{}{}{}".format(pre, plural, post)
        return False

    def _plequal(self, word1, word2, pl):
        classval = self.classical_dict.copy()
        self.classical_dict = all_classical.copy()
        if word1 == word2:
            return "eq"
        if word1 == pl(word2):
            return "p:s"
        if pl(word1) == word2:
            return "s:p"
        self.classical_dict = no_classical.copy()
        if word1 == pl(word2):
            return "p:s"
        if pl(word1) == word2:
            return "s:p"
        self.classical_dict = classval.copy()
        if pl == self.plural or pl == self.plural_noun:
            if self._pl_check_plurals_N(word1, word2):
                return "p:p"
            if self._pl_check_plurals_N(word2, word1):
                return "p:p"
        if pl == self.plural or pl == self.plural_adj:
            if self._pl_check_plurals_adj(word1, word2):
                return "p:p"
        return False

    def _pl_reg_plurals(self, pair, stems, end1, end2):
        if search(r"({})({}\|\1{}|{}\|\1{})".format(stems, end1, end2, end2, end1), pair):
            return True
        return False

    def _pl_check_plurals_N(self, word1, word2):
        pair = "{}|{}".format(word1, word2)
        if pair in list(pl_sb_irregular_s.values()):
            return True
        if pair in list(pl_sb_irregular.values()):
            return True
        if pair in list(pl_sb_irregular_caps.values()):
            return True
        for stems, end1, end2 in (
            (pl_sb_C_a_ata, "as", "ata"),
            (pl_sb_C_is_ides, "is", "ides"),
            (pl_sb_C_a_ae, "s", "e"),
            (pl_sb_C_en_ina, "ens", "ina"),
            (pl_sb_C_um_a, "ums", "a"),
            (pl_sb_C_us_i, "uses", "i"),
            (pl_sb_C_on_a, "ons", "a"),
            (pl_sb_C_o_i_stems, "os", "i"),
            (pl_sb_C_ex_ices, "exes", "ices"),
            (pl_sb_C_ix_ices, "ixes", "ices"),
            (pl_sb_C_i, "s", "i"),
            (pl_sb_C_im, "s", "im"),
            (".*eau", "s", "x"),
            (".*ieu", "s", "x"),
            (".*tri", "xes", "ces"),
            (".{2,}[yia]n", "xes", "ges"),
        ):
            if self._pl_reg_plurals(pair, stems, end1, end2):
                return True
        return False

    def _pl_check_plurals_adj(self, word1, word2):
        word1a = word1[: word1.rfind("'")] if word1.endswith(("'s", "'")) else ""
        word2a = word2[: word2.rfind("'")] if word2.endswith(("'s", "'")) else ""
        if word1a:
            if word2a and (self._pl_check_plurals_N(word1a, word2a) or self._pl_check_plurals_N(word2a, word1a)):
                return True
        return False

    def get_count(self, count=None):
        if count is None and self.persistent_count is not None:
            count = self.persistent_count
        if count is not None:
            count = (
                1
                if (
                    (str(count) in pl_count_one)
                    or (self.classical_dict["zero"] and str(count).lower() in pl_count_zero)
                )
                else 2
            )
        else:
            count = ""
        return count

    def _plnoun(self, word, count=None):
        count = self.get_count(count)
        if count == 1:
            return word
        value = self.ud_match(word, self.pl_sb_user_defined)
        if value is not None:
            return value
        if word == "":
            return word
        lowerword = word.lower()
        if lowerword in pl_sb_uninflected_complete:
            return word
        if word in pl_sb_uninflected_caps:
            return word
        for k, v in pl_sb_uninflected_bysize.items():
            if lowerword[-k:] in v:
                return word
        if self.classical_dict["herd"] and lowerword in pl_sb_uninflected_herd:
            return word
        mo = search(r"^(?:%s)$" % pl_sb_postfix_adj_stems, word, IGNORECASE)
        if mo and mo.group(2) != "":
            return "{}{}".format(self._plnoun(mo.group(1), 2), mo.group(2))
        if " a " in lowerword or "-a-" in lowerword:
            mo = search(r"^(?:%s)$" % pl_sb_prep_dual_compound, word, IGNORECASE)
            if mo and mo.group(2) != "" and mo.group(3) != "":
                return "{}{}{}".format(self._plnoun(mo.group(1), 2), mo.group(2), self._plnoun(mo.group(3)))
        lowersplit = lowerword.split(" ")
        if len(lowersplit) >= 3:
            for numword in range(1, len(lowersplit) - 1):
                if lowersplit[numword] in pl_prep_list_da:
                    return " ".join(
                        lowersplit[: numword - 1] + [self._plnoun(lowersplit[numword - 1], 2)] + lowersplit[numword:]
                    )
        lowersplit = lowerword.split("-")
        if len(lowersplit) >= 3:
            for numword in range(1, len(lowersplit) - 1):
                if lowersplit[numword] in pl_prep_list_da:
                    return " ".join(
                        lowersplit[: numword - 1]
                        + [self._plnoun(lowersplit[numword - 1], 2) + "-" + lowersplit[numword] + "-"]
                    ) + " ".join(lowersplit[(numword + 1) :])
        for k, v in pl_pron_acc_keys_bysize.items():
            if lowerword[-k:] in v:
                for pk, pv in pl_prep_bysize.items():
                    if lowerword[:pk] in pv:
                        if lowerword.split() == [lowerword[:pk], lowerword[-k:]]:
                            return lowerword[:-k] + pl_pron_acc[lowerword[-k:]]
        try:
            return pl_pron_nom[word.lower()]
        except KeyError:
            pass
        try:
            return pl_pron_acc[word.lower()]
        except KeyError:
            pass
        wordsplit = word.split()
        wordlast = wordsplit[-1]
        lowerwordlast = wordlast.lower()
        if wordlast in list(pl_sb_irregular_caps.keys()):
            llen = len(wordlast)
            return "{}{}".format(word[:-llen], pl_sb_irregular_caps[wordlast])
        if lowerwordlast in list(pl_sb_irregular.keys()):
            llen = len(lowerwordlast)
            return "{}{}".format(word[:-llen], pl_sb_irregular[lowerwordlast])
        if (" ".join(wordsplit[-2:])).lower() in list(pl_sb_irregular_compound.keys()):
            llen = len(" ".join(wordsplit[-2:]))
            return "{}{}".format(word[:-llen], pl_sb_irregular_compound[(" ".join(wordsplit[-2:])).lower()])
        if lowerword[-3:] == "quy":
            return word[:-1] + "ies"
        if lowerword[-6:] == "person":
            if self.classical_dict["persons"]:
                return word + "s"
            else:
                return word[:-4] + "ople"
        if lowerword[-3:] == "man":
            for k, v in pl_sb_U_man_mans_bysize.items():
                if lowerword[-k:] in v:
                    return word + "s"
            for k, v in pl_sb_U_man_mans_caps_bysize.items():
                if word[-k:] in v:
                    return word + "s"
            return word[:-3] + "men"
        if lowerword[-5:] == "mouse":
            return word[:-5] + "mice"
        if lowerword[-5:] == "louse":
            return word[:-5] + "lice"
        if lowerword[-5:] == "goose":
            return word[:-5] + "geese"
        if lowerword[-5:] == "tooth":
            return word[:-5] + "teeth"
        if lowerword[-4:] == "foot":
            return word[:-4] + "feet"
        if lowerword == "die":
            return "dice"
        if lowerword[-4:] == "ceps":
            return word
        if lowerword[-4:] == "zoon":
            return word[:-2] + "a"
        if lowerword[-3:] in ("cis", "sis", "xis"):
            return word[:-2] + "es"
        for lastlet, d, numend, post in (
            ("h", pl_sb_U_ch_chs_bysize, None, "s"),
            ("x", pl_sb_U_ex_ices_bysize, -2, "ices"),
            ("x", pl_sb_U_ix_ices_bysize, -2, "ices"),
            ("m", pl_sb_U_um_a_bysize, -2, "a"),
            ("s", pl_sb_U_us_i_bysize, -2, "i"),
            ("n", pl_sb_U_on_a_bysize, -2, "a"),
            ("a", pl_sb_U_a_ae_bysize, None, "e"),
        ):
            if lowerword[-1] == lastlet:
                for k, v in d.items():
                    if lowerword[-k:] in v:
                        return word[:numend] + post
        if self.classical_dict["ancient"]:
            if lowerword[-4:] == "trix":
                return word[:-1] + "ces"
            if lowerword[-3:] in ("eau", "ieu"):
                return word + "x"
            if lowerword[-3:] in ("ynx", "inx", "anx") and len(word) > 4:
                return word[:-1] + "ges"
            for lastlet, d, numend, post in (
                ("n", pl_sb_C_en_ina_bysize, -2, "ina"),
                ("x", pl_sb_C_ex_ices_bysize, -2, "ices"),
                ("x", pl_sb_C_ix_ices_bysize, -2, "ices"),
                ("m", pl_sb_C_um_a_bysize, -2, "a"),
                ("s", pl_sb_C_us_i_bysize, -2, "i"),
                ("s", pl_sb_C_us_us_bysize, None, ""),
                ("a", pl_sb_C_a_ae_bysize, None, "e"),
                ("a", pl_sb_C_a_ata_bysize, None, "ta"),
                ("s", pl_sb_C_is_ides_bysize, -1, "des"),
                ("o", pl_sb_C_o_i_bysize, -1, "i"),
                ("n", pl_sb_C_on_a_bysize, -2, "a"),
            ):
                if lowerword[-1] == lastlet:
                    for k, v in d.items():
                        if lowerword[-k:] in v:
                            return word[:numend] + post
            for d, numend, post in (
                (pl_sb_C_i_bysize, None, "i"),
                (pl_sb_C_im_bysize, None, "im"),
            ):
                for k, v in d.items():
                    if lowerword[-k:] in v:
                        return word[:numend] + post
        if lowerword in pl_sb_singular_s_complete:
            return word + "es"
        for k, v in pl_sb_singular_s_bysize.items():
            if lowerword[-k:] in v:
                return word + "es"
        if lowerword[-2:] == "es" and word[0] == word[0].upper():
            return word + "es"
        if lowerword[-1] == "z":
            for k, v in pl_sb_z_zes_bysize.items():
                if lowerword[-k:] in v:
                    return word + "es"
            if lowerword[-2:-1] != "z":
                return word + "zes"
        if lowerword[-2:] == "ze":
            for k, v in pl_sb_ze_zes_bysize.items():
                if lowerword[-k:] in v:
                    return word + "s"
        if lowerword[-2:] in ("ch", "sh", "zz", "ss") or lowerword[-1] == "x":
            return word + "es"
        if lowerword[-3:] in ("elf", "alf", "olf"):
            return word[:-1] + "ves"
        if lowerword[-3:] == "eaf" and lowerword[-4:-3] != "d":
            return word[:-1] + "ves"
        if lowerword[-4:] in ("nife", "life", "wife"):
            return word[:-2] + "ves"
        if lowerword[-3:] == "arf":
            return word[:-1] + "ves"
        if lowerword[-1] == "y":
            if lowerword[-2:-1] in "aeiou" or len(word) == 1:
                return word + "s"
            if self.classical_dict["names"]:
                if lowerword[-1] == "y" and word[0] == word[0].upper():
                    return word + "s"
            return word[:-1] + "ies"
        if lowerword in pl_sb_U_o_os_complete:
            return word + "s"
        for k, v in pl_sb_U_o_os_bysize.items():
            if lowerword[-k:] in v:
                return word + "s"
        if lowerword[-2:] in ("ao", "eo", "io", "oo", "uo"):
            return word + "s"
        if lowerword[-1] == "o":
            return word + "es"
        return "%ss" % word

    def _pl_special_verb(self, word, count=None):
        if self.classical_dict["zero"] and str(count).lower() in pl_count_zero:
            return False
        count = self.get_count(count)
        if count == 1:
            return word
        value = self.ud_match(word, self.pl_v_user_defined)
        if value is not None:
            return value
        lowerword = word.lower()
        try:
            firstword = lowerword.split()[0]
        except IndexError:
            return False
        if firstword in list(plverb_irregular_pres.keys()):
            return "{}{}".format(plverb_irregular_pres[firstword], word[len(firstword) :])
        if firstword in plverb_irregular_non_pres:
            return word
        if firstword.endswith("n't") and firstword[:-3] in list(plverb_irregular_pres.keys()):
            return "{}n't{}".format(plverb_irregular_pres[firstword[:-3]], word[len(firstword) :])
        if firstword.endswith("n't"):
            return word
        mo = search(r"^(%s)$" % plverb_special_s, word)
        if mo:
            return False
        if search(r"\s", word):
            return False
        if lowerword == "quizzes":
            return "quiz"
        if lowerword[-4:] in ("ches", "shes", "zzes", "sses") or lowerword[-3:] == "xes":
            return word[:-2]
        if lowerword[-3:] == "ies" and len(word) > 3:
            return lowerword[:-3] + "y"
        if (
            lowerword in pl_v_oes_oe
            or lowerword[-4:] in pl_v_oes_oe_endings_size4
            or lowerword[-5:] in pl_v_oes_oe_endings_size5
        ):
            return word[:-1]
        if lowerword.endswith("oes") and len(word) > 3:
            return lowerword[:-2]
        mo = search(r"^(.*[^s])s$", word, IGNORECASE)
        if mo:
            return mo.group(1)
        return False

    def _pl_general_verb(self, word, count=None):
        count = self.get_count(count)
        if count == 1:
            return word
        mo = search(r"^(%s)((\s.*)?)$" % plverb_ambiguous_pres_keys, word, IGNORECASE)
        if mo:
            return "{}{}".format(plverb_ambiguous_pres[mo.group(1).lower()], mo.group(2))
        mo = search(r"^(%s)((\s.*)?)$" % plverb_ambiguous_non_pres, word, IGNORECASE)
        if mo:
            return word
        return word

    def _pl_special_adjective(self, word, count=None):
        count = self.get_count(count)
        if count == 1:
            return word
        value = self.ud_match(word, self.pl_adj_user_defined)
        if value is not None:
            return value
        mo = search(r"^(%s)$" % pl_adj_special_keys, word, IGNORECASE)
        if mo:
            return "%s" % (pl_adj_special[mo.group(1).lower()])
        mo = search(r"^(%s)$" % pl_adj_poss_keys, word, IGNORECASE)
        if mo:
            return "%s" % (pl_adj_poss[mo.group(1).lower()])
        mo = search(r"^(.*)'s?$", word)
        if mo:
            pl = self.plural_noun(mo.group(1))
            trailing_s = "" if pl[-1] == "s" else "s"
            return "{}'{}".format(pl, trailing_s)
        return False

    def _sinoun(self, word, count=None, gender=None):
        count = self.get_count(count)
        if count == 2:
            return word
        try:
            if gender is None:
                gender = self.thegender
            elif gender not in singular_pronoun_genders:
                raise BadGenderError
        except (TypeError, IndexError):
            raise BadGenderError
        value = self.ud_match(word, self.si_sb_user_defined)
        if value is not None:
            return value
        if word == "":
            return word
        lowerword = word.lower()
        if word in si_sb_ois_oi_case:
            return word[:-1]
        if lowerword in pl_sb_uninflected_complete:
            return word
        if word in pl_sb_uninflected_caps:
            return word
        for k, v in pl_sb_uninflected_bysize.items():
            if lowerword[-k:] in v:
                return word
        if self.classical_dict["herd"] and lowerword in pl_sb_uninflected_herd:
            return word
        if lowerword in pl_sb_C_us_us:
            return word
        mo = search(r"^(?:%s)$" % pl_sb_postfix_adj_stems, word, IGNORECASE)
        if mo and mo.group(2) != "":
            return "{}{}".format(self._sinoun(mo.group(1), 1, gender=gender), mo.group(2))
        lowersplit = lowerword.split(" ")
        if len(lowersplit) >= 3:
            for numword in range(1, len(lowersplit) - 1):
                if lowersplit[numword] in pl_prep_list_da:
                    return " ".join(
                        lowersplit[: numword - 1]
                        + [self._sinoun(lowersplit[numword - 1], 1, gender=gender) or lowersplit[numword - 1]]
                        + lowersplit[numword:]
                    )
        lowersplit = lowerword.split("-")
        if len(lowersplit) >= 3:
            for numword in range(1, len(lowersplit) - 1):
                if lowersplit[numword] in pl_prep_list_da:
                    return " ".join(
                        lowersplit[: numword - 1]
                        + [
                            (self._sinoun(lowersplit[numword - 1], 1, gender=gender) or lowersplit[numword - 1])
                            + "-"
                            + lowersplit[numword]
                            + "-"
                        ]
                    ) + " ".join(lowersplit[(numword + 1) :])
        for k, v in si_pron_acc_keys_bysize.items():
            if lowerword[-k:] in v:
                for pk, pv in pl_prep_bysize.items():
                    if lowerword[:pk] in pv:
                        if lowerword.split() == [lowerword[:pk], lowerword[-k:]]:
                            return lowerword[:-k] + get_si_pron("acc", lowerword[-k:], gender)
        try:
            return get_si_pron("nom", word.lower(), gender)
        except KeyError:
            pass
        try:
            return get_si_pron("acc", word.lower(), gender)
        except KeyError:
            pass
        wordsplit = word.split()
        wordlast = wordsplit[-1]
        lowerwordlast = wordlast.lower()
        if wordlast in list(si_sb_irregular_caps.keys()):
            llen = len(wordlast)
            return "{}{}".format(word[:-llen], si_sb_irregular_caps[wordlast])
        if lowerwordlast in list(si_sb_irregular.keys()):
            llen = len(lowerwordlast)
            return "{}{}".format(word[:-llen], si_sb_irregular[lowerwordlast])
        if (" ".join(wordsplit[-2:])).lower() in list(si_sb_irregular_compound.keys()):
            llen = len(" ".join(wordsplit[-2:]))
            return "{}{}".format(word[:-llen], si_sb_irregular_compound[(" ".join(wordsplit[-2:])).lower()])
        if lowerword[-5:] == "quies":
            return word[:-3] + "y"
        if lowerword[-7:] == "persons":
            return word[:-1]
        if lowerword[-6:] == "people":
            return word[:-4] + "rson"
        if lowerword[-4:] == "mans":
            for k, v in si_sb_U_man_mans_bysize.items():
                if lowerword[-k:] in v:
                    return word[:-1]
            for k, v in si_sb_U_man_mans_caps_bysize.items():
                if word[-k:] in v:
                    return word[:-1]
        if lowerword[-3:] == "men":
            return word[:-3] + "man"
        if lowerword[-4:] == "mice":
            return word[:-4] + "mouse"
        if lowerword[-4:] == "lice":
            return word[:-4] + "louse"
        if lowerword[-5:] == "geese":
            return word[:-5] + "goose"
        if lowerword[-5:] == "teeth":
            return word[:-5] + "tooth"
        if lowerword[-4:] == "feet":
            return word[:-4] + "foot"
        if lowerword == "dice":
            return "die"
        if lowerword[-4:] == "ceps":
            return word
        if lowerword[-3:] == "zoa":
            return word[:-1] + "on"
        for lastlet, d, numend, post in (
            ("s", si_sb_U_ch_chs_bysize, -1, ""),
            ("s", si_sb_U_ex_ices_bysize, -4, "ex"),
            ("s", si_sb_U_ix_ices_bysize, -4, "ix"),
            ("a", si_sb_U_um_a_bysize, -1, "um"),
            ("i", si_sb_U_us_i_bysize, -1, "us"),
            ("a", si_sb_U_on_a_bysize, -1, "on"),
            ("e", si_sb_U_a_ae_bysize, -1, ""),
        ):
            if lowerword[-1] == lastlet:
                for k, v in d.items():
                    if lowerword[-k:] in v:
                        return word[:numend] + post
        if self.classical_dict["ancient"]:
            if lowerword[-6:] == "trices":
                return word[:-3] + "x"
            if lowerword[-4:] in ("eaux", "ieux"):
                return word[:-1]
            if lowerword[-5:] in ("ynges", "inges", "anges") and len(word) > 6:
                return word[:-3] + "x"
            for lastlet, d, numend, post in (
                ("a", si_sb_C_en_ina_bysize, -3, "en"),
                ("s", si_sb_C_ex_ices_bysize, -4, "ex"),
                ("s", si_sb_C_ix_ices_bysize, -4, "ix"),
                ("a", si_sb_C_um_a_bysize, -1, "um"),
                ("i", si_sb_C_us_i_bysize, -1, "us"),
                ("s", pl_sb_C_us_us_bysize, None, ""),
                ("e", si_sb_C_a_ae_bysize, -1, ""),
                ("a", si_sb_C_a_ata_bysize, -2, ""),
                ("s", si_sb_C_is_ides_bysize, -3, "s"),
                ("i", si_sb_C_o_i_bysize, -1, "o"),
                ("a", si_sb_C_on_a_bysize, -1, "on"),
                ("m", si_sb_C_im_bysize, -2, ""),
                ("i", si_sb_C_i_bysize, -1, ""),
            ):
                if lowerword[-1] == lastlet:
                    for k, v in d.items():
                        if lowerword[-k:] in v:
                            return word[:numend] + post
        if lowerword[-6:] == "houses" or word in si_sb_uses_use_case or lowerword in si_sb_uses_use:
            return word[:-1]
        if word in si_sb_ies_ie_case or lowerword in si_sb_ies_ie:
            return word[:-1]
        if lowerword[-5:] == "shoes" or word in si_sb_oes_oe_case or lowerword in si_sb_oes_oe:
            return word[:-1]
        if word in si_sb_sses_sse_case or lowerword in si_sb_sses_sse:
            return word[:-1]
        if lowerword in si_sb_singular_s_complete:
            return word[:-2]
        for k, v in si_sb_singular_s_bysize.items():
            if lowerword[-k:] in v:
                return word[:-2]
        if lowerword[-4:] == "eses" and word[0] == word[0].upper():
            return word[:-2]
        if lowerword in si_sb_z_zes:
            return word[:-2]
        if lowerword in si_sb_zzes_zz:
            return word[:-2]
        if lowerword[-4:] == "zzes":
            return word[:-3]
        if word in si_sb_ches_che_case or lowerword in si_sb_ches_che:
            return word[:-1]
        if lowerword[-4:] in ("ches", "shes"):
            return word[:-2]
        if lowerword in si_sb_xes_xe:
            return word[:-1]
        if lowerword[-3:] == "xes":
            return word[:-2]
        if word in si_sb_ves_ve_case or lowerword in si_sb_ves_ve:
            return word[:-1]
        if lowerword[-3:] == "ves":
            if lowerword[-5:-3] in ("el", "al", "ol"):
                return word[:-3] + "f"
            if lowerword[-5:-3] == "ea" and word[-6:-5] != "d":
                return word[:-3] + "f"
            if lowerword[-5:-3] in ("ni", "li", "wi"):
                return word[:-3] + "fe"
            if lowerword[-5:-3] == "ar":
                return word[:-3] + "f"
        if lowerword[-2:] == "ys":
            if len(lowerword) > 2 and lowerword[-3] in "aeiou":
                return word[:-1]
            if self.classical_dict["names"]:
                if lowerword[-2:] == "ys" and word[0] == word[0].upper():
                    return word[:-1]
        if lowerword[-3:] == "ies":
            return word[:-3] + "y"
        if lowerword[-2:] == "os":
            if lowerword in si_sb_U_o_os_complete:
                return word[:-1]
            for k, v in si_sb_U_o_os_bysize.items():
                if lowerword[-k:] in v:
                    return word[:-1]
            if lowerword[-3:] in ("aos", "eos", "ios", "oos", "uos"):
                return word[:-1]
        if lowerword[-3:] == "oes":
            return word[:-2]
        if word in si_sb_es_is:
            return word[:-2] + "is"
        if lowerword[-1] == "s":
            return word[:-1]
        return False

    def a(self, text, count=1):
        mo = search(r"\A(\s*)(?:an?\s+)?(.+?)(\s*)\Z", text, IGNORECASE)
        if mo:
            word = mo.group(2)
            if not word:
                return text
            pre = mo.group(1)
            post = mo.group(3)
            result = self._indef_article(word, count)
            return "{}{}{}".format(pre, result, post)
        return ""

    an = a

    def _indef_article(self, word, count):
        mycount = self.get_count(count)
        if mycount != 1:
            return "{} {}".format(count, word)
        value = self.ud_match(word, self.A_a_user_defined)
        if value is not None:
            return "{} {}".format(value, word)
        for a in (
            (r"^(%s)" % A_ordinal_a, "a"),
            (r"^(%s)" % A_ordinal_an, "an"),
        ):
            mo = search(a[0], word, IGNORECASE)
            if mo:
                return "{} {}".format(a[1], word)
        for a in (
            (r"^(%s)" % A_explicit_an, "an"),
            (r"^[aefhilmnorsx]$", "an"),
            (r"^[bcdgjkpqtuvwyz]$", "a"),
        ):
            mo = search(a[0], word, IGNORECASE)
            if mo:
                return "{} {}".format(a[1], word)
        for a in (
            (r"(%s)" % A_abbrev, "an", VERBOSE),
            (r"^[aefhilmnorsx][.-]", "an", IGNORECASE),
            (r"^[a-z][.-]", "a", IGNORECASE),
        ):
            mo = search(a[0], word, a[2])
            if mo:
                return "{} {}".format(a[1], word)
        mo = search(r"^[^aeiouy]", word, IGNORECASE)
        if mo:
            return "a %s" % word
        for a in (
            (r"^e[uw]", "a"),
            (r"^onc?e\b", "a"),
            (r"^onetime\b", "a"),
            (r"^uni([^nmd]|mo)", "a"),
            (r"^u[bcfghjkqrst][aeiou]", "a"),
            (r"^ukr", "a"),
            (r"^(%s)" % A_explicit_a, "a"),
        ):
            mo = search(a[0], word, IGNORECASE)
            if mo:
                return "{} {}".format(a[1], word)
        mo = search(r"^U[NK][AIEO]?", word)
        if mo:
            return "a %s" % word
        mo = search(r"^[aeiou]", word, IGNORECASE)
        if mo:
            return "an %s" % word
        mo = search(r"^(%s)" % A_y_cons, word, IGNORECASE)
        if mo:
            return "an %s" % word
        return "a %s" % word

    def no(self, text, count=None):
        if count is None and self.persistent_count is not None:
            count = self.persistent_count
        if count is None:
            count = 0
        mo = search(r"\A(\s*)(.+?)(\s*)\Z", text)
        pre = mo.group(1)
        word = mo.group(2)
        post = mo.group(3)
        if str(count).lower() in pl_count_zero:
            return "{}no {}{}".format(pre, self.plural(word, 0), post)
        else:
            return "{}{} {}{}".format(pre, count, self.plural(word, count), post)

    def present_participle(self, word):
        plv = self.plural_verb(word, 2)
        for pat, repl in (
            (r"ie$", r"y"),
            (r"ue$", r"u"),
            (r"([auy])e$", r"\g<1>"),
            (r"ski$", r"ski"),
            (r"[^b]i$", r""),
            (r"^(are|were)$", r"be"),
            (r"^(had)$", r"hav"),
            (r"^(hoe)$", r"\g<1>"),
            (r"([^e])e$", r"\g<1>"),
            (r"([^ ])ied$", r"\g<1>y"),
            (r"([^ ])ed$", r"\g<1>"),
            (r"([^ ])ing$", r"\g<1>"),
            (r"er$", r"er"),
            (r"([^aeiou][aeiouy]([bdgmnprst]))$", r"\g<1>\g<2>"),
        ):
            (ans, num) = subn(pat, repl, plv)
            if num:
                return "%sing" % ans
        return "%sing" % ans

    def ordinal(self, num):
        if match(r"\d", str(num)):
            try:
                num % 2
                n = num
            except TypeError:
                if "." in str(num):
                    try:
                        n = int(num[-1])
                    except ValueError:
                        n = int(num[:-1])
                else:
                    n = int(num)
            try:
                post = nth[n % 100]
            except KeyError:
                post = nth[n % 10]
            return "{}{}".format(num, post)
        else:
            mo = search(r"(%s)\Z" % ordinal_suff, num)
            try:
                post = ordinal[mo.group(1)]
                return resub(r"(%s)\Z" % ordinal_suff, post, num)
            except AttributeError:
                return "%sth" % num

    def millfn(self, ind=0):
        if ind > len(mill) - 1:
            print3("number out of range")
            raise NumOutOfRangeError
        return mill[ind]

    def unitfn(self, units, mindex=0):
        return "{}{}".format(unit[units], self.millfn(mindex))

    def tenfn(self, tens, units, mindex=0):
        if tens != 1:
            return "{}{}{}{}".format(ten[tens], "-" if tens and units else "", unit[units], self.millfn(mindex))
        return "{}{}".format(teen[units], mill[mindex])

    def hundfn(self, hundreds, tens, units, mindex):
        if hundreds:
            andword = " %s " % self.number_args["andword"] if tens or units else ""
            return "{} hundred{}{}{}, ".format(unit[hundreds], andword, self.tenfn(tens, units), self.millfn(mindex))
        if tens or units:
            return "{}{}, ".format(self.tenfn(tens, units), self.millfn(mindex))
        return ""

    def group1sub(self, mo):
        units = int(mo.group(1))
        if units == 1:
            return " %s, " % self.number_args["one"]
        elif units:
            return "%s, " % unit[units]
        else:
            return " %s, " % self.number_args["zero"]

    def group1bsub(self, mo):
        units = int(mo.group(1))
        if units:
            return "%s, " % unit[units]
        else:
            return " %s, " % self.number_args["zero"]

    def group2sub(self, mo):
        tens = int(mo.group(1))
        units = int(mo.group(2))
        if tens:
            return "%s, " % self.tenfn(tens, units)
        if units:
            return " {} {}, ".format(self.number_args["zero"], unit[units])
        return " {} {}, ".format(self.number_args["zero"], self.number_args["zero"])

    def group3sub(self, mo):
        hundreds = int(mo.group(1))
        tens = int(mo.group(2))
        units = int(mo.group(3))
        if hundreds == 1:
            hunword = " %s" % self.number_args["one"]
        elif hundreds:
            hunword = "%s" % unit[hundreds]
        else:
            hunword = " %s" % self.number_args["zero"]
        if tens:
            tenword = self.tenfn(tens, units)
        elif units:
            tenword = " {} {}".format(self.number_args["zero"], unit[units])
        else:
            tenword = " {} {}".format(self.number_args["zero"], self.number_args["zero"])
        return "{} {}, ".format(hunword, tenword)

    def hundsub(self, mo):
        ret = self.hundfn(int(mo.group(1)), int(mo.group(2)), int(mo.group(3)), self.mill_count)
        self.mill_count += 1
        return ret

    def tensub(self, mo):
        return "%s, " % self.tenfn(int(mo.group(1)), int(mo.group(2)), self.mill_count)

    def unitsub(self, mo):
        return "%s, " % self.unitfn(int(mo.group(1)), self.mill_count)

    def enword(self, num, group):
        if group == 1:
            num = resub(r"(\d)", self.group1sub, num)
        elif group == 2:
            num = resub(r"(\d)(\d)", self.group2sub, num)
            num = resub(r"(\d)", self.group1bsub, num, 1)
        elif group == 3:
            num = resub(r"(\d)(\d)(\d)", self.group3sub, num)
            num = resub(r"(\d)(\d)", self.group2sub, num, 1)
            num = resub(r"(\d)", self.group1sub, num, 1)
        elif int(num) == 0:
            num = self.number_args["zero"]
        elif int(num) == 1:
            num = self.number_args["one"]
        else:
            num = num.lstrip().lstrip("0")
            self.mill_count = 0
            mo = search(r"(\d)(\d)(\d)(?=\D*\Z)", num)
            while mo:
                num = resub(r"(\d)(\d)(\d)(?=\D*\Z)", self.hundsub, num, 1)
                mo = search(r"(\d)(\d)(\d)(?=\D*\Z)", num)
            num = resub(r"(\d)(\d)(?=\D*\Z)", self.tensub, num, 1)
            num = resub(r"(\d)(?=\D*\Z)", self.unitsub, num, 1)
        return num

    def blankfn(self, mo):
        return ""

    def commafn(self, mo):
        return ","

    def spacefn(self, mo):
        return " "

    def number_to_words(
        self,
        num,
        wantlist=False,
        group=0,
        comma=",",
        andword="and",
        zero="zero",
        one="one",
        decimal="point",
        threshold=None,
    ):
        self.number_args = dict(andword=andword, zero=zero, one=one)
        num = "%s" % num
        if threshold is not None and float(num) > threshold:
            spnum = num.split(".", 1)
            while comma:
                (spnum[0], n) = subn(r"(\d)(\d{3}(?:,|\Z))", r"\1,\2", spnum[0])
                if n == 0:
                    break
            try:
                return "{}.{}".format(spnum[0], spnum[1])
            except IndexError:
                return "%s" % spnum[0]
        if group < 0 or group > 3:
            raise BadChunkingOptionError
        nowhite = num.lstrip()
        if nowhite[0] == "+":
            sign = "plus"
        elif nowhite[0] == "-":
            sign = "minus"
        else:
            sign = ""
        myord = num[-2:] in ("st", "nd", "rd", "th")
        if myord:
            num = num[:-2]
        finalpoint = False
        if decimal:
            if group != 0:
                chunks = num.split(".")
            else:
                chunks = num.split(".", 1)
            if chunks[-1] == "":
                chunks = chunks[:-1]
                finalpoint = True
        else:
            chunks = [num]
        first = 1
        loopstart = 0
        if chunks[0] == "":
            first = 0
            if len(chunks) > 1:
                loopstart = 1
        for i in range(loopstart, len(chunks)):
            chunk = chunks[i]
            chunk = resub(r"\D", self.blankfn, chunk)
            if chunk == "":
                chunk = "0"
            if group == 0 and (first == 0 or first == ""):
                chunk = self.enword(chunk, 1)
            else:
                chunk = self.enword(chunk, group)
            if chunk[-2:] == ", ":
                chunk = chunk[:-2]
            chunk = resub(r"\s+,", self.commafn, chunk)
            if group == 0 and first:
                chunk = resub(r", (\S+)\s+\Z", " %s \\1" % andword, chunk)
            chunk = resub(r"\s+", self.spacefn, chunk)
            chunk = chunk.strip()
            if first:
                first = ""
            chunks[i] = chunk
        numchunks = []
        if first != 0:
            numchunks = chunks[0].split("%s " % comma)
        if myord and numchunks:
            mo = search(r"(%s)\Z" % ordinal_suff, numchunks[-1])
            if mo:
                numchunks[-1] = resub(r"(%s)\Z" % ordinal_suff, ordinal[mo.group(1)], numchunks[-1])
            else:
                numchunks[-1] += "th"
        for chunk in chunks[1:]:
            numchunks.append(decimal)
            numchunks.extend(chunk.split("%s " % comma))
        if finalpoint:
            numchunks.append(decimal)
        if wantlist:
            if sign:
                numchunks = [sign] + numchunks
            return numchunks
        elif group:
            signout = "%s " % sign if sign else ""
            return "{}{}".format(signout, ", ".join(numchunks))
        else:
            signout = "%s " % sign if sign else ""
            num = "{}{}".format(signout, numchunks.pop(0))
            if decimal is None:
                first = True
            else:
                first = not num.endswith(decimal)
            for nc in numchunks:
                if nc == decimal:
                    num += " %s" % nc
                    first = 0
                elif first:
                    num += "{} {}".format(comma, nc)
                else:
                    num += " %s" % nc
            return num

    def join(self, words, sep=None, sep_spaced=True, final_sep=None, conj="and", conj_spaced=True):
        if not words:
            return ""
        if len(words) == 1:
            return words[0]
        if conj_spaced:
            if conj == "":
                conj = " "
            else:
                conj = " %s " % conj
        if len(words) == 2:
            return "{}{}{}".format(words[0], conj, words[1])
        if sep is None:
            if "," in "".join(words):
                sep = ";"
            else:
                sep = ","
        if final_sep is None:
            final_sep = sep
        final_sep = "{}{}".format(final_sep, conj)
        if sep_spaced:
            sep += " "
        return "{}{}{}".format(sep.join(words[0:-1]), final_sep, words[-1])
