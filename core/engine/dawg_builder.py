"""
DAWG / Trie Builder Module for AREPO.
Provides high-speed in-memory prefix trie and positional wildcard matcher for crossword auto-solvers.
"""

import re
from typing import List, Dict, Set, Optional, Tuple


class TrieNode:
    def __init__(self):
        self.children: Dict[str, 'TrieNode'] = {}
        self.is_word: bool = False


class PositionalTrie:
    """Fast in-memory Trie structure for positional pattern matching (e.g. '.O.A')."""

    def __init__(self):
        self.root = TrieNode()
        self.words_by_length: Dict[int, Set[str]] = {}

    def insert(self, word: str) -> None:
        w = word.strip().upper()
        if not w:
            return

        l = len(w)
        if l not in self.words_by_length:
            self.words_by_length[l] = set()
        self.words_by_length[l].add(w)

        node = self.root
        for char in w:
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]
        node.is_word = True

    def populate_from_list(self, word_list: List[str]) -> None:
        for w in word_list:
            self.insert(w)

    def search_pattern(self, pattern: str, limit: int = 50) -> List[str]:
        """
        Search pattern where '.' represents wildcard. e.g. 'C.N.' matches CANE, CINA, CONO.
        """
        p = pattern.strip().upper()
        if not p:
            return []

        p_len = len(p)
        candidates = self.words_by_length.get(p_len, set())
        if not candidates:
            return []

        # Convert pattern to regex
        regex_str = "^" + p.replace('.', '[A-Z]') + "$"
        regex = re.compile(regex_str)

        results = []
        for cand in candidates:
            if regex.match(cand):
                results.append(cand)
                if len(results) >= limit:
                    break

        return results
