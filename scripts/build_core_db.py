"""
Script to build core_dictionary.sqlite from text wordlists.
Compiles 280k and 60k Italian words with vowel patterns and length indexing.
"""

import os
import sys

# Add project root to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database.connection import DatabaseManager
from core.database.models import Word, Base

VOWELS = set("AEIOUÀÈÉÌÒÙ")


def get_vowel_pattern(word: str) -> str:
    """Convert word to C/V pattern. e.g. ROMA -> CVCV"""
    res = []
    for char in word.upper():
        if char in VOWELS:
            res.append('V')
        elif char.isalpha():
            res.append('C')
    return "".join(res)


def build_database() -> None:
    db_mgr = DatabaseManager()
    session = db_mgr.get_core_session()

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    dict_dir = os.path.join(base_dir, "data", "dictionaries")

    file_280k = os.path.join(dict_dir, "italian_words_280k.txt")
    file_60k = os.path.join(dict_dir, "italian_words.txt")

    common_words = set()
    if os.path.exists(file_60k):
        with open(file_60k, encoding="utf-8", errors="ignore") as f:
            for line in f:
                w = line.strip().lower()
                if w and w.isalpha():
                    common_words.add(w)

    words_to_insert = []
    seen = set()

    if os.path.exists(file_280k):
        with open(file_280k, encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
    else:
        lines = list(common_words)

    print(f"Processing {len(lines)} words...")

    for idx, line in enumerate(lines):
        w = line.strip().lower()
        if not w or not w.isalpha() or w in seen:
            continue
        seen.add(w)

        term_upper = w.upper()
        rarity = 1 if w in common_words else 3
        v_pat = get_vowel_pattern(term_upper)

        words_to_insert.append({
            "term": term_upper,
            "length": len(term_upper),
            "vowel_pattern": v_pat,
            "rarity": rarity,
            "category": "Sostantivo",
            "is_flexed": False,
            "is_proper_name": False,
            "is_excluded": False
        })

        if len(words_to_insert) >= 10000:
            session.bulk_insert_mappings(Word, words_to_insert)
            session.commit()
            print(f"Inserted {idx + 1} words...")
            words_to_insert.clear()

    if words_to_insert:
        session.bulk_insert_mappings(Word, words_to_insert)
        session.commit()
        print("Final batch committed.")

    session.close()
    print("Database build completed successfully!")


if __name__ == "__main__":
    build_database()
