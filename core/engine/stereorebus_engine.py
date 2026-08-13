"""
Stereorebus Engine Module for AREPO.
Computational engine for Stereoscopic Rebus (Stereorebus):
- Top-Down Generator (from Solution to First Reading with 3rd-person Past/Future verbs + visual subjects)
- Bottom-Up Differential Analyzer (from Vignette A / Vignette B state changes to candidate solution phrases)
- Scoring system according to classic enigmatic rules (12-30 letters, temporal verb coherence, visual clarity).
"""

import re
import collections
from dataclasses import dataclass
from typing import List, Dict, Set, Tuple, Optional, Any
import spacy

from core.engine.anarebus_engine import COMMON_REBUS_SUBJECTS, FUNCTIONAL_WORDS, AnarebusEngine

# Lexicon of Italian 3rd-person Past/Future Verbs and Past Participles
PAST_FUTURE_VERBS_3RD: Set[str] = {
    # Passato Remoto 3a pers. singolare
    "cadde", "marciò", "sparì", "crollo", "volò", "bruciò", "recise", "svuotò", "aperse", "chiuse",
    "spense", "accese", "ruppe", "perse", "vinse", "morì", "nacque", "parlò", "entrò", "uscì",
    "salì", "scese", "corse", "cadde", "tacque", "giunse", "partì", "scrisse", "lesse", "prese",
    # Passato Remoto 3a pers. plurale
    "caddero", "marciarono", "sparirono", "crollarono", "volarono", "bruciarono", "recisero", "svuotarono",
    "apersero", "chiusero", "spensero", "accesero", "ruppero", "persero", "vinsero", "morirono", "nacquero",
    "entranti", "uscirono", "salirono", "scesero", "corsero", "tacquero", "giunsero", "partirono",
    # Imperfetto 3a pers. singolare / plurale
    "cadeva", "bruciava", "volava", "luceva", "splendeva", "correva", "fuggiva", "pendeva",
    "cadevano", "bruciavano", "volavano", "lucevano", "splendevano", "correvano", "fuggivano", "pendevano",
    # Participio Passato / Passato Prossimo (Stato B)
    "rotto", "rotta", "rotti", "rotte", "tagliato", "tagliata", "tagliati", "tagliate",
    "bruciato", "bruciata", "bruciati", "bruciate", "svuotato", "svuotata", "svuotati", "svuotate",
    "aperto", "aperta", "aperti", "aperte", "chiuso", "chiusa", "chiusi", "chiuse",
    "spento", "spenta", "spenti", "spente", "acceso", "accesa", "accesi", "accese",
    "reciso", "recisa", "recisi", "recise", "caduto", "caduta", "caduti", "cadute",
    "sparito", "sparita", "spariti", "sparite", "scoppiato", "scoppiata", "scoppiati", "scoppiate",
    "piegato", "piegata", "piegati", "piegate", "bagnato", "bagnata", "bagnati", "bagnate",
    # Futuro Semplice 3a pers. singolare / plurale
    "marcirà", "cadrà", "volerà", "romperà", "sparirà", "brucerà", "crollerà", "svuoterà",
    "marciranno", "cadranno", "voleranno", "romperanno", "spariranno", "bruceranno", "crolleranno"
}


@dataclass
class StereorebusCandidate:
    """Data transfer object for a generated Stereorebus candidate."""
    keys_text: str           # Prima lettura: e.g. "PINO FU RECISO CASSA SVUOTATA"
    solution_text: str       # Seconda lettura: e.g. "UN INTENSA EMOZIONE"
    action_verb: str         # Verbo al passato/futuro: e.g. "RECISO" / "CADDE"
    subjects: List[str]      # Soggetti visivi: e.g. ["PINO", "CASSA"]
    total_letters: int
    score: float             # Quality score 0 - 100
    grammar_coherence: str   # Feedback on temporal verb coherence
    badge: str               # Status indicator


class StereorebusEngine:
    """Core computational model for Stereoscopic Rebus (Stereorebus) generation & analysis."""

    def __init__(self, spacy_model: str = "it_core_news_sm"):
        self.anarebus_engine = AnarebusEngine(spacy_model)
        self.all_verbs = set(PAST_FUTURE_VERBS_3RD)

    def generate_from_solution(self, solution_text: str, max_results: int = 30) -> List[StereorebusCandidate]:
        """
        Top-Down Generator:
        Decomposes a target solution phrase into candidate Stereorebus First Readings
        containing 3rd-person Past/Future verbs + visual subjects + graphemes.
        """
        clean_sol = AnarebusEngine.clean_text(solution_text)
        if not clean_sol:
            return []

        sol_cnt = collections.Counter(clean_sol)
        total_len = len(clean_sol)

        # 1. Find past/future verbs that are multiset sub-sets of the solution
        valid_verbs = []
        for v in self.all_verbs:
            v_upper = v.upper()
            v_cnt = collections.Counter(v_upper)
            if AnarebusEngine._is_submultiset(v_cnt, sol_cnt):
                valid_verbs.append((v_upper, v_cnt))

        # Sort verbs by length (longer verbs preferred for better naturalness)
        valid_verbs.sort(key=lambda x: -len(x[0]))

        candidates = []

        # 2. Find matching visual subjects for each valid verb
        for v_upper, v_cnt in valid_verbs[:50]:
            rem1 = sol_cnt - v_cnt

            for subj in COMMON_REBUS_SUBJECTS:
                subj_upper = subj.upper()
                s_cnt = collections.Counter(subj_upper)

                if AnarebusEngine._is_submultiset(s_cnt, rem1):
                    rem2 = rem1 - s_cnt
                    rem_letters = []
                    for char, count in sorted(rem2.items()):
                        rem_letters.extend([char] * count)

                    grafemi = AnarebusEngine._format_grafemi(rem_letters)
                    if grafemi is not None:
                        keys_str = " ".join(grafemi + [subj_upper, v_upper])
                        
                        # Evaluate anagram quality & score
                        eval_res = self.anarebus_engine.evaluate_anarebus(keys_str, solution_text)
                        
                        # Calculate Stereorebus Quality Score (0 - 100)
                        score_100 = round(eval_res.overall_quality_score * 10, 1)
                        if 12 <= total_len <= 30:
                            score_100 += 5.0
                        score_100 = min(100.0, score_100)

                        badge = "🏆 STEREOREBUS ECCELLENTE" if score_100 >= 80 else "🟢 VALIDO"

                        candidates.append(StereorebusCandidate(
                            keys_text=keys_str,
                            solution_text=solution_text,
                            action_verb=v_upper,
                            subjects=[subj_upper],
                            total_letters=eval_res.total_letters,
                            score=score_100,
                            grammar_coherence=f"Verbo 3ª pers.: '{v_upper}'",
                            badge=badge
                        ))

                        if len(candidates) >= max_results * 2:
                            break

        candidates.sort(key=lambda x: -x.score)
        return candidates[:max_results]

    def analyze_differential_states(
        self,
        vignette_a_items: str,
        vignette_b_items: str,
        max_results: int = 30
    ) -> List[StereorebusCandidate]:
        """
        Bottom-Up Differential Analyzer:
        Given Vignette A items (e.g. "PINO, CASSA") and Vignette B state changes (e.g. "RECISO, SVUOTATA"),
        constructs First Reading phrases and searches for target solution phrases in dictionary!
        """
        items_a = [AnarebusEngine.clean_text(w) for w in vignette_a_items.split() if w.strip()]
        items_b = [AnarebusEngine.clean_text(w) for w in vignette_b_items.split() if w.strip()]

        if not items_a or not items_b:
            return []

        # Construct First Reading combined text
        keys_str = " ".join(items_a + items_b)
        
        # Solve candidates using Anarebus engine
        raw_solutions = self.anarebus_engine.solve_from_keys(keys_str, max_results=max_results)

        results = []
        for sol in raw_solutions:
            score_100 = round(sol["score"] * 10, 1)
            results.append(StereorebusCandidate(
                keys_text=keys_str,
                solution_text=sol["solution_text"],
                action_verb=", ".join(items_b),
                subjects=items_a,
                total_letters=sol["total_letters"],
                score=score_100,
                grammar_coherence="Analisi differenziale Stato A -> Stato B",
                badge=sol["badge"]
            ))

        results.sort(key=lambda x: -x.score)
        return results[:max_results]
