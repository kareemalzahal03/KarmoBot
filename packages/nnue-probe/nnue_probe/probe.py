from __future__ import annotations

from ctypes import CDLL, Array, c_int
from importlib.resources import files
from pathlib import Path

# Helpers

def _package_dir() -> Path:
    return Path(str(files(__package__)))

def default_network_path() -> Path:
    package_dir = _package_dir()
    nets = sorted(package_dir.glob("nn-*.nnue"))
    if not nets:
        raise FileNotFoundError(f"Could not find packaged nn-*.nnue file in {package_dir}")
    return nets[0]

def load_library() -> CDLL:
    package_dir = _package_dir()
    candidate = package_dir / "libnnueprobe.so"
    if candidate.exists():
        return CDLL(str(candidate))
    raise FileNotFoundError(f"Could not find NNUE shared library in {package_dir}.")

# Main Class

class NNUEProbe:
    """Thin Python wrapper around the exported nnue-probe C API."""
    # See src/nnue.h for more info on array formats...

    def __init__(self, network_file: str | Path | None = None) -> None:
        # Load Library
        self._lib = load_library()
        # Init Library
        network_path = Path(network_file) if network_file is not None else default_network_path()
        self._lib.nnue_init(str(network_path).encode("utf-8"))

    def evaluate_fen(self, fen: str) -> int:
        """
        Evaluate on FEN string
        Returns
          Score relative to side to move in approximate centi-pawns
        """
        return int(self._lib.nnue_evaluate_fen(fen.encode("utf-8")))

    def evaluate(self, player: c_int, pieces_array: Array[c_int], squares_array: Array[c_int]) -> int:
        """
        Evaluation subroutine suitable for chess engines.
        -------------------------------------------------
        Piece codes are
            wking=1, wqueen=2, wrook=3, wbishop= 4, wknight= 5, wpawn= 6,
            bking=7, bqueen=8, brook=9, bbishop=10, bknight=11, bpawn=12,
        Squares are
            A1=0, B1=1 ... H8=63
        Input format:
            piece[0] is white king, square[0] is its location
            piece[1] is black king, square[1] is its location
            ..
            piece[x], square[x] can be in any order
            ..
            piece[n+1] is set to 0 to represent end of array
        Returns
          Score relative to side to move in approximate centi-pawns
        """
        return int(self._lib.nnue_evaluate(player, pieces_array, squares_array))
