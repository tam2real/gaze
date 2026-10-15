# Alert System — Gaze Subfolder

## What It Does

Sends TTS and sound alerts for position events. Alerts fire when prices hit trim targets, stop loss, or scale-in signals.

## Alert Types

| Alert | Trigger | Sound |
|-------|---------|-------|
| Position opened | New position added | NEURO (neuro.mp3) |
| Trim target hit | Price reaches trim level | Analysis complete (analysis-complete.wav) |
| Scale in signal | Higher low confirmed | Affirmative (affirmative.wav) |
| Stop loss hit | Price reaches stop | KOKU (warning.mp3) |
| Position closed | Position closed | NEURO OFF (neurooff.mp3) |
| Drawdown warning | Drawdown exceeds threshold | KOKU (warning.mp3) |

## Sound Files

All sound files are in `D:/Sage Reborn/elfie-assistant/daemon/` (SFX) and `D:/Sage Reborn/sounds/states/` (voice states).

## Alert Delivery

1. TTS speaks alert text via Fish Audio (primary) or Edge TTS (fallback)
2. Sound effect plays via daemon
3. DexView panel updates with alert status

## Status: PLANNED

Alert types defined. Delivery logic NOT built.
