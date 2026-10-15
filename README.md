# Gaze — P&L Tracker

The all-seeing eye. Watches every open position, calculates P&L in real time,
and alerts on trim targets, stop losses, and scale in/out signals.

## How it fits

```
Predator scans the market -> finds a setup -> opens a position
  ↓
Gaze stores the position -> polls prices every 5s -> calculates P&L
  ↓
Gaze alerts on trim / stop / scale signals
  ↓
Trading City (3D) renders it all live
```

Gaze is the backend the Trading City visualization talks to:
`GET /api/gaze/positions` and `/api/gaze/closed` come from here.

## Layout

| Folder | Role |
|---|---|
| `position-tracker/` | Open/closed position storage + polling (`tracker.py`, `trader_agent.py`, `trading_router.py`) |
| `pnl-calculator/` | Real-time P&L engine (`calculator.py`) + market analyst (`analyst_agent.py`) |
| `alert-system/` | TTS + sound alerts (`alerts.py`) |
| `risk-monitor/` | Drawdown and daily-loss tracking (`monitor.py`) |
| `dashboard.html` | Orb P&L dashboard UI (5s refresh) |

## API (port :3001)

| Method | Endpoint |
|---|---|
| GET | `/api/gaze/positions` — all open positions with live P&L |
| POST | `/api/gaze/position` — open a position |
| GET | `/api/gaze/pnl/:id` — P&L for one position |
| PATCH | `/api/gaze/position/:id` — update (trailing stop) |
| DELETE | `/api/gaze/position/:id` — close a position |
| GET | `/api/gaze/history` — position history |
| GET | `/api/gaze/status` — overall P&L status |

## Run it

```sh
# entry point
python pnl-calculator/calculator.py
```

Needs a `.env` in the project root with the exchange keys you use
(see "Keys" below). No `.env` is shipped — everyone brings their own.

## Keys (all via environment, never hardcoded)

`ALPACA_API_KEY` / `ALPACA_SECRET_KEY`, `BITUNIX_API_KEY` / `BITUNIX_SECRET_KEY`,
`COINBASE_API_KEY` / `COINBASE_API_SECRET`, `KRAKEN_API_KEY` / `KRAKEN_SECRET_KEY`,
plus optional CoinGecko demo key. Missing keys degrade gracefully — the
affected account just reports "not connected."

## Data files (live state — back these up)

- `position-tracker/data/open-positions.json` — currently open
- `position-tracker/data/closed-positions.json` — history
- `pnl-calculator/data/pnl-history.json` — P&L ledger

## Notes

- Imported 2026-10-03 from the Windows "Sage Reborn" build (`D:/Sage Reborn/voice-os/`); see `ORIGIN.md`.
- Cleanup 2026-10-15: removed `__pycache__/` and stale `.bak` / `.pre-cleanup` position files. Code untouched.
