# Position Tracker — Gaze Subfolder

## What It Does

Stores open positions and manages the position lifecycle. Each position tracks symbol, direction, entry, size, leverage, stop loss, and trim targets.

## Data Files

| File | Purpose |
|------|---------|
| open-positions.json | Currently open positions |
| closed-positions.json | Closed position history |

## Position Schema

```json
{
  "id": "uuid",
  "symbol": "BTC",
  "direction": "long",
  "entry": 65000,
  "size": 100,
  "leverage": 100,
  "stop": 64000,
  "target": 67000,
  "trim_levels": [
    {"level": 1, "price": 66000, "action": "trim_25%"},
    {"level": 2, "price": 67000, "action": "trim_25%"},
    {"level": 3, "price": 68000, "action": "trim_25%"}
  ],
  "status": "open",
  "opened_at": "2026-09-24T08:00:00Z",
  "last_updated": "2026-09-24T08:00:00Z"
}
```

## Copied Files

| File | Source | Purpose |
|------|--------|---------|
| trader_agent.py | D:/Sage Reborn/voice-os/agents/ | Alpaca paper trading |
| breakout_prop_agent.py | D:/Sage Reborn/voice-os/agents/ | Breakout Prop agent |
| trading_router.py | D:/Sage Reborn/voice-os/ | Multi-account routing |

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/gaze/positions | List all open positions |
| POST | /api/gaze/position | Open new position |
| GET | /api/gaze/position/:id | Get single position |
| PATCH | /api/gaze/position/:id | Update position (trailing stop) |
| DELETE | /api/gaze/position/:id | Close position |

## Status: PARTIALLY BUILT

Data files created. Position tracker logic NOT built. Agents copied.
