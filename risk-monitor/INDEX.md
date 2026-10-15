# Risk Monitor — Gaze Subfolder

## What It Does

Monitors position-level risk metrics. Tracks drawdown, distance to stop, and time in position.

## Metrics Tracked

| Metric | Description |
|--------|-------------|
| Position drawdown | How far current price is from entry |
| Distance to stop | How far current price is from stop loss |
| Distance to trim | How far current price is from next trim target |
| Risk/reward ratio | Current R:R based on entry and stop |
| Time in position | How long position has been open |

## Alert Thresholds

| Threshold | Action |
|-----------|--------|
| Stop loss within 1% | Warning alert |
| Trim target within 0.5% | Info alert |
| Position drawdown exceeds 50% of max risk | Critical alert |

## Data Files

| File | Purpose |
|------|---------|
| risk-metrics.json | Current risk per position |

## Status: PLANNED

Metrics defined. Monitoring logic NOT built.
