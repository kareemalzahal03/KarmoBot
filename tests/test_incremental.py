import chess
import pytest
from chess.polyglot import zobrist_hash

from karmobot.nnue import EvaluateNNUE
from karmobot.zobristhash import IncrementalZobrist

TEST_CASES = [
    # Normal moves
    (chess.STARTING_BOARD_FEN, "g1f3"), # Reti
    (chess.STARTING_BOARD_FEN, "e2e4"), # King's Pawn
    # Capture
    ("8/8/2R1r3/8/2K1k3/8/8/8 w - - 0 1", "c6e6"), # white capture
    ("8/8/2R1r3/8/2K1k3/8/8/8 b - - 0 1", "e6c6"), # black capture
    # En pessant
    ("rnbqkbnr/ppppp1pp/5p2/3P4/8/8/PPP1PPPP/RNBQKBNR b KQkq - 0 2", "e7e5"), # en pessant now exists
    ("rnbqkbnr/pppp2pp/5p2/3Pp3/8/8/PPP1PPPP/RNBQKBNR w KQkq e6 0 3", "d5e6"), # en pessant capture
    ("rnbqkb1r/ppp1pppp/5n2/3P4/8/8/PPP2PPP/RNBKQBNR b kq - 0 2", "e7e5"), # en pessant square exists, but illegal
    # Castling
    ("r1bqkb1r/pppp1ppp/2n2n2/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4", "e1g1"), # white king side castle
    ("r1bqk2r/pppp1ppp/2n2n2/2b1p3/2B1P3/3P1N2/PPP2PPP/RNBQ1RK1 b kq - 0 5", "e8g8"), # black king side castle
    ("r3kbnr/pppqpppp/2n5/3p1b2/3P1B2/2N5/PPPQPPPP/R3KBNR w KQkq - 6 5", "e1c1"), # white queen side castle
    ("r3kbnr/pppqpppp/2n5/3p1b2/3P1B2/2N5/PPPQPPPP/2KR1BNR b kq - 7 5", "e8c8"), # black queen side castle
    ("rnbqk1nr/pppp1ppp/4p3/8/1B1P4/8/PPP1PPPP/RN1QKBNR b KQkq - 0 3", "g8f6"), # castling is illegal
    ("rnbqk2r/pppp1pp1/4pn1p/8/3P4/8/PPPBPPPP/RN1QKBNR w KQkq - 0 5", "d2b4"), # castling becomes illegal
    # Promotions
    ("2K1q3/3P4/2k5/8/8/8/8/8 w - - 0 1", "d7d8q"), # white promotion to queen
    ("2K1q3/3P4/2k5/8/8/8/8/8 w - - 0 1", "d7d8b"), # white promotion to bishop
    ("2K1q3/3P4/2k5/8/8/8/8/8 w - - 0 1", "d7e8q"), # white capture + promotion to queen
    ("2K1q3/3P4/2k5/8/8/8/8/8 w - - 0 1", "d7e8b"), # white capture + promotion to bishop
    ("8/8/8/8/8/5K2/4p3/3Q1k2 b - - 0 1", "e2e1q"), # black ``
    ("8/8/8/8/8/5K2/4p3/3Q1k2 b - - 0 1", "e2e1b"),
    ("8/8/8/8/8/5K2/4p3/3Q1k2 b - - 0 1", "e2d1q"),
    ("8/8/8/8/8/5K2/4p3/3Q1k2 b - - 0 1", "e2d1b"),
]


@pytest.fixture(scope="module")
def zobrist_board() -> IncrementalZobrist:
    return IncrementalZobrist()

def _same_hash(board: IncrementalZobrist) -> bool:
    return board.zobrist_hash == zobrist_hash(board) and board.repetitions() == 1

@pytest.mark.parametrize(("fen", "uci"), TEST_CASES)
def test_incremental_zobrist_matches_notebook_checks(
    zobrist_board: IncrementalZobrist, fen: str, uci: str
) -> None:
    
    # After reseting board
    zobrist_board.set_fen(fen)
    assert _same_hash(zobrist_board)

    # Pushing and popping null move
    zobrist_board.push(chess.Move.null())
    assert _same_hash(zobrist_board)
    zobrist_board.pop()
    assert _same_hash(zobrist_board)

    # Ensure test case is correct
    move = chess.Move.from_uci(uci)
    assert zobrist_board.is_legal(move), f"Illegal move in test case: {uci} for {fen}"

    # Push move
    zobrist_board.push(move)
    assert _same_hash(zobrist_board)

    # Undo move
    if zobrist_board.move_stack:
        zobrist_board.pop()
        assert _same_hash(zobrist_board)


### NNUE Board State stays in Sync with underlying board


@pytest.fixture(scope="module")
def nnue_board() -> EvaluateNNUE:
    return EvaluateNNUE()

@pytest.mark.parametrize(("fen", "uci"), TEST_CASES)
def test_evaluate_nnue_matches_notebook_checks(
    nnue_board: EvaluateNNUE, fen: str, uci: str
) -> None:
    
    # After reseting board
    nnue_board.set_fen(fen)
    assert _same_board(nnue_board)

    # Pushing and popping null move
    nnue_board.push(chess.Move.null())
    assert _same_board(nnue_board)
    nnue_board.pop()
    assert _same_board(nnue_board)

    # Ensure test case is correct
    move = chess.Move.from_uci(uci)
    assert nnue_board.is_legal(move), f"Illegal move in test case: {uci} for {fen}"

    # Push move
    nnue_board.push(move)
    assert _same_board(nnue_board)

    # Undo move
    if nnue_board.move_stack:
        nnue_board.pop()
        assert _same_board(nnue_board)


def _same_board(nnue: EvaluateNNUE) -> bool:
    rebuilt = chess.Board()
    rebuilt.clear_board()

    i = 0
    while True:
        piece_code = nnue.pieces_array[i]
        if piece_code == 0:
            break

        color = piece_code <= 6
        piece = 6 * (1 - color) + 7 - piece_code
        square = nnue.squares_array[i]
        rebuilt.set_piece_at(square, chess.Piece(piece, color))
        i += 1

    return (
        rebuilt.occupied_co[0] == nnue.occupied_co[0]
        and rebuilt.occupied_co[1] == nnue.occupied_co[1]
        and rebuilt.pawns == nnue.pawns
        and rebuilt.knights == nnue.knights
        and rebuilt.bishops == nnue.bishops
        and rebuilt.rooks == nnue.rooks
        and rebuilt.queens == nnue.queens
        and rebuilt.kings == nnue.kings
    )
