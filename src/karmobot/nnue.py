import chess
from ctypes import c_int

from nnue_probe import NNUEProbe

from .increment import IncrementalBase

BoardArray = c_int * 65
NO_PIECE: c_int = 0
NO_SQUARE: c_int = 0
NO_INDEX: c_int = 64

class EvaluateNNUE(IncrementalBase):
    """Incremental NNUE evaluator backed by the `libnnueprobe` C library.

    This class maintains packed ctypes arrays (`pieces_array`, `squares_array`)
    in the format expected by `nnue_evaluate(side_to_move, pieces, squares)`.
    Array slots `0` and `1` are reserved for the two kings, and non-king pieces
    are kept densely packed from index `2` onward. `index_lookup` maps board
    squares to their current packed index, enabling O(1) add/delete/move updates
    after each incremental board change.

    `evaluate()` returns the NNUE score for the current position from the
    side-to-move perspective used by the probe API.
    """

    def __init__(self, **kwargs):
        self.nnue = NNUEProbe()
        super().__init__(**kwargs)

    def evaluate(self) -> int:
        score = self.nnue.evaluate(1 - self.turn, self.pieces_array, self.squares_array)
        return score

    # Incremental Board API

    def reset_incremental_state(self):
        super().reset_incremental_state()
        self.non_king_pieces = 0
        self.pieces_array  = BoardArray(*( NO_PIECE for _ in range(65)))
        self.squares_array = BoardArray(*(NO_SQUARE for _ in range(65)))
        self.index_lookup  = BoardArray(*( NO_INDEX for _ in range(65)))

    def _add_piece(self, square, piece, color):
        super()._add_piece(square, piece, color)

        # Get index of where to add piece
        adding_king = (piece == chess.KING)
        index = (1 - color) if adding_king else 2 + self.non_king_pieces

        # Update arrays
        self.pieces_array[index] = (7 - piece) + 6 * (1 - color)
        self.squares_array[index] = square
        self.index_lookup[square] = index

        # Update piece count
        self.non_king_pieces += not adding_king

    def _del_piece(self, square, piece, color):
        super()._del_piece(square, piece, color)

        # Remove piece from the board -> swap with last
            
        # Get current index
        index = self.index_lookup[square]

        if index < 2:
            # 'Removing' a king piece (kings dont change index)
            self.pieces_array[index] = NO_PIECE
            self.squares_array[index] = NO_SQUARE
            self.index_lookup[square] = NO_INDEX
            return
        
        # Swap with last to keep packed
        swap_index = 2 + self.non_king_pieces - 1
        if index != swap_index:
            # Put piece at last index in index
            self.pieces_array[index] = self.pieces_array[swap_index]
            # Put square at last index in index
            last_square = self.squares_array[swap_index]
            self.squares_array[index] = last_square
            # Update index location of last square to this index
            self.index_lookup[last_square] = index

        # Clear info in last index
        self.pieces_array[swap_index] = NO_PIECE
        self.squares_array[swap_index] = NO_SQUARE
        # Clear lookup location of square
        self.index_lookup[square] = NO_INDEX

        self.non_king_pieces -= 1

    def _move_piece(self, from_sq, to_sq, piece, color):
        super()._move_piece(from_sq, to_sq, piece, color)

        # Make the new square lookup to where the previous square was
        self.index_lookup[to_sq] = self.index_lookup[from_sq]
        self.index_lookup[from_sq] = NO_INDEX

        # Make the square at the index the new square
        self.squares_array[self.index_lookup[to_sq]] = to_sq
