"""
Unit tests for AREPO Core Engines.
Verifies Syllabifier, AnarebusEngine, WordSearchEngine, PositionalTrie, and Database Connection.
"""

import unittest
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.engine.syllabifier import Syllabifier
from core.engine.anarebus_engine import AnarebusEngine
from core.engine.word_search_engine import WordSearchEngine
from core.engine.stereorebus_engine import StereorebusEngine
from core.engine.dawg_builder import PositionalTrie
from core.database.connection import DatabaseManager


class TestCoreEngines(unittest.TestCase):

    def test_syllabifier(self):
        line = "Nel mezzo del cammin di nostra vita"
        count, syls, details = Syllabifier.count_line_metric_syllables(line)
        self.assertEqual(count, 11)
        self.assertEqual(Syllabifier.get_meter_name(count), "Endecasillabo (11)")

    def test_anarebus_evaluator(self):
        engine = AnarebusEngine()
        eval_res = engine.evaluate_anarebus("DITO ROSA", "RIDATO SO")
        self.assertTrue(eval_res.is_perfect_anagram)
        self.assertGreater(eval_res.overall_quality_score, 7.0)

    def test_stereorebus_engine(self):
        engine = StereorebusEngine()
        cands = engine.analyze_differential_states("PINO CASSA", "RECISO SVUOTATA", max_results=10)
        self.assertIsNotNone(cands)

    def test_word_search_engine(self):
        engine = WordSearchEngine()
        results = engine.search_words(query="ROSA", pos_mode="start", category_filter="nouns", max_results=10)
        self.assertGreater(len(results), 0)
        self.assertEqual(results[0].match_position, "Inizio")

    def test_positional_trie(self):
        trie = PositionalTrie()
        trie.populate_from_list(["CANE", "CINA", "CONO", "ROMA"])
        matches = trie.search_pattern("C.N.")
        self.assertIn("CANE", matches)
        self.assertIn("CINA", matches)
        self.assertNotIn("ROMA", matches)

    def test_database_manager(self):
        db_mgr = DatabaseManager()
        session = db_mgr.get_core_session()
        self.assertIsNotNone(session)
        session.close()


if __name__ == "__main__":
    unittest.main()
