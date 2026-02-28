from dataclasses import dataclass
from typing import Callable

import chess
import pytest

from karmobot.search import EngineNNUE, MATE


Validator = Callable[[EngineNNUE, int, chess.Move], bool]


@dataclass(frozen=True)
class EngineTestCase:
    case_id: str
    fen: str
    depth: int
    validator: Validator
    expectation: str


ENGINE_TEST_CASES = [
    EngineTestCase(
        case_id="mate_in_2",
        fen="1q4k1/p2Q1ppp/4p3/3p4/8/2R4P/PrP1RPP1/6K1 b - - 0 30",
        depth=6,
        validator=lambda _engine, score, move: score >= MATE - 10 and move.uci() == "b2b1",
        expectation="find forced mate with b2b1",
    ),
    EngineTestCase(
        case_id="mate_in_4",
        fen="r5rk/2p1Nppp/3p3P/pp2p1P1/4P3/2qnPQK1/8/R6R w - - 1 0",
        depth=9,
        validator=lambda _engine, score, move: score >= MATE - 20 and move.uci() == "h6g7",
        expectation="find forced mate line starting with h6g7",
    ),
    EngineTestCase(
        case_id="dont_hang_mate_in_2",
        fen="1q4k1/p2Q1ppp/4p3/3p4/8/2rR3P/PrP1RPP1/6K1 w - - 0 30",
        depth=8,
        validator=lambda _engine, score, _move: score > -MATE + 1000,
        expectation="avoid immediate forced-mate collapse",
    ),
    EngineTestCase(
        case_id="dont_hang_mate_in_3",
        fen="2r3k1/3R1ppp/8/6Q1/2P1p3/7P/5PPK/q7 b - - 5 45",
        depth=8,
        validator=lambda _engine, score, _move: score > -MATE + 1000,
        expectation="avoid immediate forced-mate collapse",
    ),
    EngineTestCase(
        case_id="dont_blunder_b8c8",
        fen="1k6/8/1p6/6P1/4r3/1R6/1p2rB2/1R4K1 b - - 0 40",
        depth=8,
        validator=lambda _engine, _score, move: move.uci() != "b8c8",
        expectation="avoid blunder move b8c8",
    ),
    EngineTestCase(
        case_id="dont_blunder_g6f6",
        fen="8/B6k/6R1/7P/5np1/5p2/5Pr1/7K w - - 4 65",
        depth=9,
        validator=lambda _engine, _score, move: move.uci() != "g6f6",
        expectation="avoid blunder move g6f6",
    ),
    EngineTestCase(
        case_id="go_for_perpetual",
        fen="6r1/1b3k2/7R/1B1p4/pP1PpP2/P3K1p1/8/8 w - - 2 51",
        depth=8,
        validator=lambda _engine, score, move: move.uci() == "h6h7" and score == 0,
        expectation="choose perpetual-check move h6h7 with near-draw score",
    ),
    EngineTestCase(
        case_id="middle_game",
        fen="r1bq1rk1/pppnn1bp/3p2p1/3Ppp2/2P1P1P1/2N2P2/PP2B2P/R1BQNRK1 b - -",
        depth=8,
        validator=lambda _engine, score, move: -100 <= score <= 100,
        expectation="pick a sane improving move with a roughly balanced score",
    ),
]


@pytest.mark.parametrize("case", ENGINE_TEST_CASES, ids=[c.case_id for c in ENGINE_TEST_CASES])
def test_engine_notebook_positions(case: EngineTestCase) -> None:
    
    # Create New Engine
    engine = EngineNNUE()

    # Run engine on position
    engine.set_fen(case.fen)
    score, move = engine.think(case.depth)

    # Normalized score from white's perspective
    cp = score * (1 if engine.turn else -1)

    assert case.validator(engine, score, move), (
        f"{case.expectation}; got move={move.uci()}, score={score}, cp={cp}, depth={case.depth}"
    )
