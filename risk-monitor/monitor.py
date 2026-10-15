"""
Gaze Risk Monitor — position-level risk metrics + alert checks.
"""
from pathlib import Path

def get_position_metrics(position, current_price):
    entry = float(position["entry"])
    stop = float(position["stop"])
    size = float(position.get("size", 1))
    risk_per_unit = abs(entry - stop)
    total_risk = risk_per_unit * size
    distance_to_stop = abs(float(current_price) - stop)
    distance_to_stop_pct = (distance_to_stop / entry) * 100 if entry else 0
    drawdown = abs(entry - float(current_price))
    drawdown_pct = (drawdown / risk_per_unit) * 100 if risk_per_unit else 0
    return {
        "distance_to_stop": round(distance_to_stop, 2),
        "distance_to_stop_pct": round(distance_to_stop_pct, 2),
        "drawdown": round(drawdown, 2),
        "drawdown_pct": round(drawdown_pct, 2),
        "risk_amount": round(total_risk, 2),
        "entry": entry,
        "stop": stop,
        "current": float(current_price),
    }

def check_alerts(position, current_price):
    entry = float(position["entry"])
    metrics = get_position_metrics(position, current_price)
    alerts = []
    if metrics["distance_to_stop_pct"] < 1:
        alerts.append({"type": "critical", "message": f"Stop loss within 1% — {position.get('symbol')} at {current_price}, stop {position.get('stop')}"})
    if metrics["drawdown_pct"] > 50:
        alerts.append({"type": "warning", "message": f"Drawdown {metrics['drawdown_pct']:.1f}% of max risk — {position.get('symbol')}"})
    for level in position.get("trim_levels", []):
        if level.get("hit"):
            continue
        lvl_price = float(level.get("price", 0))
        if abs(float(current_price) - lvl_price) / entry * 100 < 0.5 if entry else False:
            alerts.append({"type": "info", "message": f"Trim level {level.get('level')} approaching — {position.get('symbol')} at {lvl_price}"})
    # Chart divergence vs TradingView (graceful skip if wrapper offline)
    try:
        import requests as _rq
        r = _rq.post(
            "http://localhost:9233/mcp",
            json={"tool": "chart_get_state", "args": {"symbol": position.get("symbol", "")}},
            timeout=2,
        )
        state = r.json()
        tv_price = state.get("price") if isinstance(state, dict) else None
        if tv_price:
            div = check_chart_divergence(float(current_price), float(tv_price))
            if div.get("diverged"):
                alerts.append({"type": "warning", "message": div.get("alert", "chart divergence")})
    except Exception:
        pass
    return {"metrics": metrics, "alerts": alerts}

def check_chart_divergence(cg_price: float, tv_price: float, threshold: float = 0.05):
    if not cg_price or not tv_price:
        return {"diverged": False}
    div = abs(cg_price - tv_price) / cg_price if cg_price else 0
    if div > threshold:
        return {"diverged": True, "divergence_pct": round(div * 100, 2), "alert": f"Price divergence {div*100:.2f}% CG {cg_price} vs TV {tv_price}"}
    return {"diverged": False, "divergence_pct": round(div * 100, 2)}
