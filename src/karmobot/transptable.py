from chess import Move
from .zobristhash import IncrementalZobrist

EXACT, LOWER, UPPER = 0, 1, 2
MAX_TT_SIZE = 200000

class TranspositionTable(IncrementalZobrist):
    """
    Transposition Table (TT) for caching search results.

    This class extends an incremental Zobrist-hashed board and uses the
    current Zobrist key as the dictionary key for stored positions.

    Each entry stores:
        - score: evaluation score from search
        - depth: search depth at which score was obtained
        - node_type: EXACT / LOWER / UPPER
        - best_move: best move found from this position

    The TT is used to:
        - produce alpha-beta cutoffs
        - improve move ordering
        - avoid re-searching identical positions

    Read more:
        - https://www.chessprogramming.org/Transposition_Table
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.table: dict[int, tuple[float, int, int, Move]] = {}

    def probe(self, depth: int, alpha: float, beta: float) -> float | None:
        """
        Probe the TT for a usable search score based on the state of the current
        search. To be used in alpha-beta search so searches are never re-done.
        """

        # Find if entry exists in TT
        entry = self.table.get(self.zobrist_hash)
        if not entry:
            return None
        entry_score, entry_depth, entry_type, _ = entry

        # Try to cutoff
        if (entry_depth >= depth and
                (  (entry_type == EXACT)
                or (entry_type == LOWER and entry_score >= beta)
                or (entry_type == UPPER and entry_score <= alpha) )):
            # Perform cutoff
            return entry_score
            
        return None

    def store(self, depth: int, score: float, alpha0: float, beta: float, best_move: Move) -> None:
        """Store a search result in the TT."""

        key = self.zobrist_hash
        node_type = UPPER if score <= alpha0 else LOWER if score >= beta else EXACT

        # Replace if already in TT, and not lower depth
        if key in self.table:
            old_depth = self.table[key][1]
            if depth >= old_depth:
                self.table[key] = (score, depth, node_type, best_move)
            return
        
        # Pop oldest entry if TT full
        if len(self.table) >= MAX_TT_SIZE:
            self.table.pop(next(iter(self.table)))

        # Add entry
        self.table[key] = (score, depth, node_type, best_move)

    def probe_entry(self) -> tuple[float, int, int, Move] | None:
        """Return raw TT entry for current position."""
        return self.table.get(self.zobrist_hash)

    def probe_score(self) -> float | None:
        """Return stored score regardless of depth or bounds."""
        entry = self.table.get(self.zobrist_hash)
        return entry[0] if entry else None

    def probe_type(self) -> int | None:
        """Return stored node type regardless of depth or bounds."""
        entry = self.table.get(self.zobrist_hash)
        return entry[2] if entry else None

    def probe_move(self) -> Move | None:
        """Return stored move regardless of depth or bounds."""
        entry = self.table.get(self.zobrist_hash)
        return entry[3] if entry else None
