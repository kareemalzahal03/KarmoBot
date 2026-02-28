import chess
from chess import Square, PieceType, Color, Move, Board

class IncrementalBase(Board):
    """
    A chess.Board subclass that supports fully incremental state updates
    using a reversible step stack.

    Each chess move is decomposed into a sequence of primitive piece
    operations (add, delete, move). These operations are applied
    incrementally when a move is pushed, and reversed exactly when the
    move is popped.

    This design allows derived classes to maintain additional state
    (e.g. Zobrist hash, material counts, evaluation terms, NNUE features)
    without recomputation, while remaining perfectly synchronized with
    the board state.

    Subclasses must implement the primitive piece operations and define
    how incremental state is updated in response to them.
    """

    ### Startup / Reset Board

    def clear_stack(self) -> None:
        """
        Clear the board move stack and the incremental step stack, then
        rebuild all incremental state from the current/new board position.

        This overrides chess.Board.clear_stack(). It is invoked during
        initialization and any operation that resets the board state,
        including set_fen, set_board_fen, clear_board, etc.

        Subclasses can assume that after this call, incremental state
        exactly reflects the board position. (No manual update needed)
        """
        
        # Clear board move stack
        super().clear_stack()

        # Clear step stack
        self._steps_per_move = []
        self._from_sq = []
        self._to_sq = []
        self._piece_type = []
        self._piece_color = []
        
        # Clear increment history
        self.reset_incremental_state()

        # Set board using incremental steps
        for color, squares in enumerate(self.occupied_co):
            for square in chess.scan_reversed(squares):
                self._add_piece(square, self.piece_type_at(square), color)

    ### Required Overrides / API

    def reset_incremental_state(self) -> None:
        """
        Reset all incremental state maintained by subclasses.

        This method is called whenever the board is fully cleared, such as
        during initialization, or after a stack clear.
        """

    def _move_piece(self, from_sq: Square, to_sq: Square, piece: PieceType, color: Color) -> None:
        """
        Apply an incremental update corresponding to moving a piece from one
        square to another. Also provides the piecetype and color for convinience.
        """

    def _add_piece(self, square: Square, piece: PieceType, color: Color) -> None:
        """
        Apply an incremental update corresponding to adding a piece to a
        square.
        """

    def _del_piece(self, square: Square, piece: PieceType, color: Color) -> None:
        """
        Apply an incremental update corresponding to removing a piece from a
        square. Also provides the piecetype and color for convinience.
        """
        
    ### POP STEP LOGIC

    def pop(self) -> Move:
        """
        Undo the most recent move.

        Reverts the board state using chess.Board.pop(), then reverses all
        incremental steps associated with that move.
        """
        # Undo last chess move
        m = super().pop()
        # Unperform last move by undoing steps
        self._pop_steps()
        # Return move
        return m

    def _pop_steps(self):
        # Reverse all primitive steps associated with the most recent move.
        num_steps = self._steps_per_move.pop()
        while num_steps > 0:
            self._pop_step()
            num_steps -= 1

    def _pop_step(self):
        # Reverse a single primitive step from the step stack

        delete = self._from_sq.pop()
        add = self._to_sq.pop()
        piece = self._piece_type.pop()
        color = self._piece_color.pop()

        # Call reverse of function
        if delete is not None and add is not None:
            self._move_piece(add, delete, piece, color)
        elif delete is not None:
            self._add_piece(delete, piece, color)
        elif add is not None:
            self._del_piece(add, piece, color)

    ### PUSH STEP LOGIC

    def push(self, move: Move) -> None:
        """
        Push a move onto the board.

        The move is first decomposed into primitive steps and applied
        incrementally. The move is then pushed onto the underlying board.
        """
        # When a move is played, push the move steps onto step stack
        self._steps_per_move.append(0)
        self._push_steps(move)
        # Push move to chess board
        super().push(move)

    def _push_steps(self, move: Move) -> None:
        # Push the different steps of the move
        
        # Null move has no steps
        if not move:
            return

        cur_piece = self.piece_type_at(move.from_square)
        captured_piece = self.piece_type_at(move.to_square)

        # A direct capture, promotion, or both
        if captured_piece or move.promotion:
            
            # Delete captured piece if exists
            if captured_piece:
                self._push_step(delete = move.to_square, piece = captured_piece, color = not self.turn)

            # Handle promotion
            if move.promotion:
                # Delete pawn and add promoted piece
                self._push_step(delete = move.from_square, piece = chess.PAWN, color = self.turn)
                # Add promotion piece
                self._push_step(add = move.to_square, piece = move.promotion, color = self.turn)
            else:
                # Make move onto captured square
                self._push_step(delete = move.from_square, add = move.to_square, piece = cur_piece, color = self.turn)

            return
            
        # Make move directly, no piece on capture square
        self._push_step(delete = move.from_square, add = move.to_square, piece = cur_piece, color = self.turn)

        # Remove captured En passant square if it exists
        if cur_piece == chess.PAWN and move.to_square == self.ep_square:
            ep_pawn_square = self.ep_square + (-8 if self.turn else 8)
            # Delete opponent pawn below / above EP square            
            self._push_step(delete = ep_pawn_square, piece = chess.PAWN, color = not self.turn)

        # Castles
        elif cur_piece == chess.KING:
            # Check king move distance to verify if move is a castle
            move_dist = move.to_square - move.from_square
            if abs(move_dist) == 2:
                # +2 if kingside, -2 if queenside
                kingside = move_dist > 0
                # Rook old and new square
                if self.turn == chess.WHITE:
                    rook_old_sq = chess.H1 if kingside else chess.A1
                    rook_new_sq = chess.F1 if kingside else chess.D1
                else:
                    rook_old_sq = chess.H8 if kingside else chess.A8
                    rook_new_sq = chess.F8 if kingside else chess.D8

                # Move rook over king
                self._push_step(delete = rook_old_sq, add = rook_new_sq, piece = chess.ROOK, color = self.turn)

    def _push_step(self, *,
            delete: Square | None = None,
            add: Square | None = None,
            piece: PieceType,
            color: Color ) -> None:
        
        # Add current step to step stack
        self._steps_per_move[-1] += 1
        self._from_sq.append(delete)
        self._to_sq.append(add)
        self._piece_type.append(piece)
        self._piece_color.append(color)

        # Call related step function
        if delete is not None and add is not None:
            self._move_piece(delete, add, piece, color)
        elif delete is not None:
            self._del_piece(delete, piece, color)
        elif add is not None:
            self._add_piece(add, piece, color)
