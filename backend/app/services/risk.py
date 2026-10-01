from __future__ import annotations
import numpy as np


def historical_var_cvar(returns: list[float], confidence: float = 0.95, notional: float = 1_000_000) -> dict[str, float]:
    if not 0.5 < confidence < 0.999:
        raise ValueError("confidence must be between 0.5 and 0.999")
    if notional <= 0:
        raise ValueError("notional must be positive")
    arr = np.asarray(returns, dtype=float)
    if arr.size < 20:
        raise ValueError("at least 20 return observations are required")
    if not np.isfinite(arr).all():
        raise ValueError("returns must contain only finite numbers")

    loss = -arr * notional
    var = float(np.quantile(loss, confidence, method="linear"))
    tail = loss[loss >= var]
    cvar = float(tail.mean()) if tail.size else var
    return {
        "confidence": confidence,
        "notional": notional,
        "var": var,
        "cvar": cvar,
        "observations": int(arr.size),
    }


def pnl_scenarios(delta: float, gamma: float, vega: float, spot: float, spot_shocks: list[float], vol_shocks: list[float]) -> list[dict[str, float]]:
    if spot <= 0:
        raise ValueError("spot must be positive")
    rows: list[dict[str, float]] = []
    for s_shock in spot_shocks:
        d_s = spot * s_shock
        for v_shock in vol_shocks:
            approx_pnl = delta * d_s + 0.5 * gamma * d_s**2 + vega * (v_shock * 100.0)
            rows.append({
                "spot_shock_pct": float(s_shock * 100.0),
                "vol_shock_points": float(v_shock * 100.0),
                "approx_pnl": float(approx_pnl),
            })
    return rows
