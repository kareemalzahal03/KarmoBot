# https://github.com/lichess-bot-devs/lichess-bot/wiki/Create-a-homemade-engine

import logging
from typing import TypeAlias

import chess
from chess.engine import Limit, PlayResult

try: # Import lichess lib module requirements, only meant to be run within lichess-bot...
    # This module is provided by lichess-bot at runtime.
    from lib.engine_wrapper import MinimalEngine  # type: ignore  # pylint: disable=import-error
    MOVE: TypeAlias = PlayResult | list[chess.Move]
except ModuleNotFoundError as exc:
    raise RuntimeError("homemade.py must run inside lichess-bot runtime") from exc

from karmobot.search import EngineNNUE

# Use this logger variable to print messages to the console or log files.
# logger.info("message") will always print "message" to the console or log file.
# logger.debug("message") will only print "message" if verbose logging is enabled.
logger = logging.getLogger(__name__)

class ExampleEngine(MinimalEngine):
    """An example engine that all homemade engines inherit."""
    # DO NOT REMOVE -- lichess requires it

class KarmoBot(ExampleEngine):

    karmobot = EngineNNUE()

    def search(self,
               board: chess.Board,
               time_limit: Limit,
               ponder: bool,  # noqa: ARG002
               draw_offered: bool,
               root_moves: MOVE) -> PlayResult:
        """
        Choose a move using multiple different methods.

        :param board: The current position.
        :param time_limit: Conditions for how long the engine can search (e.g. we have 10 seconds and search up to depth 10).
        :param ponder: Whether the engine can ponder after playing a move.
        :param draw_offered: Whether the bot was offered a draw.
        :param root_moves: If it is a list, the engine should only play a move that is in `root_moves`.
        :return: The move to play.
        """

        # Set Bot Board Position
        self.karmobot.reset()
        for move in board.move_stack:
            self.karmobot.push(move)

        # Get Move
        score, move = self.karmobot.think(10)

        # Log Move, Score, Nodes
        logger.info("\t".join((
            move.uci(),
            str(score * (1 if self.karmobot.turn else -1)),
            str(self.karmobot._nodes),
        )))

        return PlayResult(move, None)
