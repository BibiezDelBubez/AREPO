"""
Word Search Engine Module for AREPO.
Provides positional search across Italian dictionary words (from SQLite DB and list files)
with grammatical filtering, length bounds, and functional word exclusion.
"""

import os
from dataclasses import dataclass
from typing import List, Dict, Set, Optional, Any
import spacy

from core.engine.anarebus_engine import FUNCTIONAL_WORDS, COMMON_REBUS_SUBJECTS
from core.database.connection import DatabaseManager
from core.database.models import Word


@dataclass(frozen=True)
class WordSearchResult:
    """Immutable Data Transfer Object representing a matched word."""
    word: str
    category: str
    letters_count: int
    match_position: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "Parola": self.word,
            "Categoria Grammaticale": self.category,
            "N° Lettere": self.letters_count,
            "Posizione Match": self.match_position
        }


EXCLUDED_FUNCTIONAL_WORDS: Set[str] = set(FUNCTIONAL_WORDS).union({
    "il", "lo", "la", "i", "gli", "le", "un", "uno", "una", "un'",
    "di", "a", "da", "in", "con", "su", "per", "tra", "fra",
    "del", "dello", "della", "dei", "degli", "delle",
    "al", "allo", "alla", "ai", "agli", "alle",
    "dal", "dallo", "dalla", "dai", "dagli", "dalle",
    "nel", "nello", "nella", "nei", "negli", "nelle",
    "sul", "sullo", "sulla", "sui", "sugli", "sulle",
    "ed", "ad", "od", "se", "ma", "che", "non", "perché", "poiché", "quando", "come", "anche",
    "mi", "ti", "si", "ci", "vi", "ne", "me", "te", "io", "tu", "lui", "lei", "noi", "voi", "loro",
    "questo", "questa", "questi", "queste", "quello", "quella", "quelli", "quelle"
})

VERB_SUFFIXES = (
    "are", "ere", "ire", "ando", "endo", "ato", "ito", "uto",
    "arono", "erono", "irono", "avano", "evano", "ivano",
    "ero", "erò", "irò", "iamo", "ate", "ete", "ite", "asse", "esse", "isse"
)

ADJ_SUFFIXES = (
    "bile", "bili", "ivo", "iva", "ivi", "ive",
    "oso", "osa", "osi", "ose", "ale", "ali", "ile", "ili",
    "ico", "ica", "ici", "iche"
)

NOUN_SUFFIXES = (
    "zione", "zioni", "sione", "sioni", "mento", "menti",
    "ità", "tore", "tori", "trice", "trici", "ismo", "ismi",
    "ista", "isti", "este", "anza", "anze", "enza", "enze",
    "eria", "erie", "grafia", "logia"
)


class WordSearchEngine:
    """Core computational model for searching Italian dictionary words."""

    def __init__(self, spacy_model: str = "it_core_news_sm", db_mgr: Optional[DatabaseManager] = None):
        self.spacy_model = spacy_model
        self.nlp = None
        self.db_mgr = db_mgr or DatabaseManager()
        self.words_280k: List[str] = []
        self.words_60k: List[str] = []
        self._load_dictionaries()
        self._init_spacy()

    def _init_spacy(self) -> None:
        try:
            self.nlp = spacy.load(self.spacy_model, disable=["ner", "textcat"])
        except Exception:
            self.nlp = None

    def _load_dictionaries(self) -> None:
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        dict_dir = os.path.join(base_dir, "data", "dictionaries")
        
        file_280k = os.path.join(dict_dir, "italian_words_280k.txt")
        if os.path.exists(file_280k):
            with open(file_280k, encoding="utf-8", errors="ignore") as f:
                seen = set()
                for line in f:
                    w = line.strip().lower()
                    if w and w.isalpha() and w not in seen:
                        seen.add(w)
                        self.words_280k.append(w)

        file_60k = os.path.join(dict_dir, "italian_words.txt")
        if os.path.exists(file_60k):
            with open(file_60k, encoding="utf-8", errors="ignore") as f:
                seen = set()
                for line in f:
                    w = line.strip().lower()
                    if w and w.isalpha() and w not in seen:
                        seen.add(w)
                        self.words_60k.append(w)

        if not self.words_280k and not self.words_60k:
            fallback = sorted(list(set(COMMON_REBUS_SUBJECTS)))
            self.words_280k = fallback
            self.words_60k = fallback

    def classify_word(self, word: str, spacy_pos: Optional[str] = None) -> str:
        w_lower = word.lower()
        
        if w_lower in EXCLUDED_FUNCTIONAL_WORDS:
            return "FUNCT"

        if w_lower in COMMON_REBUS_SUBJECTS:
            return "Sostantivo"

        if w_lower.endswith(NOUN_SUFFIXES):
            return "Sostantivo"
        if w_lower.endswith(ADJ_SUFFIXES):
            return "Aggettivo"
        if w_lower.endswith("mente") and len(w_lower) > 5:
            return "Avverbio"

        if spacy_pos:
            if spacy_pos in ("NOUN", "PROPN"):
                return "Sostantivo"
            elif spacy_pos in ("VERB", "AUX"):
                return "Verbo"
            elif spacy_pos == "ADJ":
                return "Aggettivo"
            elif spacy_pos == "ADV":
                return "Avverbio"
            elif spacy_pos in ("ADP", "DET", "PRON", "CCONJ", "SCONJ"):
                return "FUNCT"

        if w_lower.endswith(VERB_SUFFIXES):
            return "Verbo"

        return "Sostantivo"

    def search_words(
        self,
        query: str,
        pos_mode: str = "start",
        category_filter: str = "all",
        min_letters: int = 3,
        max_letters: int = 20,
        dict_choice: str = "280k",
        max_results: int = 100
    ) -> List[WordSearchResult]:
        q = query.strip().lower()
        if not q or len(q) < 2:
            return []

        word_list = self.words_280k if dict_choice == "280k" and self.words_280k else self.words_60k
        if not word_list:
            word_list = self.words_280k

        matched_words = []
        scan_limit = max(max_results * 5, 500)

        for w in word_list:
            l_count = len(w)
            if not (min_letters <= l_count <= max_letters):
                continue

            match_label = ""
            if pos_mode == "start":
                if w.startswith(q):
                    match_label = "Inizio"
            elif pos_mode == "end":
                if w.endswith(q):
                    match_label = "Fine"
            elif pos_mode == "middle":
                if q in w and not w.startswith(q) and not w.endswith(q):
                    match_label = "In mezzo"
            else:  # "contains"
                if q in w:
                    if w.startswith(q):
                        match_label = "Inizio"
                    elif w.endswith(q):
                        match_label = "Fine"
                    else:
                        match_label = "In mezzo"

            if match_label:
                matched_words.append((w, match_label))
                if len(matched_words) >= scan_limit:
                    break

        if not matched_words:
            return []

        spacy_tags: Dict[str, str] = {}
        if self.nlp:
            raw_words = [item[0] for item in matched_words[:300]]
            try:
                docs = list(self.nlp.pipe(raw_words))
                for w_str, doc in zip(raw_words, docs):
                    if len(doc) > 0:
                        spacy_tags[w_str] = doc[0].pos_
            except Exception:
                pass

        results: List[WordSearchResult] = []
        for word_str, pos_label in matched_words:
            sp_pos = spacy_tags.get(word_str)
            cat = self.classify_word(word_str, spacy_pos=sp_pos)

            if cat == "FUNCT":
                continue

            if category_filter == "nouns" and cat != "Sostantivo":
                continue
            elif category_filter == "other" and cat == "Sostantivo":
                continue
            elif category_filter == "verbs" and cat != "Verbo":
                continue
            elif category_filter == "adjectives" and cat != "Aggettivo":
                continue

            results.append(WordSearchResult(
                word=word_str.upper(),
                category=cat,
                letters_count=len(word_str),
                match_position=pos_label
            ))

            if len(results) >= max_results:
                break

        return results
