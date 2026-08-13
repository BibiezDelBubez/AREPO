"""
Syllabification and Prosody Engine for AREPO (Giochi in Versi).
Handles Italian syllabification rules, sinalefe (vowel elision across word boundaries),
dieresi (<dieresi>word</dieresi>), and verse metric count (e.g. Endecasillabo = 11 metric syllables).
"""

import re
from typing import List, Tuple, Dict, Any

VOWELS = set("aeiouàèéìòùAEIOUÀÈÉÌÒÙ")
STRONG_VOWELS = set("aeoàèéòAEÒÈÉ")
WEAK_VOWELS = set("iuìùIUÌÙ")


class Syllabifier:
    """Computes phonological and metric syllables for Italian text lines."""

    @staticmethod
    def syllabify_word(word: str) -> List[str]:
        """
        Split an isolated Italian word into grammatical syllables using regex heuristics.
        """
        w = word.strip()
        if not w:
            return []

        # Remove dieresi tags if present
        clean_w = re.sub(r'</?dieresi>', '', w)

        # Regex heuristic matching Italian syllable patterns
        # Syllables centered around vowel nuclei
        pattern = r'(?i)(?:[bcdfghlmnpqrstvwxz]*[aeiouàèéìòù]+(?:[iu]|(?=[bcdfghlmnpqrstvwxz]{2,}))?|[bcdfghlmnpqrstvwxz]+)'
        matches = re.findall(pattern, clean_w)
        
        if not matches:
            return [clean_w]

        # Re-combine lone consonant clusters with preceding syllable
        syllables = []
        for m in matches:
            if not any(c in VOWELS for c in m) and syllables:
                syllables[-1] += m
            else:
                syllables.append(m)

        return syllables if syllables else [clean_w]

    @classmethod
    def count_line_metric_syllables(cls, line: str) -> Tuple[int, List[str], List[Dict[str, Any]]]:
        """
        Compute metric syllables for a line of poetry considering Sinalefe across words.

        :param line: Text of the line (may contain <dieresi> tags)
        :return: Tuple (total_metric_syllables, list_of_all_grammatical_syllables, list_of_word_details)
        """
        # Parse for <dieresi> tags
        words = line.strip().split()
        if not words:
            return 0, [], []

        all_syllables: List[str] = []
        word_details = []

        for w in words:
            has_dieresi = "<dieresi>" in w or "</dieresi>" in w
            clean = re.sub(r'</?dieresi>', '', w)
            clean_alpha = re.sub(r'[^a-zA-ZàèéìòùÀÈÉÌÒÙ]', '', clean)
            
            syls = cls.syllabify_word(clean_alpha)
            if has_dieresi and len(syls) == 1 and len(clean_alpha) >= 3:
                # Force dieresi split into 2 syllables
                mid = len(clean_alpha) // 2
                syls = [clean_alpha[:mid], clean_alpha[mid:]]

            all_syllables.extend(syls)
            word_details.append({
                "word": clean_alpha,
                "syllables": syls,
                "has_dieresi": has_dieresi
            })

        # Calculate metric count with Sinalefe
        # Sinalefe: when word ends with vowel and next word starts with vowel, 1 metric syllable is saved
        sinalefe_count = 0
        for i in range(len(word_details) - 1):
            w1 = word_details[i]["word"]
            w2 = word_details[i + 1]["word"]
            if w1 and w2:
                last_char = w1[-1].lower()
                first_char = w2[0].lower()
                if last_char in VOWELS and first_char in VOWELS:
                    sinalefe_count += 1

        total_grammatical = len(all_syllables)
        total_metric = max(1, total_grammatical - sinalefe_count)

        return total_metric, all_syllables, word_details

    @classmethod
    def get_meter_name(cls, metric_count: int) -> str:
        """Return traditional Italian poetic meter name based on syllable count."""
        meters = {
            3: "Ternario",
            4: "Quenario",
            5: "Quinario",
            6: "Senario",
            7: "Settenario",
            8: "Ottonario",
            9: "Novenario",
            10: "Decasillabo",
            11: "Endecasillabo (11)",
            12: "Dodecasillabo",
        }
        return meters.get(metric_count, f"{metric_count} Sillabe")
