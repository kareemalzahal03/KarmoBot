# `lichess/`

This directory contains the integration layer between the chess engine and the `lichess-bot` runtime. These files are the adapter/config/deployment wiring that makes it play games on [Lichess](https://lichess.org/).

Lichess provides a simple API for hosting chess engines that can be played against. The Dockerfile starts with the template [lichess-bot](https://github.com/lichess-bot-devs/lichess-bot) implementation, copies KarmoBot source code and configuration files (this directory), and runs a containerized server which communicates the engine with lichess.

## What This Folder Is For

`lichess-bot` contains a config directory that defines:
- how to connect to Lichess
- what engine to run
- what protocol to use (`uci`, `xboard`, or `homemade`)
- challenge behavior and runtime policy

This folder contains the configuration files & `homemade.py` wrapper engine that when placed in `lichess-bot\config`, will be able to run our engine and communicate with lichess.

This project uses `protocol: homemade`, which means `lichess-bot` calls Python code in `homemade.py` directly.

Read more: [Lichess Wiki](https://github.com/lichess-bot-devs/lichess-bot/wiki/Create-a-homemade-engine)

## File-by-File

- `config.yml`
  - Main `lichess-bot` configuration.
  - Defines engine path, protocol, challenge settings, draw/resign policy, and bot behavior.
- `homemade.py`
  - Python adapter between `lichess-bot` and `karmobot`.
  - Receives board state from `lichess-bot`, rebuilds engine state, runs search, and returns a move.
- `Dockerfile`
  - Builds a runnable image from `lichessbotdevs/lichess-bot`.
  - Copies this repo into the container and installs the Python packages.
- `.env` / `.env.example`
  - Secrets and runtime env vars (for example `LICHESS_BOT_TOKEN`).
  - Should stay private and never be committed with real credentials.

## How The Runtime Flow Works

1. Container starts with `lichess-bot`.
2. `lichess-bot` reads `/lichess-bot/config/config.yml`.
3. Because `engine.protocol` is `homemade`, it imports `config/homemade.py`.
4. `KarmoBot.search(...)` is called for each move decision.
5. `search(...)` in `homemade.py`:
   - resets internal engine state
   - replays all moves from the incoming `board.move_stack`
   - calls `EngineNNUE.think(...)`
   - returns a `PlayResult` move to `lichess-bot`
6. `lichess-bot` sends that move to Lichess API.

## How Docker Wiring Works

From repo root:

```bash
docker compose up -d --build
docker compose logs -f karmobot
docker compose down
```

`docker-compose.yml` uses:
- build context: repo root
- Dockerfile: `lichess/Dockerfile`
- env file: `lichess/.env`
