"""
Gaze P&L Calculator — batch price poll + correct P&L/R-multiple + history rotation.

Price source is Bitunix (real futures, no key). CoinGecko is fallback only; its
free tier rate-limits this IP, which previously froze P&L at stale values.
"""
import json
import requests
from pathlib import Path
from datetime import datetime, timezone, timedelta

BITUNX_URL = "https://fapi.bitunix.com/api/v1/futures/market/tickers"

OPEN_POSITIONS_PATH = Path(__file__).parent.parent / "position-tracker" / "data" / "open-positions.json"
PNL_HISTORY_PATH = Path(__file__).parent / "data" / "pnl-history.json"

def _ny_now():
    """NY 12-hour timestamp (EDT), e.g. "2026-10-06 6:39:11 PM".
    Gaze is the NY ops layer — all trade history and P&L timestamps are local."""
    edt = timezone(timedelta(hours=-4))
    return datetime.now(edt).strftime("%Y-%m-%d %I:%M:%S %p").lstrip("0")

def _utc_iso():
    """UTC ISO timestamp for the JSON file (machine-readable)."""
    return datetime.now(timezone.utc).isoformat()


MAX_HISTORY = 1000

CG_MAP = {
    "BTC": "bitcoin", "ETH": "ethereum", "SOL": "solana", "BNB": "binancecoin",
    "XRP": "ripple", "DOGE": "dogecoin", "ADA": "cardano", "AVAX": "avalanche-2",
    "LINK": "chainlink", "MATIC": "matic-network",
}
CG_URL = "https://api.coingecko.com/api/v3/simple/price"

def load_positions():
    if not OPEN_POSITIONS_PATH.exists():
        return {"positions": []}
    return json.loads(OPEN_POSITIONS_PATH.read_text(encoding="utf-8"))

def save_positions(data):
    data["last_updated"] = _utc_iso()
    OPEN_POSITIONS_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

def fetch_batch_prices(symbols):
    """Fetch prices. Bitunix first (real futures, no key, no rate limit), CoinGecko second.

    CoinGecko's free tier returns HTTP 429 from this IP. The old code let that
    raise, update_all_pnl() caught it and printed a warning, then every position
    was skipped because price was None — so P&L silently froze at its last value
    instead of marking to market. Bitunix needs no key and has no such limit.
    """
    symbols = [str(s).strip().upper() for s in symbols]
    pairs = {"BTC": "BTCUSDT", "ETH": "ETHUSDT", "SOL": "SOLUSDT",
             "BNB": "BNBUSDT", "XRP": "XRPUSDT", "DOGE": "DOGEUSDT",
             "ADA": "ADAUSDT", "AVAX": "AVAXUSDT", "LINK": "LINKUSDT",
             "MATIC": "MATICUSDT"}
    wanted = [s for s in symbols if s in pairs]
    if wanted:
        try:
            r = requests.get(BITUNX_URL, params={"symbol": pairs[wanted[0]]}, timeout=10)
            r.raise_for_status()
            rows = r.json().get("data") or []
            by_pair = {row.get("symbol"): row for row in rows if isinstance(row, dict)}
            out = {}
            for base in wanted:
                row = by_pair.get(pairs[base])
                if row:
                    px = float(row.get("lastPrice") or 0)
                    if px > 0:
                        out[base] = px
            if out:
                return out
        except Exception as e:
            print(f"[calculator] bitunix fetch failed, trying coingecko: {e}")

    ids = ",".join(CG_MAP[s] for s in symbols if s in CG_MAP)
    if not ids:
        return {}
    r = requests.get(CG_URL, params={"ids": ids, "vs_currencies": "usd"}, timeout=8)
    r.raise_for_status()
    data = r.json()
    inv = {v: k for k, v in CG_MAP.items()}
    return {inv[cg_id]: vals.get("usd") for cg_id, vals in data.items() if cg_id in inv}

def calculate_pnl(position, current_price):
    """P&L for one position.

    SIZE is DOLLARS of margin — the same number you type into the form. The
    calculator converts it to coins internally:

        coins = margin / entry

    The old code treated `size` as a coin count, so typing 2000 meant 2000 BTC.
    On a 10x short that showed a loss of $2,806,400 on a position that never
    risked more than a few hundred dollars.
    """
    entry = float(position["entry"])
    margin = float(position.get("size", 1))          # dollars you put up
    size = (margin / entry) if entry > 0 else margin  # convert to coins once
    leverage = float(position.get("leverage", 1))
    direction = position.get("direction", "long")
    stop = float(position.get("stop", entry * 0.97))
    if direction == "long":
        pnl = (current_price - entry) * size * leverage
        pnl_pct = ((current_price - entry) / entry) * 100 * leverage if entry else 0
    else:
        pnl = (entry - current_price) * size * leverage
        pnl_pct = ((entry - current_price) / entry) * 100 * leverage if entry else 0
    risk_per_unit = abs(entry - stop)
    # Leverage scales the P&L above, so it must scale the risk denominator too.
    # Without it, r_multiple came out inflated by exactly the leverage factor —
    # a 2.12R trade on a 10x position was being reported as 21.16R.
    total_risk = risk_per_unit * size * leverage if risk_per_unit else 0
    r_multiple = (pnl / total_risk) if total_risk else 0
    return {
        "symbol": position["symbol"],
        "entry": entry,
        "current": current_price,
        "pnl": round(pnl, 2),
        "pnl_pct": round(pnl_pct, 2),
        "r_multiple": round(r_multiple, 2),
        "risk_amount": round(total_risk, 2),
        "timestamp": _utc_iso(),
    }

def update_all_pnl():
    positions_data = load_positions()
    positions = positions_data.get("positions", [])
    open_positions = [p for p in positions if p.get("status") == "open"]
    if not open_positions:
        return {"positions": [], "total_pnl": 0, "total_pnl_pct": 0, "count": 0}
    symbols = list({p["symbol"] for p in open_positions})
    prices = {}
    try:
        prices = fetch_batch_prices(symbols)
    except Exception as e:
        print(f"[calculator] price fetch failed: {e}")
    results = []
    for pos in open_positions:
        price = prices.get(pos["symbol"])
        if price is None:
            continue
        # TV price validation (graceful skip if wrapper offline) — no extra CG call
        try:
            tv_price = _tv_state_price(pos["symbol"])
            if tv_price and price and abs(tv_price - price) / price > 0.02:
                print(f"[calculator] divergence {pos['symbol']}: CG {price} vs TV {tv_price} >2%")
        except Exception:
            pass
        pnl = calculate_pnl(pos, price)
        pos["current_price"] = price
        pos["pnl"] = pnl["pnl"]
        pos["pnl_pct"] = pnl["pnl_pct"]
        pos["r_multiple"] = pnl["r_multiple"]
        pos["last_updated"] = _utc_iso()
        results.append(pnl)
    save_positions(positions_data)
    # history with rotation
    history = {"history": []}
    if PNL_HISTORY_PATH.exists():
        try:
            history = json.loads(PNL_HISTORY_PATH.read_text(encoding="utf-8"))
        except Exception:
            history = {"history": []}
    history["history"].append({"timestamp": _utc_iso(), "positions": results, "total_pnl": round(sum(r["pnl"] for r in results), 2)})
    history["history"] = history["history"][-MAX_HISTORY:]
    PNL_HISTORY_PATH.write_text(json.dumps(history, indent=2, ensure_ascii=False), encoding="utf-8")
    return {
        "positions": results,
        "total_pnl": round(sum(r["pnl"] for r in results), 2),
        "total_pnl_pct": round(sum(r["pnl_pct"] for r in results), 2),
        "count": len(results),
        "timestamp": _utc_iso(),
    }

async def get_price_from_tradingview(symbol: str):
    try:
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "tradingview"))
        from tv_bridge import tv_set_symbol, tv_get_state
        await tv_set_symbol(symbol)
        import asyncio
        await asyncio.sleep(1)
        state = await tv_get_state()
        return state.get("price") if isinstance(state, dict) else None
    except Exception:
        return None

def _tv_state_price(symbol: str):
    import requests as _rq
    r = _rq.post(
        "http://localhost:9233/mcp",
        json={"tool": "chart_get_state", "args": {"symbol": symbol}},
        timeout=2,
    )
    state = r.json()
    if isinstance(state, dict):
        p = state.get("price")
        return float(p) if p is not None else None
    return None

def get_price_with_tv_validation(symbol: str):
    cg_price = fetch_batch_prices([symbol]).get(symbol)
    try:
        tv_price = _tv_state_price(symbol)
        if tv_price and cg_price and abs(tv_price - cg_price) / cg_price > 0.02:
            print(f"[calculator] price divergence {symbol}: CG {cg_price} vs TV {tv_price} >2%")
    except Exception:
        pass
    return cg_price

if __name__ == "__main__":
    print(json.dumps(update_all_pnl(), indent=2))

# Background poller for live P&L updates
_poller_thread = None
_poller_stop = None

def _background_poller(interval=5):
    """Run update_all_pnl() every `interval` seconds in background thread."""
    import threading
    global _poller_stop
    _poller_stop = threading.Event()
    while not _poller_stop.wait(interval):
        try:
            update_all_pnl()
        except Exception as e:
            print(f"[calculator] background poll error: {e}")

def start_background_poller(interval=5):
    """Start the background P&L poller thread. Call once at startup."""
    global _poller_thread
    if _poller_thread and _poller_thread.is_alive():
        return
    import threading
    _poller_thread = threading.Thread(target=_background_poller, args=(interval,), daemon=True, name="gaze-pnl-poller")
    _poller_thread.start()
    print(f"[calculator] background poller started (every {interval}s)")

def stop_background_poller():
    """Stop the background P&L poller."""
    global _poller_stop
    if _poller_stop:
        _poller_stop.set()
    print("[calculator] background poller stopped")
