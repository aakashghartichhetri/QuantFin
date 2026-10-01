from __future__ import annotations
import numpy as np


def buffered_note_payoff(
    initial_spot: float,
    terminal_spot: float,
    notional: float = 1000.0,
    upside_participation: float = 1.2,
    buffer: float = 0.15,
    cap: float | None = 0.30,
) -> float:
    if initial_spot <= 0 or terminal_spot < 0 or notional <= 0:
        raise ValueError("invalid price or notional input")
    if not 0 <= buffer < 1:
        raise ValueError("buffer must be in [0, 1)")
    if upside_participation < 0:
        raise ValueError("upside participation must be non-negative")

    r = terminal_spot / initial_spot - 1.0
    if r >= 0:
        product_return = upside_participation * r
        if cap is not None:
            product_return = min(product_return, cap)
    elif r >= -buffer:
        product_return = 0.0
    else:
        product_return = r + buffer
    return float(notional * (1.0 + product_return))


def buffered_note_curve(
    initial_spot: float,
    terminal_min: float,
    terminal_max: float,
    points: int,
    notional: float,
    upside_participation: float,
    buffer: float,
    cap: float | None,
) -> list[dict[str, float]]:
    if points < 10 or points > 1000:
        raise ValueError("points must be between 10 and 1000")
    terminals = np.linspace(terminal_min, terminal_max, points)
    rows = []
    for t in terminals:
        payoff = buffered_note_payoff(
            initial_spot=initial_spot,
            terminal_spot=float(t),
            notional=notional,
            upside_participation=upside_participation,
            buffer=buffer,
            cap=cap,
        )
        rows.append({
            "terminal_spot": float(t),
            "underlying_return_pct": float((t / initial_spot - 1.0) * 100.0),
            "redemption_value": payoff,
            "note_return_pct": float((payoff / notional - 1.0) * 100.0),
        })
    return rows


def price_autocallable_gbm(
    initial_spot: float,
    rate: float,
    volatility: float,
    maturity: float = 1.0,
    observations: int = 4,
    autocall_barrier: float = 1.0,
    protection_barrier: float = 0.70,
    coupon_per_period: float = 0.025,
    notional: float = 1000.0,
    simulations: int = 100_000,
    seed: int = 42,
) -> dict[str, float]:
    """Price a path-dependent autocallable under constant-volatility GBM.

    Terms:
    - At each equally spaced observation, if S_t >= autocall_barrier * S0,
      redeem notional plus coupon_per_period * observation_number.
    - If never called and final S_T >= protection_barrier * S0, redeem notional.
    - Otherwise redeem notional * S_T / S0 (downside participation).

    Model scope excludes smile/skew, dividends, issuer credit,
    coupon memory, funding spread, transaction costs, or discrete hedging.
    """
    if initial_spot <= 0 or notional <= 0:
        raise ValueError("initial_spot and notional must be positive")
    if volatility <= 0 or maturity <= 0:
        raise ValueError("volatility and maturity must be positive")
    if observations < 1 or observations > 24:
        raise ValueError("observations must be between 1 and 24")
    if not 0 < autocall_barrier <= 2.0:
        raise ValueError("autocall_barrier must be in (0, 2]")
    if not 0 < protection_barrier <= 1.0:
        raise ValueError("protection_barrier must be in (0, 1]")
    if coupon_per_period < 0:
        raise ValueError("coupon_per_period must be non-negative")
    if simulations < 1_000 or simulations > 1_000_000:
        raise ValueError("simulations must be between 1,000 and 1,000,000")

    rng = np.random.default_rng(seed)
    dt = maturity / observations
    z = rng.standard_normal((simulations, observations))
    log_steps = (rate - 0.5 * volatility**2) * dt + volatility * np.sqrt(dt) * z
    paths = initial_spot * np.exp(np.cumsum(log_steps, axis=1))

    called = np.zeros(simulations, dtype=bool)
    redemption_time = np.full(simulations, maturity, dtype=float)
    cashflow = np.zeros(simulations, dtype=float)

    barrier_level = autocall_barrier * initial_spot
    for obs_idx in range(observations):
        hit = (~called) & (paths[:, obs_idx] >= barrier_level)
        if np.any(hit):
            k = obs_idx + 1
            t = k * dt
            cashflow[hit] = notional * (1.0 + coupon_per_period * k)
            redemption_time[hit] = t
            called[hit] = True

    survivors = ~called
    terminal = paths[:, -1]
    protected = survivors & (terminal >= protection_barrier * initial_spot)
    cashflow[protected] = notional

    loss_paths = survivors & ~protected
    cashflow[loss_paths] = notional * (terminal[loss_paths] / initial_spot)

    discounted = cashflow * np.exp(-rate * redemption_time)
    price = float(np.mean(discounted))
    stderr = float(np.std(discounted, ddof=1) / np.sqrt(simulations))

    return {
        "present_value": price,
        "standard_error": stderr,
        "autocall_probability": float(np.mean(called)),
        "capital_loss_probability": float(np.mean(loss_paths)),
        "expected_redemption_years": float(np.mean(redemption_time)),
        "mean_terminal_spot": float(np.mean(terminal)),
    }
