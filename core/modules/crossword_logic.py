"""
Crossword Business Logic Module for AREPO.
Provides 2D grid matrix management, cell blacking/white toggle, rotational symmetry,
automatic numbering for horizontal/vertical slots, and DFS Backtracking Solver.
"""

from typing import List, Dict, Tuple, Optional, Set
from core.engine.dawg_builder import PositionalTrie
from core.database.connection import DatabaseManager
from core.database.models import Word


class CrosswordSlot:
    """Represents a horizontal or vertical slot in the crossword grid."""

    def __init__(self, slot_id: int, direction: str, number: int, start_row: int, start_col: int, length: int):
        self.slot_id = slot_id
        self.direction = direction  # "across" or "down"
        self.number = number
        self.start_row = start_row
        self.start_col = start_col
        self.length = length
        self.cells: List[Tuple[int, int]] = []
        
        for i in range(length):
            if direction == "across":
                self.cells.append((start_row, start_col + i))
            else:
                self.cells.append((start_row + i, start_col))


class CrosswordGrid:
    """2D Grid logic for crossword puzzles."""

    def __init__(self, rows: int = 11, cols: int = 11, symmetric: bool = True):
        self.rows = rows
        self.cols = cols
        self.symmetric = symmetric
        # Matrix values: ' ' = empty white, '#' = black cell, 'A'-'Z' = letter
        self.grid: List[List[str]] = [[' ' for _ in range(cols)] for _ in range(rows)]
        self.slots_across: List[CrosswordSlot] = []
        self.slots_down: List[CrosswordSlot] = []
        self.cell_numbers: Dict[Tuple[int, int], int] = {}
        self.recompute_numbers_and_slots()

    def toggle_black_cell(self, row: int, col: int) -> None:
        """Toggle black cell state with optional rotational 180° symmetry."""
        if not (0 <= row < self.rows and 0 <= col < self.cols):
            return

        current_is_black = (self.grid[row][col] == '#')
        new_val = ' ' if current_is_black else '#'
        self.grid[row][col] = new_val

        if self.symmetric:
            sym_r = self.rows - 1 - row
            sym_c = self.cols - 1 - col
            self.grid[sym_r][sym_c] = new_val

        self.recompute_numbers_and_slots()

    def set_cell_letter(self, row: int, col: int, letter: str) -> None:
        if 0 <= row < self.rows and 0 <= col < self.cols:
            if self.grid[row][col] != '#':
                self.grid[row][col] = letter.upper() if letter.strip() else ' '

    def clear_grid() -> None:
        self.grid = [[' ' for _ in range(self.cols)] for _ in range(self.rows)]
        self.recompute_numbers_and_slots()

    def recompute_numbers_and_slots(self) -> None:
        """Scan grid to auto-number cells and compute across/down slots."""
        self.cell_numbers.clear()
        self.slots_across.clear()
        self.slots_down.clear()

        number = 1
        slot_id = 1

        for r in range(self.rows):
            for c in range(self.cols):
                if self.grid[r][c] == '#':
                    continue

                starts_across = (c == 0 or self.grid[r][c - 1] == '#') and (c + 1 < self.cols and self.grid[r][c + 1] != '#')
                starts_down = (r == 0 or self.grid[r - 1][c] == '#') and (r + 1 < self.rows and self.grid[r + 1][c] != '#')

                if starts_across or starts_down:
                    self.cell_numbers[(r, c)] = number

                    if starts_across:
                        length = 0
                        while c + length < self.cols and self.grid[r][c + length] != '#':
                            length += 1
                        slot = CrosswordSlot(slot_id, "across", number, r, c, length)
                        self.slots_across.append(slot)
                        slot_id += 1

                    if starts_down:
                        length = 0
                        while r + length < self.rows and self.grid[r + length][c] != '#':
                            length += 1
                        slot = CrosswordSlot(slot_id, "down", number, r, c, length)
                        self.slots_down.append(slot)
                        slot_id += 1

                    number += 1

    def get_slot_pattern(self, slot: CrosswordSlot) -> str:
        chars = []
        for r, c in slot.cells:
            val = self.grid[r][c]
            chars.append(val if val in "ABCDEFGHIJKLMNOPQRSTUVWXYZ" else '.')
        return "".join(chars)


class CrosswordSolver:
    """Backtracking DFS Solver for crossword grids using PositionalTrie."""

    def __init__(self, trie: PositionalTrie):
        self.trie = trie

    def solve_grid(self, grid: CrosswordGrid, max_solutions: int = 1) -> bool:
        """
        Attempt to solve empty slots using DFS backtracking. Returns True if solved.
        """
        all_slots = grid.slots_across + grid.slots_down
        if not all_slots:
            return False

        # Sort slots by number of fixed letters (most constrained first)
        def constraint_key(slot: CrosswordSlot) -> float:
            pat = grid.get_slot_pattern(slot)
            fixed_count = sum(1 for ch in pat if ch != '.')
            return -fixed_count

        unfilled = [s for s in all_slots if '.' in grid.get_slot_pattern(s)]
        if not unfilled:
            return True

        unfilled.sort(key=constraint_key)

        def backtrack(idx: int) -> bool:
            if idx >= len(unfilled):
                return True

            slot = unfilled[idx]
            pattern = grid.get_slot_pattern(slot)
            candidates = self.trie.search_pattern(pattern, limit=20)

            for cand in candidates:
                # Save previous grid state for slot cells
                prev_vals = [grid.grid[r][c] for r, c in slot.cells]

                # Place candidate word
                for (r, c), char in zip(slot.cells, cand):
                    grid.grid[r][c] = char

                if backtrack(idx + 1):
                    return True

                # Restore previous state on backtrack
                for (r, c), old_char in zip(slot.cells, prev_vals):
                    grid.grid[r][c] = old_char

            return False

        return backtrack(0)
