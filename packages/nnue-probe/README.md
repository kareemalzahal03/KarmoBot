# nnue-probe

`nnue-probe` is a lightweight, cross-platform Python wrapper around a native NNUE probing library for chess evaluation.

The native code is derived from:
- [dshawul/nnue-probe](https://github.com/dshawul/nnue-probe)
- [syzygy1/Cfish](https://github.com/syzygy1/Cfish)

It is packaged here as a small ctypes interface that can be used from Python chess engines.

## Features

- Builds native probe library during install/build.
- Downloads a default NNUE network automatically.
- Exposes a thin Python API over:
  - `nnue_init`
  - `nnue_evaluate_fen`
  - `nnue_evaluate`

## Requirements

- `g++` and `make` (for building shared library)

## Installation

From this package repo:

```bash
python -m pip install -e nnue-probe
```

During installation/build, `make` compiles the native library and ensures the default network file is available.

## Quick Start

```python
from nnue_probe import NNUEProbe

probe = NNUEProbe()
score = probe.evaluate_fen("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
print(score)
```

## API Notes

- `evaluate_fen(fen: str) -> int`:
  - easiest interface, accepts FEN directly.
- `evaluate(player, pieces_array, squares_array) -> int`:
  - thin wrapper for the raw C API.
  - caller provides ctypes arrays in the format expected by `nnue.h`.

For piece/square encoding details and memory layout, see [`src/nnue.h`](src/nnue.h).

## Network File

- Default network filename: `nn-62ef826d1a6d.nnue`.
- Network format: `halfkp_256x2-32-32`.
- You can initialize with a different network file path:

```python
probe = NNUEProbe(network_file="/path/to/your.nnue")
```

## Build Notes

- The native artifact is produced as `nnue_probe/libnnueprobe` (extensionless filename).
- Build and network retrieval are controlled by the package `Makefile`.
