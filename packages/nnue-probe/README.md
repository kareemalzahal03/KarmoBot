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

Building nnue-probe requires `make` and a working `gcc` environment.

With MacOS, it is recommended to install these using `brew`.
```bash
brew install make gcc
```
With Linux, they are typically available via the package manager. If not, you can install them using:
```bash
sudo apt-get install build-essential
```
With Windows, the [MSYS2](https://www.msys2.org/) environment is recommended for compiling nnue-probe. It provides a Unix-like environment and the necessary tools to build C/C++ code.

How to set up MSYS2 (Windows):

1. Download and install MSYS2 from the [MSYS2](https://www.msys2.org/) website.
2. Open an MSYS2 MinGW 64-bit terminal (e.g. via the Windows Start menu).
3. Install the MinGW 64-bit toolchain by entering `pacman -S mingw-w64-x86_64-toolchain`.
4. Close the MSYS2 MinGW 64-bit terminal and open another instance.

## Installation

Once requirements are met and a python virtual environment is created, simply run:

```bash
python -m pip install nnue-probe
```

Compilation of the C++ library & installation of the NNUE is performed automatically during installation/build of the python library. `make` compiles the native library using `g++` and ensures the default network file is available.

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
