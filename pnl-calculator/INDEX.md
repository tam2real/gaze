# P&L Calculator — Gaze Subfolder

## What It Does

Calculates real-time P&L for all open positions. Polls current prices every 5 seconds and updates P&L values.

## P&L Formula

```
P&L = (Current Price - Entry Price) x Position Size x Leverage
```

## Example

- Entry: $65,000
- Current: $65,500
- Size: $100
- Leverage: 100x
- P&L = ($65,500 - $65,000) x $100 x 100 = +$5,000

## Data Files

| File | Purpose |
|------|---------|
| pnl-history.json | Historical P&L snapshots |

## Copied Files

| File | Source | Purpose |
|------|--------|---------|
| analyst_agent.py | D:/Sage Reborn/voice-os/agents/ | Market analysis, price fetching |

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/gaze/pnl/:id | Get P&L for position |
| GET | /api/gaze/pnl | Get P&L for all positions |
| GET | /api/gaze/status | Overall P&L status |

## Output Format

```json
{
  "positions": [
    {
      "id": "uuid",
      "symbol": "BTC",
      "entry": 65000,
      "current": 65500,
      "pnl": 5000,
      "pnl_pct": 0.77,
      "r_multiple": 0.5
    }
  ],
  "total_pnl": 5000,
  "total_pnl_pct": 0.5
}
```

## Status: PLANNED

Formula defined. Calculator logic NOT built. Price polling NOT built.
