"""
Verse Games Business Logic Module for AREPO (Giochi in Versi).
Provides word transformation algorithms: Rhymes, Anagrams, Zeppe, Cambi, Bisenzi.
"""

from typing import List, Dict, Set, Tuple, Optional
from core.database.connection import DatabaseManager
from core.database.models import Word


class VerseLogic:
    """Business logic model for verse games and word transformations."""

    def __init__(self, db_mgr: Optional[DatabaseManager] = None):
        self.db_mgr = db_mgr or DatabaseManager()

    def find_rhymes(self, target_word: str, max_results: int = 50) -> List[str]:
        """
        Find perfect rhyming words ending with the same tonic rhyme suffix (min 3 letters).
        """
        w = target_word.strip().upper()
        if len(w) < 3:
            return []

        rhyme_suffix = w[-3:]
        session = self.db_mgr.get_core_session()
        try:
            results = session.query(Word.term).filter(
                Word.term.like(f"%{rhyme_suffix}"),
                Word.term != w
            ).limit(max_results).all()
            return [r[0] for r in results]
        finally:
            session.close()

    def find_anagrams(self, target_word: str) -> List[str]:
        """Find exact anagrams of a word."""
        w = target_word.strip().upper()
        if not w:
            return []

        sorted_target = ''.join(sorted(w))
        target_len = len(w)

        session = self.db_mgr.get_core_session()
        try:
            candidates = session.query(Word.term).filter(
                Word.length == target_len,
                Word.term != w
            ).limit(3000).all()

            anagrams = []
            for cand in candidates:
                term = cand[0]
                if ''.join(sorted(term)) == sorted_target:
                    anagrams.append(term)
            return anagrams
        finally:
            session.close()

    def find_zeppe(self, target_word: str) -> List[Tuple[str, str, int]]:
        """
        Find 'Zeppa' transformations: inserting 1 letter into target_word to form a valid word.
        Returns list of tuples: (resulting_word, inserted_letter, position)
        """
        w = target_word.strip().upper()
        if not w:
            return []

        target_len = len(w) + 1
        session = self.db_mgr.get_core_session()
        try:
            candidates = session.query(Word.term).filter(Word.length == target_len).limit(5000).all()
            cand_set = {c[0] for c in candidates}

            zeppe = []
            alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
            for pos in range(len(w) + 1):
                for char in alphabet:
                    inserted = w[:pos] + char + w[pos:]
                    if inserted in cand_set and inserted != w:
                        zeppe.append((inserted, char, pos))
            return zeppe
        finally:
            session.close()

    def find_cambi(self, target_word: str) -> List[Tuple[str, str, str, int]]:
        """
        Find 'Cambio di lettera' transformations: replacing 1 letter in target_word.
        Returns list of tuples: (resulting_word, old_char, new_char, position)
        """
        w = target_word.strip().upper()
        if not w:
            return []

        target_len = len(w)
        session = self.db_mgr.get_core_session()
        try:
            candidates = session.query(Word.term).filter(Word.length == target_len).limit(5000).all()
            cand_set = {c[0] for c in candidates}

            cambi = []
            alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
            for pos in range(len(w)):
                old_char = w[pos]
                for new_char in alphabet:
                    if new_char == old_char:
                        continue
                    changed = w[:pos] + new_char + w[pos + 1:]
                    if changed in cand_set:
                        cambi.append((changed, old_char, new_char, pos))
            return cambi
        finally:
            session.close()

    def find_bisenzi(self, target_word: str) -> List[str]:
        """
        Find 'Bisenzo' / Homonyms: words having multiple distinct dictionary meanings.
        """
        w = target_word.strip().upper()
        session = self.db_mgr.get_core_session()
        try:
            word_obj = session.query(Word).filter(Word.term == w).first()
            if word_obj and len(word_obj.definitions) >= 2:
                return [d.clue for d in word_obj.definitions]
            return []
        finally:
            session.close()
