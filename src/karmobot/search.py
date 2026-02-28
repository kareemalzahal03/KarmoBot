from typing import Iterator
import chess
from chess import Move, BB_ALL
from operator import itemgetter
from enum import IntEnum
from math import inf, log
import time

from .transptable import TranspositionTable
from .heuristics import Killers, History, MAX_PLY, peek_upto_two
from .nnue import EvaluateNNUE





class MoveStage(IntEnum):
    TT = 1
    GOOD_CAPTURE = 2
    KILLER = 3
    QUIET_GOOD_HISTORY = 4
    QUIET_BAD_HISTORY = 5
    BAD_CAPTURE = 6
    VERY_BAD_CAPTURE = 7

    def _is_capture_stage(self) -> bool:
        return self == 2 or self >= 6

    def _is_quiet_stage(self) -> bool:
        return 2 < self and self < 6
    
    def _is_futility_candidate(self) -> bool:
        return self > 4


MATE = 100000
PIECE_VALUES = (0,100,300,300,500,900,0)


class EngineNNUE(TranspositionTable, EvaluateNNUE):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Heuristics
        self.killers = Killers()
        self.history = History()

        # Node count, time management
        self._nodes = 0
        self._stop = False
        self._start_time = 0
        self._max_time = None


    def _time_exceeded(self) -> bool:
        if self._max_time is None:
            return False
        return (time.time() - self._start_time) >= self._max_time


    def push(self, move):
        super().push(move)

        self._nodes += 1

        # Only check occasionally for performance
        if (self._nodes & 2047) == 0:
            if self._time_exceeded():
                self._stop = True

    ### SEARCH ALGORITHM

    
    def think(self, max_depth: int, max_time: float = 10) -> tuple[int, Move]:
        """
        Iterative deepening search.
        
        Args:
            max_depth: Maximum depth to search.
            max_time: Maximum time in seconds (None = no time limit).

        Returns:
            (best_score, best_move) from the last fully completed depth.
        """

        # Terminal node check
        if self.is_game_over() or self.is_repetition() or self.is_fifty_moves():
            return 0, Move.null()

        # Reset search state
        self.history.age()
        self.killers.clear()
        self._nodes = 0
        self._stop = False

        # Time control setup
        self._start_time = time.time()
        self._max_time = max_time

        best_score = 0
        best_move = Move.null()

        # Iterative deepening loop
        for depth in range(1, max_depth + 1):

            # Stop BEFORE starting deeper iteration (soft stop)
            if (self._max_time is not None and
                (time.time() - self._start_time) >= self._max_time):
                break

            score, move = self._aspiration_window(depth, best_score)

            # If search was interrupted mid-depth, discard result
            if self._stop:
                break

            # Only update best move after fully completed depth
            best_score = score
            best_move = move

        self._max_time = None
        return best_score, best_move


    def _is_win_score(self, score: int):
        return abs(score) >= MATE - MAX_PLY        


    def _aspiration_window(self, depth: int, best_score: int) -> tuple[int, Move]:
        # Run search of the root node with a specified depth, and using
        # a predicted score from the previous iteration of deepening.
        # Doesn't run on the first few iterations so a stable score can be established...
        # https://www.chessprogramming.org/Aspiration_Windows

        # Check if aspiration window not necessary
        if depth < 4 or self._is_win_score(best_score):
            return self._root_alpha_beta(-inf, inf, depth)

        # Aspiration window
        window = 25
        alpha = best_score - window
        beta  = best_score + window

        # Search with window
        researches = 0
        while researches < 4:
            
            # Get score using window
            score, move = self._root_alpha_beta(alpha, beta, depth)

            # If winning value, return
            if self._is_win_score(score) or not move:
                return score, move

            # If fail-low, re-search
            if score <= alpha:
                alpha -= window
                window *= 2
                researches += 1
                continue

            # If fail-high, re-search
            if score >= beta:
                beta += window
                window *= 2
                researches += 1
                continue

            # If score was within window, return score
            return score, move
        
        # If too many re-searches, return search with no window
        return self._root_alpha_beta(-inf, inf, depth)

    


    def _root_alpha_beta(self, alpha: int, beta: int, depth: int) -> tuple[int, Move]:
        # Start search at the root node, assuming the game is not over.
        # https://www.chessprogramming.org/Root
        assert alpha >= -inf and beta <= inf and alpha < beta
        assert depth > 0

        # Search with alpha-beta pruning
        alpha0 = alpha
        best_score = -inf
        best_move = Move.null()

        for move_num, (move,_) in enumerate(self.ordered_legal_moves(), 1):

            isPV = (move_num == 1)

            ### GET SCORE OF MOVE

            self.push(move)
            

            # Principal Variation Search (PVS)
            score = 0
            if isPV:
                # PV Move: Full window, full depth
                score = -self._alpha_beta(-beta, -alpha, depth-1)
            else:
                # Other moves: Zero window, reduced depth
                score = -self._alpha_beta(-alpha-1, -alpha, depth-1)

                # Score within window: new PV found! Re-search with full window and depth
                if (score > alpha and score < beta):
                    score = -self._alpha_beta(-beta, -alpha, depth-1)

            self.pop()

            ### COMPARE MOVE SCORE TO PREVIOUS

            if score > best_score:
                # This is the best option your opponent has given you so far.
                best_score = score
                best_move = move

                if score > alpha: # ALPHA UPDATE
                    # This score is higher than the previous highest score I
                    # could guarantee myself in previous branches.
                    alpha = score

            if score >= beta: # BETA CUTOFF
                # https://www.chessprogramming.org/Beta-Cutoff
                # This score is higher than the minimum score my opponent 
                # can guarantee to give me. The rest of the search for this
                # node is not looked at.
                # Note: Not useful to store in TT due to aspiration window
                break

        # Should store an 'exact' node
        if best_move:
            self.store(depth, best_score, alpha0, beta, best_move)

        return best_score, best_move


    def _alpha_beta(self, alpha: int, beta: int, depth: int, ply: int = 1) -> int:

        if ply >= MAX_PLY:
            raise RecursionError()

        if self._stop:
            return 0

        # Check extension
        node_extension = 0
        is_check = self.is_check()
        if is_check:
            node_extension = 1

        # Quiescence search if not in check and no depth left
        elif depth == 0:
            return self._qsearch(alpha, beta, 5, ply)

        # If node repeats previous position in game
        if self.is_repetition(2):
            # Repeating a previous position is scored as equal, so if:
            # - Your position is better:
            # 1. You are encouraged to choose other moves instead of repeating,
            #    since repeating allows your opponent to repeat and potentially draw.
            # - Your position is worse:
            # 2. You are encouraged to choose this move and repeat.
            #    This option is usually pruned the next move because of rule 1.
            return 0

        # Neither side can win => auto draw
        if self.is_insufficient_material():
            return 0

        # Mate distance pruning
        alpha = max(alpha, -MATE + ply)
        beta = min(beta,  MATE - ply - 1)
        if alpha >= beta:
            return alpha

        # TT probe cutoff
        isPV = (beta - alpha) != 1
        if not isPV:
            score = self.probe(depth, alpha, beta)
            if score is not None:
                return score
        
        # TODO:
        # Syzygy Endgame Probe
        
        # Calculate static evaluation once, used for pruning heuristics
        static_eval = 0
        if not is_check:
            static_eval = self.evaluate()

        # Reverse Futility Pruning
        # https://www.chessprogramming.org/Reverse_Futility_Pruning
        if depth <= 4 and not isPV and not is_check:
            static_margin = 100
            # Prune if evaluation is too good
            if static_eval - depth * static_margin >= beta:
                return static_eval - depth * static_margin

        # Razoring
        # https://www.chessprogramming.org/Razoring
        if (not isPV
                and not is_check
                and depth == 3
                and static_eval + 1150 <= alpha
                and self.occupied_co[not self.turn].bit_count() > 3
                and bool(self.occupied ^ self.pawns ^ self.kings)):
            # Reduce search in hopeless nodes
            depth -= 1

        # Null-move pruning
        # https://www.chessprogramming.org/Null_Move_Pruning
        if (not isPV
                and not is_check
                and static_eval >= beta
                and depth > 1
                # Avoid zugzwang in K+P endgames (must be other pieces than just pawns and kings)
                and bool(self.occupied ^ self.pawns ^ self.kings)
                # Dont make consecutive null moves
                and len(self.move_stack) > 0 and self.move_stack[-1] != Move.null()):
            # Make a null move
            self.push(Move.null())
            

            # Allow Opponent to make a move
            r = 4
            null_depth = max(0, depth - r)
            null_score = -self._alpha_beta(-beta, -beta+1, null_depth, ply+1)

            # Undo Null Move
            self.pop()

            # If a reduced search on a null move fails high over beta, then return a fail high
            if null_score >= beta:
                # Avoid reporting false mates in zugzwang
                if self._is_win_score(null_score):
                    null_score = beta
                # Store as LOWER
                self.store(depth, null_score, -inf, beta, Move.null())
                return null_score

        # Move Generator
        num_moves, moves = peek_upto_two(self.ordered_legal_moves(ply))

        # Checkmate / Stalemate
        if num_moves == 0:
            if is_check:
                # Player to move is checkmated
                return - MATE + ply
            # Stalemate
            return 0
        
        # 50 Move Rule
        if self.halfmove_clock >= 100:
            # Verified after checking if at least 1 legal move
            return 0

        # One-reply extension
        if num_moves == 1:
            # There is only one move available for player to play...
            # Search loop runs once, with extended depth
            node_extension = 1

        # Start searching moves with alpha-beta pruning
        alpha0 = alpha
        best_score = -inf
        best_move = None

        # Judge moves
        for move_num, (move, move_stage) in enumerate(moves, 1):
            childPV = (move_num == 1)
            is_capture_stage = move_stage._is_capture_stage()
            is_promotion = bool(move.promotion)
            local_extension = node_extension

            # Recapture / Hanging Piece Extension (same-square)
            # https://www.chessprogramming.org/Recapture_Extensions
            recapture_extended = False
            if depth >= 2 and is_capture_stage and self.move_stack:
                last_move = self.move_stack[-1]
                # If last move by opponent lands on the same square as current move
                # Either they captured one of ours, or they hung a piece
                if (last_move and last_move.to_square == move.to_square):
                    local_extension += 1
                    recapture_extended = True

            # Futility pruning (quiets + bad captures only)
            # https://www.chessprogramming.org/Futility_Pruning
            if (not isPV
                    and not childPV
                    and not is_check
                    and depth <= 4
                    and not self._is_win_score(alpha)
                    and move_stage._is_futility_candidate()):

                # Add safety margin to static eval
                bound = static_eval + 0 + 25 * depth

                # If this safety margin does not exceed alpha, skip this move
                if bound <= alpha:
                    if bound > best_score:
                        best_score = bound
                continue

            # Late Move Reductions (conservative)
            # https://www.chessprogramming.org/Late_Move_Reductions
            reduction = 0
            if (not isPV
                    and not childPV
                    and not is_check
                    and depth >= 3
                    and move_num > 3
                    and not is_promotion
                    and not recapture_extended
                    and move_stage._is_futility_candidate()):
                
                # if move_stage == MoveStage.VERY_BAD_CAPTURE:
                #     reduction = int(
                #         .50 - .40*(isPV) + ( (1.35*log(depth)) + (.40*log(move_num)) )
                #     )

                # elif move_stage == MoveStage.BAD_CAPTURE:
                #     reduction = int(
                #         -.85 + ( (1.35*log(depth)) + (.40*log(move_num)) )
                #     )

                # else:
                #     reduction = int(
                #         -1.85 + ( (.50*log(depth)) + (1.65*log(move_num)) )
                #     )

                r = 1
                if depth >= 6 and move_num >= 10 and move_stage == MoveStage.QUIET_BAD_HISTORY:
                    r = 2
                elif move_stage in (MoveStage.QUIET_GOOD_HISTORY, MoveStage.BAD_CAPTURE):
                    r = 1

                reduction = min(r, 2, max(0, depth - 2))


            ### GET SCORE OF MOVE

            self.push(move)
            

            # Principal Variation Search (PVS)
            full_depth = depth - 1 + local_extension
            # reduction = 0 if self.is_check() else reduction # dont reduce if move gives check
            reduced_depth = max(0, full_depth - reduction)

            score = 0
            if (isPV and childPV):
                # PV Move: Full window, full depth
                score = -self._alpha_beta(-beta, -alpha, full_depth, ply+1)
            else:
                # Other moves: Zero window, reduced/full depth
                score = -self._alpha_beta(-alpha-1, -alpha, reduced_depth, ply+1)

                # Reduced search failed high: re-search with full depth
                if reduction and score > alpha:
                    score = -self._alpha_beta(-alpha-1, -alpha, full_depth, ply+1)

                # Score within window: new PV found! Re-search with full window and depth
                if (score > alpha and score < beta):
                    score = -self._alpha_beta(-beta, -alpha, full_depth, ply+1)

            self.pop()

            ### COMPARE MOVE SCORE TO PREVIOUS

            if score > best_score:
                # This is the best option your opponent has given you so far.
                best_score = score
                best_move = move

                if score > alpha: # ALPHA UPDATE
                    # This score is higher than the previous highest score I
                    # could guarantee myself in previous branches.
                    alpha = score

            if score >= beta: # BETA CUTOFF
                # https://www.chessprogramming.org/Beta-Cutoff
                # This score is higher than the minimum score my opponent 
                # can guarantee to give me. The rest of the search for this
                # node is not looked at.
                
                # Quiet move caused beta cutoff
                if not self.is_capture(move):
                    # Add to HISTORY
                    self.history.update(self, move, depth)
                    # Add as KILLER
                    self.killers.update(move, ply)

                break

            # Quiet move did not cause cutoff -> bad history
            if not self.is_capture(move):
                self.history.update(self, move, depth, penalize=True)

        # Store score in transposition table
        self.store(depth, best_score, alpha0, beta, best_move)

        return best_score
    

    
    

    def _qsearch(self, alpha: int, beta: int, depth_left: int, ply: int) -> int:
        """Quiescence search to avoid horizon effect"""
        # https://www.chessprogramming.org/Quiescence_Search
        assert(alpha >= -inf and beta <= inf and alpha < beta)

        if self._stop:
            return 0

        # Prevent infinite recursion (extremely unlikely).
        if depth_left <= 0:
            return self.evaluate()

        # Equal node
        if self.is_repetition(2) or self.is_insufficient_material():
            return 0

        # TT probe cutoff
        isPV = (beta - alpha) != 1
        if not isPV:
            score = self.probe(0, alpha, beta)
            if score is not None:
                return score

        # Move Generator
        is_check = self.is_check()
        moves = self.ordered_legal_evasions() if is_check else self.ordered_legal_captures()

        # Checkmate / Stalemate
        move = next(moves, None)
        any_moves = move is not None
        if not any_moves:
            if is_check:
                # Player to move is checkmated
                return - MATE + ply
            # Need to confirm if any LEGAL moves
            elif not any(self.generate_legal_moves()):
                return 0

        # 50 Move Rule
        if self.halfmove_clock >= 100:
            return 0

        # Standing Pat (not allowed if in check)
        # https://www.chessprogramming.org/Quiescence_Search#Standing_Pat
        
        best_score = -inf
        best_move = None

        stand_pat = 0
        if not is_check:
            # Standing Pat is static evaluation in quiet position
            stand_pat = self.evaluate()

            if stand_pat > alpha:
                if stand_pat >= beta:
                    return stand_pat
                alpha = stand_pat
                
            best_score = stand_pat

        # Start search
        while move is not None:

            if not is_check: # (move is a legal capture)
                see = self.SEE(move)

                # Static SEE Pruning, discard hopeless captures
                if see < -250:
                    move = next(moves, None)
                    continue

                # Delta Pruning
                # Calculate a heuristic score for futility pruning. Depending on the SEE:
                #  - For safe captures (SEE >= 0): an optimistic score using the maximum potential gain to represent the move impact.
                #  - For sacrifices    (SEE  < 0): a realistic estimate using the material cost to determine if the sacrifice is affordable.
                if see >= 0:
                    estimated_score = stand_pat + 90 + see + PIECE_VALUES[self.piece_type_at(move.to_square) or chess.PAWN]
                else:
                    estimated_score = stand_pat + see

                if estimated_score < alpha:
                    if estimated_score > best_score:
                        best_score = estimated_score
                    move = next(moves, None)
                    continue

            self.push(move)
               
            score = -self._qsearch(-beta, -alpha, depth_left - 1, ply+1)
            self.pop()

            if score > best_score:
                best_score = score
                best_move = move
            if score >= beta:
                # Store as LOWER node in TT
                self.store(0, best_score, -inf, beta, best_move)
                return score
            if score > alpha:
                alpha = score

            # Change to next move
            move = next(moves, None)

        return best_score






















    ### SEARCH ORDER

    def SEE(self, move: Move):
        """Return SEE score of capture. Accepts only legal captures in the position."""
        # https://www.chessprogramming.org/Static_Exchange_Evaluation
        # https://www.chessprogramming.org/SEE_-_The_Swap_Algorithm

        attacker_square = move.from_square
        victim_square = move.to_square

        attacker_type = self.piece_type_at(attacker_square) # Will throw error if None
        victim_type = self.piece_type_at(victim_square) or chess.PAWN # En Passant

        turn = self.turn
        occupied = self.occupied
        gain = [0]

        while True:

            ### Perform capture of victim by attacker

            # We gain the score of the victim piece
            gain.append(PIECE_VALUES[victim_type] - gain[-1])

            # The attacker square is no longer occupied, and is now unavailable to attack again
            occupied ^= chess.BB_SQUARES[attacker_square]

            # The capturing attacker is now the victim (now on victim square)
            victim_type = attacker_type

            ### Plan response from opponent

            # Opponent's turn to capture: Look for opponent's available attackers
            turn = not turn
            new_attackers = self.attackers(turn, victim_square, occupied) & occupied

            # If opponent has no attackers, break
            if not new_attackers:
                break

            # Opponent chooses least valuable attacker to recapture
            attacker_square = min( new_attackers, key = self.piece_type_at )
            attacker_type = self.piece_type_at( attacker_square )

            # King is chosen to recapture
            if attacker_type == chess.KING:
                # If opponent still has attackers, then break since king cannot go into check
                if (self.attackers(not turn, victim_square, occupied) & occupied):
                    break
                # Otherwise, capture with king and loop will break on next iteration

        # Note: Not exactly the same while loop as C implementation,
        # since no speculative score at end of gain.
        for d in range(len(gain)-1, 1, -1):
            gain[d-1] = -max( -gain[d-1], gain[d] )

        return gain[1]

    def generate_legal_quiets(self) -> Iterator[Move]:
        """Generates legal non-capture moves."""

        moves = self.generate_legal_moves(
            self.occupied_co[self.turn],
            # to_square is not occupied by an enemy piece
            BB_ALL ^ self.occupied_co[not self.turn]
        )

        if self.ep_square is None:
            yield from moves
            return
        
        for move in moves:
            if self.is_en_passant(move):
                continue
            yield move

    def quiet_score(self, move: Move):
        if move.promotion:
            return self.history.MAX_HISTORY + move.promotion
        return self.history.score(self, move)

    def ordered_legal_moves(self, ply: int = 0) -> Iterator[tuple[Move,MoveStage]]:
        # https://www.chessprogramming.org/Move_Generation
        # https://www.chessprogramming.org/Move_Ordering#Typical_move_ordering
        
        # PV / Hash Move
        tt_move = self.probe_move()
        if tt_move:
            yield tt_move, MoveStage.TT

        captures = sorted((
            (capture, self.SEE(capture))
            for capture in self.generate_legal_captures()
            if capture != tt_move
        ), key=itemgetter(1), reverse=True)

        # Non-Losing Captures
        for capture, see in captures:
            if see >= 0:
                yield capture, MoveStage.GOOD_CAPTURE

        killers = list(
            move for move in self.killers.get(ply)
            if self.is_legal(move) and move != tt_move)

        # Killers
        for killer in killers:
            yield killer, MoveStage.KILLER

        quiets = sorted((
            (move, self.quiet_score(move))
            for move in self.generate_legal_quiets()
            if move not in killers and move != tt_move
        ), key=itemgetter(1), reverse=True)

        # Quiets by history
        for quiet, score in quiets:
            if score >= self.history.MAX_HISTORY // 4:
                yield quiet, MoveStage.QUIET_GOOD_HISTORY
            else:
                yield quiet, MoveStage.QUIET_BAD_HISTORY

        # Losing Captures
        for capture, see in captures:
            if see < 0:
                yield capture, MoveStage.BAD_CAPTURE


    ### Move ordering for Qsearch


    def mvv_lva(self, move: Move) -> int:
        # https://www.chessprogramming.org/MVV-LVA

        attacker = self.piece_type_at(move.from_square)
        victim = self.piece_type_at(move.to_square) or chess.PAWN

        # MVV LVA
        return 10 * victim + 6 - attacker

    def ordered_legal_captures(self) -> Iterator[Move]:
        """Used for QSearch"""
        yield from sorted(
            self.generate_legal_captures(),
            key=self.mvv_lva, reverse=True
        )

    def evasion_score(self, move: Move) -> int:
        """Rate a single check evasion."""

        # Evasion is a capture -> capture with least valuable
        piece_at_square = self.piece_type_at(move.to_square)
        if piece_at_square:
            return 12 - piece_at_square # 6-11
        
        # Blocking check with piece -> block with least valuable
        # Dodge check by moving king -> last choice
        piece_moving = self.piece_type_at(move.from_square)
        return 6 - piece_moving # 0-5
                    
    def ordered_legal_evasions(self) -> Iterator[Move]:
        """All check evasions in sorted order."""
        yield from sorted(
            self.generate_legal_moves(),
            key=self.evasion_score, reverse=True
        )
