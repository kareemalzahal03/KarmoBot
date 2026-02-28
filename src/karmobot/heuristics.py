from chess import Board, Move
from typing import Iterator, Iterable, TypeVar
from itertools import chain

MAX_PLY = 128

class Killers:
    """
    Killer move heuristic manager.
    - https://www.chessprogramming.org/Killer_Move
    """
    
    SLOTS = 2

    def __init__(self):
        self.table: list[list[Move]] = [
            [Move.null(), Move.null()] for _ in range(MAX_PLY)
        ]

    def _in_bounds(self, ply: int) -> bool:
        return 0 <= ply < MAX_PLY

    def clear(self):
        """Clear all killers (e.g. new search)."""
        for row in self.table:
            row[0] = Move.null()
            row[1] = Move.null()

    def update(self, killer: Move, ply: int):
        """Update killers at ply using primary/secondary shift semantics."""
        if not killer or not self._in_bounds(ply):
            return

        primary = self.table[ply][0]
        if killer != primary:
            self.table[ply][1] = primary
            self.table[ply][0] = killer

    def get(self, ply: int) -> Iterator[Move]:
        if not self._in_bounds(ply):
            return
        primary = self.table[ply][0]
        if primary:
            yield primary
        secondary = self.table[ply][1]
        if secondary:
            yield secondary


class History:
    """
    History heuristic move manager.
    - https://www.chessprogramming.org/History_Heuristic
    """

    MAX_HISTORY = 200

    def __init__(self):
        # History array: [color][piecetype][square]
        self._array = [[[0 for _ in range(64)] for _ in range(6)] for _ in range(2)]

    def score(self, board: Board, move: Move) -> None:
        # Get historical score
        color = board.turn
        piece = board.piece_type_at(move.from_square)-1
        square = move.to_square
        return self._array[color][piece][square]

    def age(self):
        # Reduce history from old positions, but do not remove entirely
        for color in range(2):
            for piece in range(6):
                for square in range(64):
                    self._array[color][piece][square] /= 8

    def update(self, board: Board, move: Move, depth: int, *, penalize = False) -> None:
        # https://www.chessprogramming.org/History_Heuristic#Update

        color = board.turn
        piece = board.piece_type_at(move.from_square)-1
        square = move.to_square

        bonus = ( depth * depth ) * ( -1 if penalize else 1 )
        clampedbonus = min(self.MAX_HISTORY, max(-self.MAX_HISTORY, bonus))

        self._array[color][piece][square] \
            += clampedbonus - self._array[color][piece][square] * abs(clampedbonus) / self.MAX_HISTORY
    
T = TypeVar('T')
def peek_upto_two(it: Iterator[T]) -> tuple[int, Iterable[T]]:
    """
    Peek at most two elements from an iterator and classify its size.

    This allows checking whether an iterator has
    0 / 1 / 2+ elements without materializing it into a list.

    Runs in O(1) time and memory.
    """

    x1 = next(it, None)
    if x1 is None:
        return 0, ()
    
    x2 = next(it, None)
    if x2 is None:
        return 1, (x1,)

    return 2, chain((x1, x2), it)
