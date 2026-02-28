import chess
from chess import Square, PieceType, Color, Move
from chess.polyglot import POLYGLOT_RANDOM_ARRAY
from .increment import IncrementalBase

class IncrementalZobrist(IncrementalBase):

    def __init__(self, **kwargs) -> None:
        self._hash_array: list[int] = POLYGLOT_RANDOM_ARRAY
        super().__init__(**kwargs)
    
    ### Incrementally update hash after pieces move
    
    def reset_incremental_state(self):
        super().reset_incremental_state()
        # Reset hash and clear count
        self.board_hash = 0
        self._repetition_count: dict[int, int] = {}

    def _hash_piece_at_square(self, square: Square, piece: PieceType, color: Color) -> None:
        # Modify board hash to hash out/in a piece at a square
        self.board_hash ^= self._hash_array[ 64 * (( piece - 1 ) * 2 + color) + square ]

    def _add_piece(self, square: Square, piece: PieceType, color: Color) -> None:
        super()._add_piece(square, piece, color)
        # When a piece is added, hash it into board hash
        self._hash_piece_at_square(square, piece, color)

    def _del_piece(self, square: Square, piece: PieceType, color: Color) -> None:
        super()._del_piece(square, piece, color)
        # When a piece is deleted, hash it out of board hash
        self._hash_piece_at_square(square, piece, color)

    def _move_piece(self, from_sq: Square, to_sq: Square, piece: PieceType, color: Color) -> None:
        super()._move_piece(from_sq, to_sq, piece, color)
        # When a piece moves, hash it out of from_square and into to_square.
        self._hash_piece_at_square(from_sq, piece, color)
        self._hash_piece_at_square(to_sq, piece, color)

    def clear_stack(self):
        # When board reset and board hash calculated, set initial zobrist and count
        super().clear_stack()
        # Set initial Zobrist hash
        self.zobrist_hash = self.board_hash ^ self._feature_hash()
        # Make sure first board seen once
        self._inc_repetition()

    ### Position Repitition Count

    def push(self, move: Move) -> None:
        super().push(move)
        # Set New Zobrist hash
        self.zobrist_hash = self.board_hash ^ self._feature_hash()
        # Increment repitition count after move push
        self._inc_repetition()

    def _inc_repetition(self):
        # Increment count of current position
        k = self.zobrist_hash
        self._repetition_count[k] = self._repetition_count.get(k, 0) + 1

    def pop(self) -> Move:
        # Decrement repitition before move pop
        self._dec_repetition()
        # Undo last chess move
        move = super().pop()
        # Set zobrist hash
        self.zobrist_hash = self.board_hash ^ self._feature_hash()
        # Return move
        return move

    def _dec_repetition(self):
        k = self.zobrist_hash
        c = self._repetition_count[k]
        if c <= 1:
            del self._repetition_count[k]
        else:
            self._repetition_count[k] = c - 1

    def is_repetition(self, count = 3) -> bool:
        """Checks if the current position has repeated >= `count` times."""
        return self._repetition_count[self.zobrist_hash] >= count
    
    def repetitions(self) -> int:
        """Number of times a position has been repeated."""
        return self._repetition_count[self.zobrist_hash]

    ### Private hashing logic

    def _feature_hash(self) -> int:
        h = 0
        
        # Hash in the turn
        if self.turn:
            h ^= self._hash_array[780]

        # Hash in the en-passant file if EP is pseudo-legal
        if self.ep_square:
            capturers = (
                self.pawns & self.occupied_co[self.turn] &
                chess.BB_PAWN_ATTACKS[not self.turn][self.ep_square] &
                chess.BB_RANKS[4 if self.turn else 3])
            if capturers:
                h ^= self._hash_array[772 + chess.square_file(self.ep_square)]

        # Hash in Castle Rights
        cr = self.castling_rights
        if cr & chess.BB_H1:
            h ^= self._hash_array[768]
        if cr & chess.BB_A1:
            h ^= self._hash_array[769]
        if cr & chess.BB_H8:
            h ^= self._hash_array[770]
        if cr & chess.BB_A8:
            h ^= self._hash_array[771]

        return h
