# Gaze — P&L Tracker Skill

## What It Does

Watches all open positions. Never misses a movement. Tracks every price change, calculates P&L in real time, and alerts on scale in/out signals.

**In Slime:** Gaze is the all-seeing eye. It watches everything simultaneously. Nothing escapes its sight.

## Trigger

- "What's my P&L"
- "Track my position"
- "Open BTC long at $65,000, size $100, leverage 100x"
- "Close position"
- "Show my positions"

## Subfolders

| Folder | What It Does | Status |
|--------|-------------|--------|
| [position-tracker/](position-tracker/INDEX.md) | Open position storage + polling | BUILT |
| [pnl-calculator/](pnl-calculator/INDEX.md) | Real-time P&L calculation | BUILT |
| [alert-system/](alert-system/INDEX.md) | TTS + sound alerts | BUILT |
| [risk-monitor/](risk-monitor/INDEX.md) | Drawdown, daily loss tracking | BUILT |
| dashboard.html | Orb P&L dashboard UI | BUILT 2026-09-24 |

## What Was Copied

| File | Source | Purpose |
|------|--------|---------|
| trader_agent.py | D:/Sage Reborn/voice-os/agents/ | Alpaca paper trading |
| breakout_prop_agent.py | D:/Sage Reborn/voice-os/agents/ | Breakout Prop agent |
| trading_router.py | D:/Sage Reborn/voice-os/ | Multi-account routing |
| analyst_agent.py | D:/Sage Reborn/voice-os/agents/ | Market analysis |

## What Was Created

| File | Purpose |
|------|---------|
| position-tracker/data/open-positions.json | Open positions storage |
| position-tracker/data/closed-positions.json | Closed position history |
| pnl-calculator/data/pnl-history.json | P&L history |

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/gaze/positions | Get all open positions |
| POST | /api/gaze/position | Add new position |
| GET | /api/gaze/pnl/:id | Get P&L for position |
| PATCH | /api/gaze/position/:id | Update position (trailing stop) |
| DELETE | /api/gaze/position/:id | Close position |
| GET | /api/gaze/history | Position history |
| GET | /api/gaze/status | Overall P&L status |

## How It Executes

**Entry point:** `ultimate skill/gaze/pnl-calculator/calculator.py`

**From voice:** "What's my P&L" → reads open-positions.json → polls live prices via TradingView control layer → calculates P&L → returns summary + TTS alert if trim/stop hit

**From API:** `GET /api/gaze/positions` → returns all open positions with current P&L; `POST /api/gaze/position` → adds new position to tracker

**Depends on:** TradingView control layer (live price feed); `BREAKOUTPROP.md` or broker account for position data; runs on standalone port `:3001`

## P&L Formula

```
P&L = (Current Price - Entry Price) x Position Size x Leverage
```

Example:
- Entry: $65,000
- Current: $65,500
- Size: $100
- Leverage: 100x
- P&L = ($65,500 - $65,000) x $100 x 100 = +$5,000

## Connection to Predator

Predator and Gaze work together:

```
Predator scans market -> finds setup -> opens position
  ↓
Gaze stores position -> polls price every 5 seconds -> calculates P&L
  ↓
Gaze alerts on trim targets, stop loss, scale in/out signals
  ↓
Predator reads Gaze data for daily briefing
```

## Connection to Other Skills

| Skill | Relationship |
|-------|-------------|
| Predator | Gaze provides P&L data to Predator for briefings |
| Great Sage | Great Sage can trigger Gaze to check positions |
| Stomach | Gaze stores position data in Stomach |
| Magic Sense | Gaze provides position data for recap |

## Sound Effects

| Event | Sound | File |
|-------|-------|------|
| Position opened | NEURO | neuro.mp3 |
| Trim target hit | Analysis complete | analysis-complete.wav |
| Scale in signal | Affirmative | affirmative.wav |
| Stop loss hit | KOKU | warning.mp3 |
| Position closed | NEURO OFF | neurooff.mp3 |
| Drawdown warning | KOKU | warning.mp3 |

## Status: BUILT (API + Dashboard)

- Agents: COPIED (trading, breakout prop, routing, analysis)
- Data files: CREATED (open/closed positions, pnl history)
- P&L calculator: BUILT (`pnl-calculator/calculator.py`)
- Alert system: BUILT (`alert-system/alerts.py`)
- HTTP endpoints: BUILT — 7 routes on standalone `:3001` (verified 2026-09-24 open/close cycle)
- Dashboard: BUILT — `gaze/dashboard.html` (orb, cards, risk meter, open/close, 5s refresh)
- Void registration: DONE
- Completion log: `01 - Daily Notes/2026/2026-09-24-gaze-dashboard.md`
