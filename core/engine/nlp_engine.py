"""
NLP Engine Module for AREPO.
Supports spaCy syntagm extraction, random sampling, file quotas, and Rebus quality scoring.
"""

import os
import re
import bisect
import random
import math
from dataclasses import dataclass
from typing import List, Dict, Any, Callable, Optional, Set, Tuple
import spacy
from spacy.tokens import Span, Token

from core.config import (
    SENSORY_CHROMATIC_WORDS,
    SPATIAL_EVOCATIVE_WORDS,
    GENERIC_PENALIZED_WORDS,
    get_default_parameters
)


@dataclass(frozen=True)
class SyntagmResult:
    """Immutable Data Transfer Object for extracted syntagms."""
    syntagm: str
    words_count: int
    letters_count: int
    in_sweet_spot: bool
    score: float
    source: str
    line_num: int
    context: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "Sintagma": self.syntagm,
            "Parole": self.words_count,
            "Lettere": self.letters_count,
            "In Sweet Spot": "Sì" if self.in_sweet_spot else "No",
            "Score": self.score,
            "Opera / Fonte": self.source,
            "Riga": self.line_num,
            "Contesto": self.context
        }


class NLPEngine:
    """Core Model class performing spaCy parsing and syntagm extraction."""

    def __init__(self, model_name: str = "it_core_news_sm"):
        self.model_name = model_name
        self.nlp = None
        self.is_loaded = False
        self._load_model()

    def _load_model(self) -> None:
        try:
            self.nlp = spacy.load(self.model_name, disable=["ner", "textcat"])
            self.is_loaded = True
        except OSError:
            self.is_loaded = False
            raise RuntimeError(
                f"Modello spaCy '{self.model_name}' non trovato.\n"
                f"Esegui: python -m spacy download {self.model_name}"
            )

    @staticmethod
    def count_clean_letters(text: str) -> int:
        return sum(1 for char in text if char.isalpha())

    def calculate_rebus_score(
        self,
        tokens: List[Token],
        letters_count: int,
        sweet_spot_min: int,
        sweet_spot_max: int
    ) -> float:
        score: float = 5.0
        sensory_matches: int = 0
        spatial_matches: int = 0
        generic_matches: int = 0
        has_noun: bool = False
        has_adj: bool = False

        for token in tokens:
            pos = token.pos_
            if pos in ("NOUN", "PROPN"):
                has_noun = True
            elif pos == "ADJ":
                has_adj = True

            word_lower = token.text.lower()
            lemma_lower = token.lemma_.lower()

            if word_lower in SENSORY_CHROMATIC_WORDS or lemma_lower in SENSORY_CHROMATIC_WORDS:
                sensory_matches += 1
            if word_lower in SPATIAL_EVOCATIVE_WORDS or lemma_lower in SPATIAL_EVOCATIVE_WORDS:
                spatial_matches += 1
            if word_lower in GENERIC_PENALIZED_WORDS or lemma_lower in GENERIC_PENALIZED_WORDS:
                generic_matches += 1

        score += min(sensory_matches * 1.5, 3.0)
        score += min(spatial_matches * 1.5, 3.0)
        
        if has_noun and has_adj:
            score += 0.8

        if sweet_spot_min <= letters_count <= sweet_spot_max:
            score += 1.5

        score -= generic_matches * 1.8
        return round(max(1.0, min(10.0, score)), 1)

    def is_valid_nominal_syntagm(self, span: Span, strict_verb_filter: bool = True) -> bool:
        tokens = [t for t in span if not t.is_space and not t.is_punct]
        if not tokens:
            return False

        has_noun = False
        for token in tokens:
            pos = token.pos_
            if strict_verb_filter and pos in ("VERB", "AUX"):
                return False
            if pos in ("NOUN", "PROPN"):
                has_noun = True

        if not has_noun:
            return False

        if tokens[0].pos_ in ("ADP", "CCONJ", "SCONJ"):
            return False
        if tokens[-1].pos_ in ("ADP", "CCONJ", "SCONJ", "DET"):
            return False

        return True

    def extract_candidates_from_sentence(
        self,
        sent: Span,
        params: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        defaults = get_default_parameters()
        min_w = params.get("min_words", defaults["min_words"])
        max_w = params.get("max_words", defaults["max_words"])
        min_l = params.get("min_letters", defaults["min_letters"])
        max_l = params.get("max_letters", defaults["max_letters"])
        sweet_min = params.get("sweet_spot_min", defaults["sweet_spot_min"])
        sweet_max = params.get("sweet_spot_max", defaults["sweet_spot_max"])
        strict_verb = params.get("strict_verb_filter", defaults["strict_verb_filter"])
        min_score = params.get("min_score", defaults["min_score"])

        candidate_spans: List[Span] = []

        try:
            for chunk in sent.noun_chunks:
                candidate_spans.append(chunk)
        except NotImplementedError:
            pass

        for token in sent:
            if token.pos_ in ("NOUN", "PROPN"):
                sub_tokens = [token]
                for child in token.children:
                    if child.dep_ in ("amod", "nmod", "det", "nummod", "compound", "case"):
                        sub_tokens.append(child)

                if len(sub_tokens) > 1:
                    sub_tokens.sort(key=lambda t: t.i)
                    start_i = sub_tokens[0].i
                    end_i = sub_tokens[-1].i + 1
                    if start_i >= sent.start and end_i <= sent.end:
                        candidate_spans.append(sent.doc[start_i:end_i])

        results: List[Dict[str, Any]] = []
        seen_texts: Set[str] = set()

        for span in candidate_spans:
            text = re.sub(r'\s+', ' ', span.text.strip())
            if text in seen_texts:
                continue

            words = [t for t in span if t.is_alpha]
            w_count = len(words)
            if not (min_w <= w_count <= max_w):
                continue

            l_count = self.count_clean_letters(text)
            if not (min_l <= l_count <= max_l):
                continue

            if not self.is_valid_nominal_syntagm(span, strict_verb_filter=strict_verb):
                continue

            score = self.calculate_rebus_score(words, l_count, sweet_min, sweet_max)
            if score < min_score:
                continue

            seen_texts.add(text)
            results.append({
                "syntagm": text,
                "words_count": w_count,
                "letters_count": l_count,
                "in_sweet_spot": (sweet_min <= l_count <= sweet_max),
                "score": score
            })

        return results

    def process_file(
        self,
        filepath: str,
        params: Dict[str, Any],
        log_callback: Optional[Callable[[str], None]] = None,
        progress_callback: Optional[Callable[[float, str], None]] = None,
        file_idx: int = 1,
        total_files: int = 1,
        is_cancelled: Optional[Callable[[], bool]] = None,
        current_total_count: int = 0,
        file_max_limit: int = 0
    ) -> List[SyntagmResult]:
        filename = os.path.basename(filepath)
        results: List[SyntagmResult] = []
        overall_max = params.get("max_results", 50)
        random_sample = params.get("random_sample", True)

        if log_callback:
            log_callback(f"Scansione in corso: {filename}...")

        try:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
        except Exception as e:
            if log_callback:
                log_callback(f"ERRORE di lettura {filename}: {str(e)}")
            return []

        if not lines:
            return []

        line_start_offsets: List[int] = []
        curr_offset = 0
        for line in lines:
            line_start_offsets.append(curr_offset)
            curr_offset += len(line)

        def get_line_number(char_offset: int) -> int:
            idx = bisect.bisect_right(line_start_offsets, char_offset)
            return max(1, idx)

        CHUNK_SIZE = 60
        chunks: List[Tuple[str, int]] = []
        for i in range(0, len(lines), CHUNK_SIZE):
            chunk_lines = lines[i:i + CHUNK_SIZE]
            chunk_text = "".join(chunk_lines)
            chunk_start_char = line_start_offsets[i]
            chunks.append((chunk_text, chunk_start_char))

        if random_sample and len(chunks) > 1:
            random.seed(None)
            random.shuffle(chunks)

        total_chunks = len(chunks)
        chunk_texts = [c[0] for c in chunks]

        processed_chunks = 0
        for (chunk_text, chunk_start_char), doc in zip(chunks, self.nlp.pipe(chunk_texts, batch_size=32)):
            if is_cancelled and is_cancelled():
                break

            if overall_max > 0 and (current_total_count + len(results)) >= overall_max:
                if log_callback:
                    log_callback(f"Raggiunto il limite totale di {overall_max} sintagmi.")
                break

            if file_max_limit > 0 and len(results) >= file_max_limit:
                if log_callback:
                    log_callback(f"Raggiunta la quota per {filename}.")
                break

            processed_chunks += 1
            if progress_callback and total_chunks > 0:
                file_pct = (processed_chunks / total_chunks)
                overall_pct = ((file_idx - 1) + file_pct) / total_files
                progress_callback(overall_pct, f"Analisi {filename} ({int(file_pct * 100)}%) - File {file_idx}/{total_files}")

            for sent in doc.sents:
                if overall_max > 0 and (current_total_count + len(results)) >= overall_max:
                    break
                if file_max_limit > 0 and len(results) >= file_max_limit:
                    break

                candidates = self.extract_candidates_from_sentence(sent, params)
                if candidates:
                    sent_text = re.sub(r'\s+', ' ', sent.text.strip())
                    actual_char_offset = chunk_start_char + sent.start_char
                    line_no = get_line_number(actual_char_offset)

                    for cand in candidates:
                        results.append(SyntagmResult(
                            syntagm=cand["syntagm"],
                            words_count=cand["words_count"],
                            letters_count=cand["letters_count"],
                            in_sweet_spot=cand["in_sweet_spot"],
                            score=cand["score"],
                            source=filename,
                            line_num=line_no,
                            context=sent_text
                        ))
                        if overall_max > 0 and (current_total_count + len(results)) >= overall_max:
                            break
                        if file_max_limit > 0 and len(results) >= file_max_limit:
                            break

        if log_callback:
            log_callback(f"Completato {filename}: trovati {len(results)} sintagmi validi.")

        return results

    def process_directory(
        self,
        dir_path: str,
        params: Dict[str, Any],
        progress_callback: Optional[Callable[[float, str], None]] = None,
        log_callback: Optional[Callable[[str], None]] = None,
        is_cancelled: Optional[Callable[[], bool]] = None
    ) -> List[SyntagmResult]:
        if not os.path.exists(dir_path):
            if log_callback:
                log_callback(f"ERRORE: Cartella non trovata ({dir_path})")
            return []

        txt_files = [
            os.path.join(dir_path, f) for f in os.listdir(dir_path)
            if f.lower().endswith(".txt")
        ]

        if not txt_files:
            if log_callback:
                log_callback(f"Nessun file .txt trovato nella cartella {dir_path}")
            return []

        random_sample = params.get("random_sample", True)
        if random_sample and len(txt_files) > 1:
            random.seed(None)
            random.shuffle(txt_files)

        total_files = len(txt_files)
        all_results: List[SyntagmResult] = []
        overall_max = params.get("max_results", 50)

        for idx, filepath in enumerate(txt_files, 1):
            if is_cancelled and is_cancelled():
                if log_callback:
                    log_callback("Analisi interrotta dall'utente.")
                break

            if overall_max > 0 and len(all_results) >= overall_max:
                break

            remaining_needed = overall_max - len(all_results) if overall_max > 0 else 0
            remaining_files = (total_files - idx + 1)
            file_quota = math.ceil(remaining_needed / remaining_files) if overall_max > 0 else 0

            file_results = self.process_file(
                filepath,
                params,
                log_callback=log_callback,
                progress_callback=progress_callback,
                file_idx=idx,
                total_files=total_files,
                is_cancelled=is_cancelled,
                current_total_count=len(all_results),
                file_max_limit=file_quota
            )
            all_results.extend(file_results)

        if log_callback:
            log_callback(f"Scansione completata. Sintagmi estratti totali da {total_files} file: {len(all_results)}")

        return all_results
