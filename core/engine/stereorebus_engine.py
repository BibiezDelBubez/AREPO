"""
Stereorebus Engine Module for AREPO.
Dedicated AI & Algorithmic engine for Stereoscopic Rebus (Stereorebus / Stereorebi):
- Mode A: Top-Down Generator (From Solution phrase to First Reading with 3rd-person Past/Future verbs + visual subjects).
- Mode B: Bottom-Up Differential Analyzer (From Vignette A state & Vignette B action to First Reading & candidate Solutions).
- Mode C: Enigmatic LLM System Prompt Generator for Stereorebus.
- Scoring System (0-100 scale based on Naturalness, Visual Adherence, 3rd person Verb Coherence, and Cesura).
"""

import re
import collections
from dataclasses import dataclass, field
from typing import List, Dict, Set, Tuple, Optional, Any
import spacy

from core.engine.anarebus_engine import COMMON_REBUS_SUBJECTS, FUNCTIONAL_WORDS, AnarebusEngine


@dataclass
class VerbForm:
    """Represents a 3rd person past or future verb form."""
    form: str             # Verb text in uppercase e.g. "CADDE", "RECISO", "MARCIRÀ"
    tense: str            # "Passato Remoto (3ª pers.)", "Participio / Passato Prossimo", "Futuro (3ª pers.)", "Imperfetto"
    person: str           # "3ª pers. singolare" or "3ª pers. plurale"
    visual_action: str    # Visual action description for Scene II


# Comprehensive Enigmatic Database of Italian 3rd-person Past/Future Verbs for Stereorebus
STEREO_VERBS: List[VerbForm] = [
    # Passato Remoto (3ª pers. singolare / plurale)
    VerbForm("CADDE", "Passato Remoto (3ª pers.)", "3ª pers. singolare", "L'oggetto/soggetto è caduto a terra"),
    VerbForm("CADDERO", "Passato Remoto (3ª pers.)", "3ª pers. plurale", "Gli oggetti sono caduti a terra"),
    VerbForm("MARCIÒ", "Passato Remoto (3ª pers.)", "3ª pers. singolare", "L'elemento è deteriorato o marcito"),
    VerbForm("SPARÌ", "Passato Remoto (3ª pers.)", "3ª pers. singolare", "L'oggetto è scomparso dalla scena"),
    VerbForm("SPARIRONO", "Passato Remoto (3ª pers.)", "3ª pers. plurale", "Gli elementi sono scomparsi"),
    VerbForm("CROLLÒ", "Passato Remoto (3ª pers.)", "3ª pers. singolare", "La struttura si è abbattuta"),
    VerbForm("VOLÒ", "Passato Remoto (3ª pers.)", "3ª pers. singolare", "Il soggetto è volato via"),
    VerbForm("VOLARONO", "Passato Remoto (3ª pers.)", "3ª pers. plurale", "I soggetti sono volati via"),
    VerbForm("BRUCIÒ", "Passato Remoto (3ª pers.)", "3ª pers. singolare", "L'oggetto ha preso fuoco ed è bruciato"),
    VerbForm("BRUCIARONO", "Passato Remoto (3ª pers.)", "3ª pers. plurale", "Gli oggetti sono bruciati"),
    VerbForm("RECISE", "Passato Remoto (3ª pers.)", "3ª pers. singolare", "Qualcuno ha tagliato o reciso l'elemento"),
    VerbForm("SVUOTÒ", "Passato Remoto (3ª pers.)", "3ª pers. singolare", "Il contenitore è stato svuotato"),
    VerbForm("APERSE", "Passato Remoto (3ª pers.)", "3ª pers. singolare", "Il passaggio o l'oggetto si è aperto"),
    VerbForm("CHIUSE", "Passato Remoto (3ª pers.)", "3ª pers. singolare", "Il contenitore o porta si è chiusa"),
    VerbForm("SPENSE", "Passato Remoto (3ª pers.)", "3ª pers. singolare", "La luce o il fuoco si è spento"),
    VerbForm("ACCESE", "Passato Remoto (3ª pers.)", "3ª pers. singolare", "La luce o fiamma si è accesa"),
    VerbForm("RUPPE", "Passato Remoto (3ª pers.)", "3ª pers. singolare", "L'oggetto si è infranto in cocci"),
    VerbForm("RUPPERO", "Passato Remoto (3ª pers.)", "3ª pers. plurale", "Gli oggetti si sono infranti"),
    VerbForm("PERSE", "Passato Remoto (3ª pers.)", "3ª pers. singolare", "L'elemento è stato smarrito"),
    VerbForm("VINSE", "Passato Remoto (3ª pers.)", "3ª pers. singolare", "Il personaggio ha ottenuto la vittoria"),
    VerbForm("MORÌ", "Passato Remoto (3ª pers.)", "3ª pers. singolare", "La pianta o animale è privo di vita"),
    VerbForm("NACQUE", "Passato Remoto (3ª pers.)", "3ª pers. singolare", "È spuntato un nuovo germoglio o animale"),
    VerbForm("PARLÒ", "Passato Remoto (3ª pers.)", "3ª pers. singolare", "Il personaggio sta parlando"),
    VerbForm("ENTRÒ", "Passato Remoto (3ª pers.)", "3ª pers. singolare", "Il soggetto è entrato nella stanza"),
    VerbForm("USCÌ", "Passato Remoto (3ª pers.)", "3ª pers. singolare", "Il soggetto è uscito dall'ambiente"),
    VerbForm("SALÌ", "Passato Remoto (3ª pers.)", "3ª pers. singolare", "Il personaggio è salito in alto"),
    VerbForm("SCESE", "Passato Remoto (3ª pers.)", "3ª pers. singolare", "Il personaggio è sceso in basso"),
    VerbForm("CORSE", "Passato Remoto (3ª pers.)", "3ª pers. singolare", "Il soggetto si è mosso in corsa"),
    VerbForm("TACQUE", "Passato Remoto (3ª pers.)", "3ª pers. singolare", "Il personaggio ha smesso di parlare"),
    VerbForm("GIUNSE", "Passato Remoto (3ª pers.)", "3ª pers. singolare", "Il soggetto è arrivato alla meta"),
    VerbForm("PARTÌ", "Passato Remoto (3ª pers.)", "3ª pers. singolare", "Il veicolo o soggetto è ripartito"),
    VerbForm("SCRISSE", "Passato Remoto (3ª pers.)", "3ª pers. singolare", "Il testo è stato tracciato sulla carta"),
    VerbForm("LESSE", "Passato Remoto (3ª pers.)", "3ª pers. singolare", "Il personaggio sta consultando il foglio"),
    VerbForm("PRESE", "Passato Remoto (3ª pers.)", "3ª pers. singolare", "L'oggetto è stato afferrato"),
    VerbForm("APPARVE", "Passato Remoto (3ª pers.)", "3ª pers. singolare", "È comparso un nuovo elemento"),

    # Participio Passato / Cambio di Stato (Vignetta B)
    VerbForm("RECISO", "Participio / Passato Prossimo", "3ª pers. singolare m.", "L'albero o stelo è stato tagliato"),
    VerbForm("RECISA", "Participio / Passato Prossimo", "3ª pers. singolare f.", "La pianta o fune è stata recisa"),
    VerbForm("RECISI", "Participio / Passato Prossimo", "3ª pers. plurale m.", "Gli elementi sono stati recisi"),
    VerbForm("RECISE", "Participio / Passato Prossimo", "3ª pers. plurale f.", "Le strutture sono state recise"),
    VerbForm("TAGLIATO", "Participio / Passato Prossimo", "3ª pers. singolare m.", "L'oggetto appare segato o tagliato"),
    VerbForm("TAGLIATA", "Participio / Passato Prossimo", "3ª pers. singolare f.", "La superficie appare tagliata"),
    VerbForm("SVUOTATO", "Participio / Passato Prossimo", "3ª pers. singolare m.", "Il contenitore ora è vuoto"),
    VerbForm("SVUOTATA", "Participio / Passato Prossimo", "3ª pers. singolare f.", "La cassa o bottiglia è vuota"),
    VerbForm("ROTTO", "Participio / Passato Prossimo", "3ª pers. singolare m.", "L'oggetto è in frantumi"),
    VerbForm("ROTTA", "Participio / Passato Prossimo", "3ª pers. singolare f.", "La brocca o finestra è rotta"),
    VerbForm("ROTTI", "Participio / Passato Prossimo", "3ª pers. plurale m.", "I vasi sono rotti"),
    VerbForm("ROTTE", "Participio / Passato Prossimo", "3ª pers. plurale f.", "Le tazze sono rotte"),
    VerbForm("APERTO", "Participio / Passato Prossimo", "3ª pers. singolare m.", "Il varco o libro è aperto"),
    VerbForm("APERTA", "Participio / Passato Prossimo", "3ª pers. singolare f.", "La porta o finestra è aperta"),
    VerbForm("CHIUSO", "Participio / Passato Prossimo", "3ª pers. singolare m.", "Il lucchetto o libro è chiuso"),
    VerbForm("CHIUSA", "Participio / Passato Prossimo", "3ª pers. singolare f.", "La porta o cassa è chiusa"),
    VerbForm("SPENTO", "Participio / Passato Prossimo", "3ª pers. singolare m.", "Il fuoco o lume è spento"),
    VerbForm("SPENTA", "Participio / Passato Prossimo", "3ª pers. singolare f.", "La candela o lampada è spenta"),
    VerbForm("ACCESO", "Participio / Passato Prossimo", "3ª pers. singolare m.", "Il falò o faro è acceso"),
    VerbForm("ACCESA", "Participio / Passato Prossimo", "3ª pers. singolare f.", "La lampada è accesa"),
    VerbForm("BRUCIATO", "Participio / Passato Prossimo", "3ª pers. singolare m.", "L'oggetto appare annerito o bruciato"),
    VerbForm("BRUCIATA", "Participio / Passato Prossimo", "3ª pers. singolare f.", "La carta è carbonizzata"),
    VerbForm("CADUTO", "Participio / Passato Prossimo", "3ª pers. singolare m.", "L'oggetto è a terra"),
    VerbForm("CADUTA", "Participio / Passato Prossimo", "3ª pers. singolare f.", "La foglia o statua è a terra"),
    VerbForm("SPARITO", "Participio / Passato Prossimo", "3ª pers. singolare m.", "L'oggetto manca in Scena II"),
    VerbForm("SPARITA", "Participio / Passato Prossimo", "3ª pers. singolare f.", "La figura manca in Scena II"),
    VerbForm("SCOPPIATO", "Participio / Passato Prossimo", "3ª pers. singolare m.", "Il pallone o tubo è esploso"),
    VerbForm("PIEGATO", "Participio / Passato Prossimo", "3ª pers. singolare m.", "L'asse o foglio è curvato"),
    VerbForm("BAGNATO", "Participio / Passato Prossimo", "3ª pers. singolare m.", "L'abito o terreno è umido"),
    VerbForm("BAGNATA", "Participio / Passato Prossimo", "3ª pers. singolare f.", "La veste o carta è bagnata"),
    VerbForm("DIVELTO", "Participio / Passato Prossimo", "3ª pers. singolare m.", "Il cartello o albero è sradicato"),
    VerbForm("COLMATO", "Participio / Passato Prossimo", "3ª pers. singolare m.", "Il secchio ora è pieno"),
    VerbForm("FUSO", "Participio / Passato Prossimo", "3ª pers. singolare m.", "Il metallo o cera si è sciolta"),
    VerbForm("DIPINTO", "Participio / Passato Prossimo", "3ª pers. singolare m.", "Il quadro ha nuovo colore"),
    VerbForm("TOLTO", "Participio / Passato Prossimo", "3ª pers. singolare m.", "L'elemento è stato rimosso"),
    VerbForm("TOLTA", "Participio / Passato Prossimo", "3ª pers. singolare f.", "La copertura è stata rimossa"),
    VerbForm("RIEMPITO", "Participio / Passato Prossimo", "3ª pers. singolare m.", "Il vaso ora è colmo"),
    VerbForm("RIEMPITA", "Participio / Passato Prossimo", "3ª pers. singolare f.", "La bottiglia è colma"),
    VerbForm("SPOSTATO", "Participio / Passato Prossimo", "3ª pers. singolare m.", "L'oggetto cambia posizione"),
    VerbForm("PULITO", "Participio / Passato Prossimo", "3ª pers. singolare m.", "La superficie è tersa"),
    VerbForm("LAVATO", "Participio / Passato Prossimo", "3ª pers. singolare m.", "L'indumento è pulito"),

    # Futuro Semplice (3ª pers. singolare / plurale)
    VerbForm("MARCIRÀ", "Futuro (3ª pers.)", "3ª pers. singolare", "La mela o frutto andrà a male"),
    VerbForm("MARCIRANNO", "Futuro (3ª pers.)", "3ª pers. plurale", "I frutti andranno a male"),
    VerbForm("CADRÀ", "Futuro (3ª pers.)", "3ª pers. singolare", "L'oggetto sta per cadere"),
    VerbForm("CADRANNO", "Futuro (3ª pers.)", "3ª pers. plurale", "Gli oggetti stanno per cadere"),
    VerbForm("VOLERÀ", "Futuro (3ª pers.)", "3ª pers. singolare", "L'uccello sta per spiccare il volo"),
    VerbForm("VOLERANNO", "Futuro (3ª pers.)", "3ª pers. plurale", "Gli uccelli spiccheranno il volo"),
    VerbForm("ROMPERÀ", "Futuro (3ª pers.)", "3ª pers. singolare", "Il contenitore rischia di rompersi"),
    VerbForm("SPARIRÀ", "Futuro (3ª pers.)", "3ª pers. singolare", "L'oggetto svanirà a breve"),
    VerbForm("BRUCERÀ", "Futuro (3ª pers.)", "3ª pers. singolare", "La legna prenderà fuoco"),
    VerbForm("CROLLERÀ", "Futuro (3ª pers.)", "3ª pers. singolare", "Il muro cedente sta per cadere"),
    VerbForm("SVUOTERÀ", "Futuro (3ª pers.)", "3ª pers. singolare", "Il personaggio sta per svuotare il contenitore"),
    VerbForm("APRIRÀ", "Futuro (3ª pers.)", "3ª pers. singolare", "La porta si spalancherà"),
    VerbForm("CHIUDERÀ", "Futuro (3ª pers.)", "3ª pers. singolare", "Il serramento si chiuderà"),
    VerbForm("SECCHERÀ", "Futuro (3ª pers.)", "3ª pers. singolare", "Il fiore appassirà"),
    VerbForm("SCOPPIERÀ", "Futuro (3ª pers.)", "3ª pers. singolare", "Il palloncino troppo gonfio esploderà"),
    VerbForm("FONDERÀ", "Futuro (3ª pers.)", "3ª pers. singolare", "La cera al sole si scioglierà")
]


@dataclass
class StereorebusEvaluation:
    """Detailed evaluation object for a Stereorebus proposal."""
    keys_text: str
    solution_text: str
    vignette_a_desc: str
    vignette_b_desc: str
    action_verb: str
    verb_tense: str
    total_letters: int
    
    # 4 Criteria Scores (0 - 100 total)
    score_naturalness: float         # 0 to 30 pt (Fluidezza I lettura)
    score_visual_adherence: float    # 0 to 30 pt (Disegnabilità differenziale)
    score_verb_coherence: float      # 0 to 20 pt (Passato/Futuro 3ª pers.)
    score_cesura: float              # 0 to 20 pt (Qualità della cerniera)
    overall_score: float             # 0 to 100 total score
    
    badge: str
    explanation: str


class StereorebusEngine:
    """Core AI & Algorithmic model for Stereorebus design and analysis."""

    def __init__(self, spacy_model: str = "it_core_news_sm"):
        self.anarebus_engine = AnarebusEngine(spacy_model)
        self.verbs_dict: Dict[str, VerbForm] = {v.form: v for v in STEREO_VERBS}

    def generate_from_solution(self, solution_text: str, max_results: int = 30) -> List[StereorebusEvaluation]:
        """
        Mode A: Top-Down Generator
        Decomposes a target Solution phrase into valid Stereorebus First Readings
        combining: [Grafema] + [Soggetto Visivo Vignetta A] + [Verbo Passato/Futuro Vignetta B].
        """
        clean_sol = AnarebusEngine.clean_text(solution_text)
        if not clean_sol:
            return []

        sol_cnt = collections.Counter(clean_sol)
        total_len = len(clean_sol)

        results = []

        # Scan all known stereorebus verb forms
        for verb_form, v_obj in self.verbs_dict.items():
            v_cnt = collections.Counter(verb_form)
            if not AnarebusEngine._is_submultiset(v_cnt, sol_cnt):
                continue

            rem1 = sol_cnt - v_cnt

            # Scan known rebus subjects
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
                        # Construct First Reading
                        keys_str = " ".join(grafemi + [subj_upper, verb_form])
                        
                        # Evaluate quality
                        eval_obj = self.evaluate_stereorebus(
                            keys_text=keys_str,
                            solution_text=solution_text,
                            subject=subj_upper,
                            verb_form=verb_form,
                            v_obj=v_obj
                        )
                        results.append(eval_obj)

                        if len(results) >= max_results * 3:
                            break

        results.sort(key=lambda x: -x.overall_score)
        return results[:max_results]

    def analyze_differential_states(
        self,
        vignette_a_subject: str,
        vignette_b_action: str,
        grafemi: str = "",
        max_results: int = 30
    ) -> List[StereorebusEvaluation]:
        """
        Mode B: Bottom-Up Differential Analyzer
        Given Vignette A subject (e.g. "PINO", "CASSA") and Vignette B action/state (e.g. "RECISO", "SVUOTATA"),
        constructs the First Reading and searches for valid target Solution phrases in the Italian dictionary.
        """
        subj = AnarebusEngine.clean_text(vignette_a_subject)
        act = AnarebusEngine.clean_text(vignette_b_action)
        graf = AnarebusEngine.clean_text(grafemi)

        if not subj or not act:
            return []

        # Construct candidate First Reading
        components = []
        if graf:
            components.append(graf)
        components.append(subj)
        components.append(act)

        keys_str = " ".join(components)
        
        # Search candidate solution phrases from anagram/resegmentation
        raw_solutions = self.anarebus_engine.solve_from_keys(keys_str, max_results=max_results)

        results = []
        v_obj = self.verbs_dict.get(act, VerbForm(act, "Passato / Futuro 3ª pers.", "3ª pers.", "Cambiamento di stato"))

        for sol in raw_solutions:
            eval_obj = self.evaluate_stereorebus(
                keys_text=keys_str,
                solution_text=sol["solution_text"],
                subject=subj,
                verb_form=act,
                v_obj=v_obj
            )
            results.append(eval_obj)

        results.sort(key=lambda x: -x.overall_score)
        return results[:max_results]

    def evaluate_stereorebus(
        self,
        keys_text: str,
        solution_text: str,
        subject: str,
        verb_form: str,
        v_obj: Optional[VerbForm] = None
    ) -> StereorebusEvaluation:
        """
        Evaluate a Stereorebus according to enigmatic classic rules (0 - 100 Quality Score).
        """
        clean_keys = AnarebusEngine.clean_text(keys_text)
        clean_sol = AnarebusEngine.clean_text(solution_text)
        total_len = len(clean_keys)

        # 1. Naturalness of I Reading (0 - 30 pt)
        anarebus_eval = self.anarebus_engine.evaluate_anarebus(keys_text, solution_text)
        nat_score = round(anarebus_eval.grammar_score * 3.0, 1) # 1.0-10.0 -> 3.0-30.0

        # 2. Visual Adherence & Action Clarity (0 - 30 pt)
        vis_score = 25.0
        if subject.lower() in COMMON_REBUS_SUBJECTS:
            vis_score += 5.0

        # 3. Verb Coherence (0 - 20 pt)
        verb_tense = v_obj.tense if v_obj else "Passato/Futuro 3ª pers."
        verb_score = 18.0
        if v_obj:
            verb_score = 20.0

        # 4. Cesura / Cerniera (0 - 20 pt)
        cesura_score = 15.0
        if anarebus_eval.max_contiguous_kept <= 3:
            cesura_score = 20.0
        elif anarebus_eval.max_contiguous_kept == 4:
            cesura_score = 12.0
        else:
            cesura_score = 5.0

        # Overall Score (0 - 100)
        overall = round(min(100.0, max(0.0, nat_score + vis_score + verb_score + cesura_score)), 1)

        # Length check penalty/bonus
        if not (12 <= total_len <= 30):
            overall = max(0.0, overall - 15.0)

        if overall >= 85:
            badge = "🏆 STEREOREBUS ECCELLENTE (90-100)"
        elif overall >= 70:
            badge = "🟢 VALIDO (70-84)"
        elif overall >= 50:
            badge = "⚠️ SUFFICIENTE (50-69)"
        else:
            badge = "❌ SCONSIGLIATO (< 50)"

        v_a_desc = f"Scena I (Stato Iniziale): {subject} integro / visibile"
        v_b_desc = f"Scena II (Azione): {subject} -> {verb_form} ({v_obj.visual_action if v_obj else 'cambio di stato'})"

        explanation = (
            f"Fluidezza I Lettura: {nat_score}/30 | "
            f"Disegnabilità: {vis_score}/30 | "
            f"Tempo Verbale ({verb_tense}): {verb_score}/20 | "
            f"Cesura: {cesura_score}/20"
        )

        return StereorebusEvaluation(
            keys_text=keys_text,
            solution_text=solution_text,
            vignette_a_desc=v_a_desc,
            vignette_b_desc=v_b_desc,
            action_verb=verb_form,
            verb_tense=verb_tense,
            total_letters=total_len,
            score_naturalness=nat_score,
            score_visual_adherence=vis_score,
            score_verb_coherence=verb_score,
            score_cesura=cesura_score,
            overall_score=overall,
            badge=badge,
            explanation=explanation
        )

    @staticmethod
    def get_llm_system_prompt() -> str:
        """Mode C: Return pre-configured System Prompt for LLM Enigmatic AI Assistants."""
        return (
            "Sei un maestro enigmistico specializzato in rebus stereoscopici (stereorebus).\n"
            "Genera proposte di prima lettura basate su due vignette (Stato A e Stato B).\n\n"
            "REGOLE FONDAMENTALI STEREOREBUS:\n"
            "1. La Prima Lettura DEVE contenere un verbo al passato remoto, imperfetto, participio passato o futuro semplice alla 3ª persona (singolare o plurale).\n"
            "2. Descrivi un cambio di stato visibile tra la Vignetta A (Stato iniziale) e la Vignetta B (Stato finale/azione).\n"
            "3. La lunghezza totale della prima lettura deve essere compresa tra 12 e 30 lettere.\n"
            "4. Riduci al minimo i grafemi isolati non legati ad oggetti naturali ed evita verbi arcaici astrusi.\n"
            "5. Le parole della I lettura devono spezzarsi nettamente (cesura/cerniera) per formare la II lettura di senso compiuto."
        )
