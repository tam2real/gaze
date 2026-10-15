"""
Gaze Position Tracker — open/close/trailing-stop lifecycle.
"""

import json
import uuid
from pathlib import Path
from datetime import datetime, timezone, timedelta

OPEN_POSITIONS_PATH = Path(__file__).parent / "data" / "open-positions.json"
CLOSED_POSITIONS_PATH = Path(__file__).parent / "data" / "closed-positions.json"


def _ny_now():
    """NY 12-hour timestamp (EDT), e.g. "2026-10-06 6:39:11 PM".
    Gaze is the NY ops layer — all trade history and P&L timestamps are local."""
    edt = timezone(timedelta(hours=-4))
    return datetime.now(edt).strftime("%Y-%m-%d %I:%M:%S %p").lstrip("0")


def _utc_iso():
    """UTC ISO timestamp for the JSON file (machine-readable)."""
    return datetime.now(timezone.utc).isoformat()


def load_open():
    if not OPEN_POSITIONS_PATH.exists():
        return {"positions": [], "last_updated": None}
    return json.loads(OPEN_POSITIONS_PATH.read_text(encoding="utf-8"))


def save_open(data):
    data["last_updated"] = _utc_iso()
    OPEN_POSITIONS_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def load_closed():
    if not CLOSED_POSITIONS_PATH.exists():
        return {"positions": [], "last_updated": None}
    return json.loads(CLOSED_POSITIONS_PATH.read_text(encoding="utf-8"))


def save_closed(data):
    data["last_updated"] = _utc_iso()
    CLOSED_POSITIONS_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def open_position(symbol, direction, entry, size, leverage, stop, target):
    data = load_open()
    position = {
        "id": str(uuid.uuid4()),
        "symbol": symbol.upper(),
        "direction": direction,
        "entry": float(entry),
        "size": float(size),
        "leverage": int(leverage) if leverage else 1,
        "stop": float(stop),
        "target": float(target),
        "current_price": float(entry),
        "pnl": 0,
        "pnl_pct": 0,
        "r_multiple": 0,
        "trim_levels": [
            {"level": 1, "price": round(float(entry) + (float(target) - float(entry)) * 0.33, 2), "action": "trim_25%", "hit": False},
            {"level": 2, "price": round(float(entry) + (float(target) - float(entry)) * 0.66, 2), "action": "trim_25%", "hit": False},
            {"level": 3, "price": float(target), "action": "trim_25%", "hit": False},
        ],
        "status": "open",
        "opened_at": _utc_iso(),
        "opened_at_ny": _ny_now(),
        "last_updated": _utc_iso(),
        "last_updated_ny": _ny_now(),
    }
    data["positions"].append(position)
    save_open(data)
    return position


def close_position(position_id, reason="manual", exit_price=None):
    data = load_open()
    closed = load_closed()
    for i, pos in enumerate(data["positions"]):
        if pos["id"] == position_id and pos.get("status") == "open":
            pos["status"] = "closed"
            pos["closed_at"] = _utc_iso()
            pos["closed_at_ny"] = _ny_now()
            pos["close_reason"] = reason

            if exit_price is not None:
                pos["exit_price"] = float(exit_price)
                entry = float(pos["entry"])
                size = float(pos.get("size", 1))
                direction = pos.get("direction", "long")
                ep = float(exit_price)
                if direction == "long":
                    pos["pnl"] = round((ep - entry) * size, 2)
                    pos["pnl_pct"] = round(((ep - entry) / entry) * 100, 2) if entry else 0
                else:
                    pos["pnl"] = round((entry - ep) * size, 2)
                    pos["pnl_pct"] = round(((entry - ep) / entry) * 100, 2) if entry else 0

                # Compute duration in minutes
                try:
                    entry_dt = datetime.fromisoformat(pos["opened_at"])
                    close_dt = datetime.fromisoformat(pos["closed_at"])
                    duration_min = (close_dt - entry_dt).total_seconds() / 60.0
                    pos["duration_minutes"] = round(duration_min, 1)
                except (ValueError, TypeError):
                    pos["duration_minutes"] = None

            closed["positions"].append(pos)
            data["positions"].pop(i)
            save_open(data)
            save_closed(closed)
            return {"success": True, "position": pos}
    return {"success": False, "error": "position not found or not open"}


def trim_position(position_id, pct=25, exit_price=None, level=None):
    """Take profit on part of a position without closing the rest.

    `size` is MARGIN IN DOLLARS, so trimming 25% means releasing 25% of the
    margin. The realised P&L for that slice is banked into `realized_pnl` so it
    survives even if the rest of the position later goes against you.
    """
    data = load_open()
    for pos in data["positions"]:
        if pos["id"] != position_id:
            continue
        margin = float(pos.get("size") or 0)
        if margin <= 0:
            return {"success": False, "error": "nothing to trim"}

        pct = max(0.01, min(100.0, float(pct)))
        cut = margin * (pct / 100.0)
        price = float(exit_price if exit_price is not None else pos.get("current_price") or pos["entry"])
        entry = float(pos["entry"])
        lev = float(pos.get("leverage") or 1)

        coins = margin / entry if entry > 0 else 0
        cut_coins = coins * (pct / 100.0)
        if pos.get("direction") == "short":
            realized = (entry - price) * cut_coins * lev
        else:
            realized = (price - entry) * cut_coins * lev

        pos["size"] = round(margin - cut, 6)
        pos["realized_pnl"] = round(float(pos.get("realized_pnl") or 0) + realized, 2)
        pos["trims_taken"] = int(pos.get("trims_taken") or 0) + 1
        pos["last_updated"] = _utc_iso()
        pos["last_updated_ny"] = _ny_now()

        # Mark the trim level that was reached, if one was named.
        for tl in pos.get("trim_levels") or []:
            if level is not None and tl.get("level") == level:
                tl["hit"] = True
            elif level is None and not tl.get("hit"):
                tl["hit"] = True
                break

        # After the first trim the stop moves to entry — forward only, never back.
        moved = None
        if pos["trims_taken"] == 1 and float(pos.get("stop") or 0) < entry:
            moved = entry
            pos["stop"] = entry

        save_open(data)
        return {"success": True, "trimmed_pct": pct, "realized_pnl": round(realized, 2),
                "remaining_margin": pos["size"], "position": pos,
                "stop_moved_to": moved}
    return {"success": False, "error": "position not found"}


def update_position(position_id, stop=None, target=None, size=None):
    """Edit an open position in place. Only fields provided are changed."""
    data = load_open()
    for pos in data["positions"]:
        if pos["id"] != position_id:
            continue
        if stop is not None:
            pos["stop"] = float(stop)
        if target is not None:
            pos["target"] = float(target)
        if size is not None:
            pos["size"] = float(size)
        pos["last_updated"] = _utc_iso()
        pos["last_updated_ny"] = _ny_now()
        save_open(data)
        return {"success": True, "position": pos}
    return {"success": False, "error": "position not found"}


def update_trailing_stop(position_id, new_stop):
    data = load_open()
    for pos in data["positions"]:
        if pos["id"] == position_id:
            pos["stop"] = float(new_stop)
            pos["last_updated"] = _utc_iso()
            pos["last_updated_ny"] = _ny_now()
            save_open(data)
            return {"success": True, "position": pos}
    return {"success": False, "error": "position not found"}


def get_positions():
    return load_open().get("positions", [])


def get_position(position_id):
    for pos in load_open().get("positions", []):
        if pos["id"] == position_id:
            return pos
    return None


if __name__ == "__main__":
    pos = open_position("BTC", "long", 65000, 0.1, 1, 64000, 67000)
    print(json.dumps(pos, indent=2))
    print(json.dumps(close_position(pos["id"], "test"), indent=2))
