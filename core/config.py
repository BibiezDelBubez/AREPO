"""
Configuration module for AREPO (Enigmistica Suite).
Contains default UI parameters, NLP lexicons, and app constants.
"""

from typing import Set, Dict, Any, Tuple

# Default NLP & Filtering Constraints
DEFAULT_MIN_WORDS: int = 2
DEFAULT_MAX_WORDS: int = 5
DEFAULT_MIN_LETTERS: int = 10
DEFAULT_MAX_LETTERS: int = 30
DEFAULT_SWEET_SPOT_MIN: int = 12
DEFAULT_SWEET_SPOT_MAX: int = 20
DEFAULT_VERB_STRICT: bool = True
DEFAULT_MIN_SCORE: float = 5.0
DEFAULT_MAX_RESULTS: int = 50
DEFAULT_RANDOM_SAMPLE: bool = True

# Evocative Lexicons for Rebus Score calculation
SENSORY_CHROMATIC_WORDS: Set[str] = frozenset({
    "rosso", "rossa", "rossi", "rosse", "blu", "azzurro", "azzurra", "azzurri", "azzurre",
    "verde", "verdi", "giallo", "gialla", "gialli", "gialle", "nero", "nera", "neri", "nere",
    "bianco", "bianca", "bianchi", "bianche", "dorato", "dorata", "dorati", "dorate",
    "argenteo", "argentea", "argentei", "argentee", "fosco", "fosca", "foschi", "fosche",
    "cupo", "cupa", "cupi", "cupe", "brillante", "brillanti", "luminoso", "luminosa",
    "luminosi", "luminose", "profumato", "profumata", "profumati", "profumate",
    "gelido", "gelida", "gelidi", "gelide", "tiepido", "tiepida", "silenzioso", "silenziosa",
    "mormorante", "mormoranti", "vibrante", "vibranti", "velato", "velata", "opaco", "opaca",
    "trasparente", "trasparenti", "scarlatto", "scarlatta", "smeraldo", "turchese", "zaffiro",
    "porpora", "violaceo", "violacea", "plumbeo", "plumbea", "caldo", "calda", "freddo", "fredda",
    "morbido", "morbida", "ruvido", "ruvida", "aspro", "aspra", "dolce", "profumata"
})

SPATIAL_EVOCATIVE_WORDS: Set[str] = frozenset({
    "alto", "alta", "alti", "alte", "profondo", "profonda", "profondi", "profonde",
    "remoto", "remota", "remoti", "remote", "nascosto", "nascosta", "nascosti", "nascoste",
    "deserto", "deserta", "deserti", "deserte", "solitario", "solitaria", "solitari", "solitarie",
    "eterno", "eterna", "eterni", "eterne", "antico", "antica", "antichi", "antiche",
    "segreto", "segreta", "segreti", "segrete", "invisibile", "invisibili", "immenso", "immensa",
    "lontano", "lontana", "lontani", "lontane", "oscuro", "oscura", "oscuri", "oscure",
    "sommerso", "sommersa", "silvestre", "notturno", "notturna", "marino", "marina",
    "stellato", "stellata", "sublime", "infinito", "infinita", "sotterraneo", "sotterranea"
})

GENERIC_PENALIZED_WORDS: Set[str] = frozenset({
    "bello", "bella", "belli", "belle", "grande", "grandi", "buono", "buona", "buoni", "buone",
    "piccolo", "piccola", "piccoli", "piccole", "nuovo", "nuova", "nuovi", "nuove",
    "vecchio", "vecchia", "vecchi", "vecchie", "cosa", "cose", "parte", "parti",
    "uomo", "uomini", "donna", "donne", "volta", "volte", "modo", "modi",
    "tipo", "tipi", "fatto", "fatti", "stato", "stati", "caso", "casi", "giorno", "giorni",
    "molto", "molta", "molti", "molte", "poco", "poca", "pochi", "poche", "stesso", "stessa"
})

APP_TITLE: str = "AREPO - Enigmistica Suite"
WINDOW_SIZE: str = "1280x850"
MIN_WINDOW_SIZE: Tuple[int, int] = (1100, 720)


def get_default_parameters() -> Dict[str, Any]:
    """DRY Helper: Return dictionary of default NLP search parameters."""
    return {
        "min_words": DEFAULT_MIN_WORDS,
        "max_words": DEFAULT_MAX_WORDS,
        "min_letters": DEFAULT_MIN_LETTERS,
        "max_letters": DEFAULT_MAX_LETTERS,
        "sweet_spot_min": DEFAULT_SWEET_SPOT_MIN,
        "sweet_spot_max": DEFAULT_SWEET_SPOT_MAX,
        "strict_verb_filter": DEFAULT_VERB_STRICT,
        "min_score": DEFAULT_MIN_SCORE,
        "max_results": DEFAULT_MAX_RESULTS,
        "random_sample": DEFAULT_RANDOM_SAMPLE
    }
