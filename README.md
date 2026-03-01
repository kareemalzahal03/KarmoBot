

<div align="center">  <!-- https://www.svggenie.com/tools/font-to-svg -->
  <img src=".github/images/karmo-bot-chango-regular.svg" alt="KARMO BOT">
</div>
<br>

KarmoBot is a Python chess engine project focused on practical search performance, incremental state updates, and Lichess deployment.

It combines:
- a custom alpha-beta search engine (`karmobot`)
- a packaged NNUE probing backend (`packages/nnue-probe`)
- a `lichess-bot` integration layer (`lichess/`)

## Highlights

- NNUE evaluation through a native probe library (`nnue-probe`).
- Incremental board state and hash updates for speed.
- Alpha-beta with iterative deepening and aspiration windows.
- Move ordering using transposition table, captures, killers, and history heuristics.
- Quiescence search and common pruning/reduction techniques.
- Dockerized Lichess runtime based on `lichessbotdevs/lichess-bot`.

## Project Layout

```text
.
├── src/karmobot/              # Engine package (search, heuristics, NNUE integration)
├── packages/nnue-probe/       # Native NNUE probe packaged as a Python dependency
├── lichess/                   # Lichess adapter/config/docker integration
├── tests/                     # Engine and incremental-state tests
├── pyproject.toml             # KarmoBot package metadata
└── docker-compose.yml         # Local container orchestration
```

## Requirements

- Python `>= 3.10`
- See [nnue-probe requirements](packages/nnue-probe/README.md) for building the native NNUE probe library.

## Installation (Local Development)

Within a Python virtual environment, install with editable mode from repo root:

```bash
python -m pip install -e .
```

This will install `karmobot` and required dependencies automatically, including `nnue-probe`.

## Running Tests

Install pytest:

```bash
python -m pip install pytest
```

From repo root:

```bash
python -m pytest -q
```

Test coverage currently focuses on:
- search behavior on curated positions
- incremental zobrist correctness
- NNUE board-state synchronization
