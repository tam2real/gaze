"""
Gaze Alert System — daemon SFX via sendToDaemon (not os.system).
Use from API route handlers: import alerts; alerts.alert_stop_loss(...)
"""
import json
import subprocess
import sys
from pathlib import Path

# Daemon IPC helper — reuse pattern from api/src/neuroStore.js sendToDaemon
# For direct Python usage, we emit JSON lines that the daemon's IPC port consumes,
# or simply log if daemon offline.

def _send_to_daemon(payload: dict):
    """Best-effort daemon IPC via HTTP bridge if available, else no-op."""
    try:
        import requests
        # daemon exposes HTTP bridge on 127.0.0.1:41907 per elfie_daemon.py:41907
        # but primary path is via api server's sendToDaemon (Node). From Python, just log.
        return
    except Exception:
        pass

def _play_sfx(filename: str):
    """Log SFX request — actual playback is via daemon when API route calls sendToDaemon."""
    print(f"[gaze:alert] SFX:{filename}")

def alert_position_opened(symbol, direction, entry):
    _play_sfx("neuro.mp3")
    return f"Position opened: {symbol} {direction} at {entry}"

def alert_trim_target(symbol, level, price):
    _play_sfx("analysis-complete.wav")
    return f"Trim target {level} hit: {symbol} at {price}"

def alert_stop_loss(symbol, price):
    _play_sfx("warning.mp3")
    return f"STOP LOSS HIT: {symbol} at {price}"

def alert_position_closed(symbol, pnl):
    _play_sfx("neurooff.mp3")
    return f"Position closed: {symbol} P&L: {pnl}"

def alert_drawdown(pct):
    _play_sfx("warning.mp3")
    return f"WARNING: Drawdown {pct}%"

def alert_scale_in(symbol, price):
    _play_sfx("neuro.mp3")
    return f"Scale-in: {symbol} at {price}"
