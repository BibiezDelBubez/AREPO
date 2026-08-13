"""
Anarebus Engine Module for AREPO.
Provides bi-directional anagram generation, decomposition into visual subjects and grafemi,
letter difference analytics, and comprehensive evaluation according to the Golden Rules of Enigmatics.
"""

import os
import re
import collections
from dataclasses import dataclass
from typing import List, Tuple, Dict, Set, Optional, Any
import spacy

COMMON_REBUS_SUBJECTS: Set[str] = {
    "dito", "carota", "ramo", "vaso", "pane", "sole", "cane", "gatto", "topo", "nido", "rosa",
    "fune", "remo", "vela", "pino", "vino", "osso", "palla", "tazza", "disco", "perla", "drago",
    "elmo", "gufo", "lupo", "mela", "noce", "nave", "perno", "rete", "scala", "teschio", "uovo",
    "zappa", "albero", "ancora", "borsa", "bosco", "capra", "carta", "cassa", "citta", "fumo",
    "gesso", "isola", "lancia", "leone", "libro", "luna", "muro", "notte", "onda", "palazzo",
    "ponte", "porta", "quadro", "rana", "sedia", "spada", "stella", "storia", "punto", "treno",
    "valle", "zampa", "pentola", "cipolla", "coltello", "finestra", "tavolo", "ruota", "scorta",
    "auto", "bici", "torta", "arco", "dardo", "re", "dadi", "muto", "sarto", "tuta", "velo",
    "baffi", "tana", "tenda", "secchio", "specchio"
}

FUNCTIONAL_WORDS: Set[str] = {
    "di", "da", "in", "con", "su", "per", "tra", "fra",
    "il", "lo", "la", "i", "gli", "le", "un", "uno", "una",
    "ed", "ad", "se", "ma", "che", "non", "del", "della", "dello", "dei", "degli", "delle",
    "al", "alla", "allo", "ai", "agli", "alle", "dal", "dalla", "dallo", "dai", "dagli", "dalle",
    "nel", "nella", "nello", "nei", "negli", "nelle", "sul", "sulla", "sullo", "sui", "sugli", "sulle"
}


@dataclass
class AnarebusEvaluation:
    """Data object containing complete quality assessment of an Anarebus pair."""
    keys_text: str
    solution_text: str
    total_letters: int
    is_perfect_anagram: bool
    missing_letters: Dict[str, int]
    surplus_letters: Dict[str, int]
    
    # Golden Rules Metrics
    length_category: str
    length_status_badge: str
    keys_word_count: int
    keys_word_status: str
    sol_word_count: int
    sol_word_status: str
    
    # Root Defect / Shuffling
    rimescolamento_rating: str
    max_contiguous_kept: int
    root_defects: List[Tuple[str, str, str, int]]
    
    # Visual Innocence & Grammar
    innocence_score: float
    innocence_feedback: str
    grammar_score: float
    grammar_feedback: str
    
    overall_quality_score: float


class AnarebusEngine:
    """Core computational model for Anarebus generation, evaluation, and scomposizione."""

    def __init__(self, spacy_model: str = "it_core_news_sm"):
        self.nlp = None
        self._load_spacy(spacy_model)
        
        self.all_words: Set[str] = set()
        self.common_words: Set[str] = set()
        self.canon_map: Dict[str, List[str]] = collections.defaultdict(list)
        self._load_dictionaries()

    def _load_spacy(self, model_name: str) -> None:
        try:
            self.nlp = spacy.load(model_name, disable=["ner", "textcat"])
        except Exception:
            self.nlp = None

    def _load_dictionaries(self) -> None:
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        dict_dir = os.path.join(base_dir, "data", "dictionaries")
        
        files = [
            os.path.join(dict_dir, "italian_words_280k.txt"),
            os.path.join(dict_dir, "italian_words.txt")
        ]
        
        loaded = False
        for fpath in files:
            if os.path.exists(fpath):
                with open(fpath, encoding="utf-8", errors="ignore") as f:
                    for line in f:
                        w = line.strip().lower()
                        if 1 <= len(w) <= 18 and w.isalpha():
                            self.all_words.add(w)
                            if "italian_words.txt" in fpath:
                                self.common_words.add(w)
                loaded = True
                
        if not loaded:
            self.all_words = set(COMMON_REBUS_SUBJECTS).union(FUNCTIONAL_WORDS)
            self.common_words = set(COMMON_REBUS_SUBJECTS)

        self.all_words.update(FUNCTIONAL_WORDS)
        self.common_words.update(COMMON_REBUS_SUBJECTS)
        self.common_words.update(FUNCTIONAL_WORDS)

        for w in self.all_words:
            k = ''.join(sorted(w.upper()))
            if w.upper() not in self.canon_map[k]:
                self.canon_map[k].append(w.upper())

    @staticmethod
    def clean_text(text: str) -> str:
        return re.sub(r'[^a-zA-Z]', '', text).upper()

    @staticmethod
    def get_letter_counts(text: str) -> collections.Counter:
        return collections.Counter(AnarebusEngine.clean_text(text))

    def evaluate_anarebus(self, keys_text: str, solution_text: str) -> AnarebusEvaluation:
        clean_keys = self.clean_text(keys_text)
        clean_sol = self.clean_text(solution_text)
        
        cnt_keys = collections.Counter(clean_keys)
        cnt_sol = collections.Counter(clean_sol)
        
        is_perfect = (cnt_keys == cnt_sol)
        missing = dict(cnt_sol - cnt_keys)
        surplus = dict(cnt_keys - cnt_sol)
        
        total_letters = len(clean_keys) if is_perfect else max(len(clean_keys), len(clean_sol))
        
        if total_letters < 6:
            length_cat = "Troppo corto (< 6)"
            length_badge = "❌ TROPPO CORTO (< 6 lettere)"
        elif 6 <= total_letters <= 7:
            length_cat = "Sconsigliato / Banale (6-7)"
            length_badge = "⚠️ TROPPO FACILE (6-7 lettere)"
        elif total_letters == 8:
            length_cat = "Valido (8)"
            length_badge = "🟢 VALIDO (8 lettere)"
        elif 9 <= total_letters <= 13:
            length_cat = "Zona Aurea (9-13)"
            length_badge = "🏆 ZONA AUREA (9-13 lettere - NUMERO PERFETTO)"
        elif 14 <= total_letters <= 18:
            length_cat = "Valido Lungo (14-18)"
            length_badge = "🟢 VALIDO LUNGO (14-18 lettere)"
        else:
            length_cat = "Troppo lungo (> 18)"
            length_badge = "❌ TROPPO LUNGO (> 18 lettere - IMPOSSIBILE A MENTE)"
            
        keys_words = [w for w in keys_text.strip().split() if w.strip()]
        sol_words = [w for w in solution_text.strip().split() if w.strip()]
        
        k_count = len(keys_words)
        if k_count == 3:
            k_status = "🏆 Perfetto (3 elementi)"
        elif 2 <= k_count <= 4:
            k_status = f"🟢 Valido ({k_count} elementi)"
        else:
            k_status = f"⚠️ Fuori norma ({k_count} elementi)"
            
        s_count = len(sol_words)
        if 2 <= s_count <= 3:
            s_status = f"🏆 Perfetto ({s_count} parole)"
        elif 1 <= s_count <= 4:
            s_status = f"🟢 Valido ({s_count} parole)"
        else:
            s_status = f"⚠️ Fuori norma ({s_count} parole)"
            
        defects, max_kept = self._check_root_defects(keys_text, solution_text)
        if max_kept <= 2:
            rim_rating = "🌟 Eccellente (Rimescolamento Totale)"
            rim_score_val = 10.0
        elif max_kept == 3:
            rim_rating = "🟢 Buono (Piccole sottostringhe conservate)"
            rim_score_val = 8.0
        elif max_kept == 4:
            rim_rating = "⚠️ Sufficiente (Sottostringa di 4 lettere conservata)"
            rim_score_val = 5.5
        else:
            rim_rating = "❌ Difetto di Radice (Parola quasi inalterata nella soluzione!)"
            rim_score_val = 2.0
            
        innocence_score, innocence_feedback = self._evaluate_innocence(keys_words)
        grammar_score, grammar_feedback = self._evaluate_grammar(solution_text)
        
        base_score = 5.0
        if is_perfect: base_score += 2.0
        else: base_score -= 3.0
        
        if 9 <= total_letters <= 13: base_score += 1.5
        elif 8 <= total_letters <= 18: base_score += 0.8
        
        base_score += (rim_score_val - 5.0) * 0.25
        base_score += (innocence_score - 5.0) * 0.15
        base_score += (grammar_score - 5.0) * 0.15
        
        overall = round(max(1.0, min(10.0, base_score)), 1)
        
        return AnarebusEvaluation(
            keys_text=keys_text,
            solution_text=solution_text,
            total_letters=total_letters,
            is_perfect_anagram=is_perfect,
            missing_letters=missing,
            surplus_letters=surplus,
            length_category=length_cat,
            length_status_badge=length_badge,
            keys_word_count=k_count,
            keys_word_status=k_status,
            sol_word_count=s_count,
            sol_word_status=s_status,
            rimescolamento_rating=rim_rating,
            max_contiguous_kept=max_kept,
            root_defects=defects,
            innocence_score=innocence_score,
            innocence_feedback=innocence_feedback,
            grammar_score=grammar_score,
            grammar_feedback=grammar_feedback,
            overall_quality_score=overall
        )

    def _check_root_defects(self, keys_text: str, sol_text: str) -> Tuple[List[Tuple[str, str, str, int]], int]:
        k_words = [self.clean_text(w) for w in keys_text.split() if len(self.clean_text(w)) >= 3]
        s_words = [self.clean_text(w) for w in sol_text.split() if len(self.clean_text(w)) >= 3]
        
        defects = []
        max_kept = 0
        
        for kw in k_words:
            for sw in s_words:
                m, n = len(kw), len(sw)
                lcs_len = 0
                best_sub = ""
                for i in range(m):
                    for j in range(n):
                        k = 0
                        while i + k < m and j + k < n and kw[i+k] == sw[j+k]:
                            k += 1
                        if k > lcs_len:
                            lcs_len = k
                            best_sub = kw[i:i+k]
                if lcs_len >= 3:
                    defects.append((kw, sw, best_sub, lcs_len))
                    if lcs_len > max_kept:
                        max_kept = lcs_len
                        
        return defects, max_kept

    def _evaluate_innocence(self, keys_words: List[str]) -> Tuple[float, str]:
        if not keys_words:
            return 5.0, "Nessuna chiave fornita."
            
        known_count = 0
        unknown = []
        
        for w in keys_words:
            clean_w = self.clean_text(w).lower()
            if len(clean_w) <= 2:
                continue
            elif clean_w in COMMON_REBUS_SUBJECTS or clean_w in self.common_words:
                known_count += 1
            else:
                unknown.append(w)
                
        if not unknown:
            return 9.5, "Tutti i soggetti sono chiari, naturali e facilmente disegnabili."
        elif len(unknown) == 1:
            return 7.0, f"Soggetto potenzialmente complesso: '{unknown[0]}'."
        else:
            return 4.0, f"Soggetti insoliti: {', '.join(unknown)}."

    def _evaluate_grammar(self, sol_text: str) -> Tuple[float, str]:
        if not sol_text.strip():
            return 5.0, "Soluzione vuota."
            
        if self.nlp is None:
            words = sol_text.lower().split()
            valid = sum(1 for w in words if w in self.all_words)
            pct = valid / max(1, len(words))
            score = round(3.0 + pct * 6.0, 1)
            return score, f"Analisi dizionario: {valid}/{len(words)} parole riconosciute."
            
        doc = self.nlp(sol_text.lower())
        has_noun = any(t.pos_ in ("NOUN", "PROPN") for t in doc)
        has_verb = any(t.pos_ in ("VERB", "AUX") for t in doc)
        
        score = 6.0
        details = []
        
        if has_noun:
            score += 2.0
            details.append("Contiene sostantivo")
        if has_verb:
            score += 1.5
            details.append("Contiene verbo")
            
        if doc[0].pos_ in ("ADP", "CCONJ"):
            score -= 1.0
            details.append("Inizia con congiunzione/preposizione")
            
        final_score = round(max(1.0, min(10.0, score)), 1)
        feedback = "Frase fluida (" + ", ".join(details) + ")"
        return final_score, feedback

    def decompose_solution(self, solution_text: str, max_results: int = 30) -> List[Dict[str, Any]]:
        clean_sol = self.clean_text(solution_text)
        sol_cnt = collections.Counter(clean_sol)
        
        if not clean_sol:
            return []

        valid_subjects = []
        for w in self.common_words:
            if 3 <= len(w) <= 12 and w.isalpha():
                w_cnt = collections.Counter(w.upper())
                if self._is_submultiset(w_cnt, sol_cnt):
                    is_rebus_common = w.lower() in COMMON_REBUS_SUBJECTS
                    valid_subjects.append((w.upper(), w_cnt, is_rebus_common))
                    
        valid_subjects.sort(key=lambda x: (not x[2], -len(x[0]), x[0]))
        
        results = []
        for i in range(len(valid_subjects)):
            s1, c1, is_c1 = valid_subjects[i]
            rem1 = sol_cnt - c1
            
            for j in range(i, len(valid_subjects)):
                s2, c2, is_c2 = valid_subjects[j]
                if self._is_submultiset(c2, rem1):
                    rem2 = rem1 - c2
                    rem_letters = []
                    for char, count in sorted(rem2.items()):
                        rem_letters.extend([char] * count)
                        
                    grafemi = self._format_grafemi(rem_letters)
                    if grafemi is not None:
                        keys_str = " ".join(grafemi + [s1, s2])
                        eval_res = self.evaluate_anarebus(keys_str, solution_text)
                        
                        results.append({
                            "keys_text": keys_str,
                            "solution_text": solution_text,
                            "subjects": [s1, s2],
                            "grafemi": grafemi,
                            "total_letters": eval_res.total_letters,
                            "rimescolamento": eval_res.rimescolamento_rating,
                            "innocence": eval_res.innocence_feedback,
                            "score": eval_res.overall_quality_score
                        })
                        if len(results) >= max_results:
                            break
                            
        results.sort(key=lambda x: -x["score"])
        return results[:max_results]

    def solve_from_keys(
        self,
        keys_text: str,
        extra_letters_allowed: int = 0,
        max_results: int = 100,
        max_words: int = 4,
        deep_search: bool = True
    ) -> List[Dict[str, Any]]:
        clean_keys = self.clean_text(keys_text)
        if not clean_keys:
            return []
            
        target_cnt = collections.Counter(clean_keys)
        total_len = sum(target_cnt.values())
        
        valid_canon_keys = []
        for k, words in self.canon_map.items():
            k_cnt = collections.Counter(k)
            extra_needed = sum((k_cnt - target_cnt).values())
            if len(k) <= total_len + extra_letters_allowed and extra_needed <= extra_letters_allowed:
                valid_canon_keys.append((k, k_cnt, len(k), extra_needed))
                    
        valid_canon_keys.sort(key=lambda x: -x[2])
        
        found_combos = []
        combo_cap = max(3000, max_results * 30) if deep_search else max(500, max_results * 5)
        
        def dfs(current_cnt: collections.Counter, path: List[str], current_extra: int, start_idx: int):
            rem_len = sum(current_cnt.values())
            if rem_len == 0:
                found_combos.append((list(path), current_extra))
                return
            if len(path) >= max_words:
                return
                
            for i in range(start_idx, len(valid_canon_keys)):
                k, k_cnt, k_len, extra_req = valid_canon_keys[i]
                if extra_req + current_extra > extra_letters_allowed:
                    continue
                diff = k_cnt - current_cnt
                added_extra = sum(diff.values())
                if current_extra + added_extra <= extra_letters_allowed:
                    next_cnt = current_cnt - k_cnt
                    dfs(next_cnt, path + [k], current_extra + added_extra, i)
                    if len(found_combos) >= combo_cap:
                        return

        dfs(target_cnt, [], 0, 0)
        
        import itertools
        results = []
        seen = set()
        words_variant_limit = 10 if deep_search else 4
        
        for canon_seq, extra_used in found_combos:
            word_lists = [self.canon_map[k] for k in canon_seq]
            trimmed_lists = [wlist[:words_variant_limit] for wlist in word_lists]
            
            for word_tuple in itertools.product(*trimmed_lists):
                for perm in itertools.permutations(word_tuple):
                    sol_candidate = " ".join(perm)
                    if sol_candidate in seen:
                        continue
                    seen.add(sol_candidate)
                    
                    eval_res = self.evaluate_anarebus(keys_text, sol_candidate)
                    results.append({
                        "keys_text": keys_text,
                        "solution_text": sol_candidate,
                        "total_letters": eval_res.total_letters,
                        "extra_letters": extra_used,
                        "rimescolamento": eval_res.rimescolamento_rating,
                        "score": eval_res.overall_quality_score,
                        "badge": eval_res.length_status_badge
                    })
                    if len(results) >= max_results * 5:
                        break
                if len(results) >= max_results * 5:
                    break
                    
        results.sort(key=lambda x: -x["score"])
        return results[:max_results]

    @staticmethod
    def _is_submultiset(sub: collections.Counter, parent: collections.Counter) -> bool:
        for k, v in sub.items():
            if parent[k] < v:
                return False
        return True

    @staticmethod
    def _format_grafemi(rem_letters: List[str]) -> Optional[List[str]]:
        if not rem_letters:
            return []
        s = "".join(rem_letters)
        if len(s) == 1:
            return [s]
        if len(s) == 2:
            return [s]
        if len(s) == 3:
            return [s[0], s[1:]]
        if len(s) <= 4:
            return [s[:2], s[2:]]
        return None
