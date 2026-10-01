from __future__ import annotations

from dataclasses import dataclass
import math
import numpy as np
from scipy.stats import norm


@dataclass(frozen=True)
class OptionInputs:
    spot: float
    strike: float
    rate: float
    volatility: float
    maturity: float
    dividend_yield: float = 0.0
    option_type: str = "call"

    def validate(self) -> None:
        if self.spot <= 0 or self.strike <= 0:
            raise ValueError("spot and strike must be positive")
        if self.maturity <= 0:
            raise ValueError("maturity must be positive")
        if self.volatility <= 0:
            raise ValueError("volatility must be positive")
        if self.option_type not in {"call", "put"}:
            raise ValueError("option_type must be 'call' or 'put'")


def _d1_d2(x: OptionInputs) -> tuple[float, float]:
    x.validate()
    vol_sqrt_t = x.volatility * math.sqrt(x.maturity)
    d1 = (
        math.log(x.spot / x.strike)
        + (x.rate - x.dividend_yield + 0.5 * x.volatility**2) * x.maturity
    ) / vol_sqrt_t
    d2 = d1 - vol_sqrt_t
    return d1, d2


def black_scholes_price(x: OptionInputs) -> float:
    d1, d2 = _d1_d2(x)
    df_r = math.exp(-x.rate * x.maturity)
    df_q = math.exp(-x.dividend_yield * x.maturity)
    if x.option_type == "call":
        return float(x.spot * df_q * norm.cdf(d1) - x.strike * df_r * norm.cdf(d2))
    return float(x.strike * df_r * norm.cdf(-d2) - x.spot * df_q * norm.cdf(-d1))


def black_scholes_greeks(x: OptionInputs) -> dict[str, float]:
    d1, d2 = _d1_d2(x)
    df_r = math.exp(-x.rate * x.maturity)
    df_q = math.exp(-x.dividend_yield * x.maturity)
    pdf = norm.pdf(d1)

    if x.option_type == "call":
        delta = df_q * norm.cdf(d1)
        theta = (
            -(x.spot * df_q * pdf * x.volatility) / (2 * math.sqrt(x.maturity))
            - x.rate * x.strike * df_r * norm.cdf(d2)
            + x.dividend_yield * x.spot * df_q * norm.cdf(d1)
        )
        rho = x.strike * x.maturity * df_r * norm.cdf(d2)
    else:
        delta = df_q * (norm.cdf(d1) - 1)
        theta = (
            -(x.spot * df_q * pdf * x.volatility) / (2 * math.sqrt(x.maturity))
            + x.rate * x.strike * df_r * norm.cdf(-d2)
            - x.dividend_yield * x.spot * df_q * norm.cdf(-d1)
        )
        rho = -x.strike * x.maturity * df_r * norm.cdf(-d2)

    gamma = df_q * pdf / (x.spot * x.volatility * math.sqrt(x.maturity))
    vega = x.spot * df_q * pdf * math.sqrt(x.maturity)

    return {
        "delta": float(delta),
        "gamma": float(gamma),
        "vega": float(vega / 100.0),  # per 1 vol point
        "theta": float(theta / 365.0),  # per calendar day
        "rho": float(rho / 100.0),  # per 1 rate point
    }


def implied_volatility(
    market_price: float,
    base: OptionInputs,
    lower: float = 1e-4,
    upper: float = 5.0,
    tol: float = 1e-7,
    max_iter: int = 200,
) -> float:
    if market_price <= 0:
        raise ValueError("market_price must be positive")

    low, high = lower, upper
    low_price = black_scholes_price(OptionInputs(**{**base.__dict__, "volatility": low}))
    high_price = black_scholes_price(OptionInputs(**{**base.__dict__, "volatility": high}))
    if not (low_price <= market_price <= high_price):
        raise ValueError("market price is outside the model's implied-volatility search range")

    for _ in range(max_iter):
        mid = 0.5 * (low + high)
        mid_price = black_scholes_price(OptionInputs(**{**base.__dict__, "volatility": mid}))
        if abs(mid_price - market_price) < tol:
            return float(mid)
        if mid_price < market_price:
            low = mid
        else:
            high = mid
    return float(0.5 * (low + high))


def monte_carlo_european(
    x: OptionInputs,
    simulations: int = 100_000,
    seed: int = 42,
) -> dict[str, float]:
    x.validate()
    if simulations < 1_000 or simulations > 2_000_000:
        raise ValueError("simulations must be between 1,000 and 2,000,000")
    rng = np.random.default_rng(seed)
    z = rng.standard_normal(simulations)
    terminal = x.spot * np.exp(
        (x.rate - x.dividend_yield - 0.5 * x.volatility**2) * x.maturity
        + x.volatility * math.sqrt(x.maturity) * z
    )
    if x.option_type == "call":
        payoff = np.maximum(terminal - x.strike, 0.0)
    else:
        payoff = np.maximum(x.strike - terminal, 0.0)
    discounted = np.exp(-x.rate * x.maturity) * payoff
    price = float(np.mean(discounted))
    stderr = float(np.std(discounted, ddof=1) / math.sqrt(simulations))
    return {
        "price": price,
        "standard_error": stderr,
        "ci95_low": price - 1.96 * stderr,
        "ci95_high": price + 1.96 * stderr,
    }


def binomial_american(
    x: OptionInputs,
    steps: int = 300,
) -> float:
    x.validate()
    if steps < 10 or steps > 5000:
        raise ValueError("steps must be between 10 and 5000")
    dt = x.maturity / steps
    u = math.exp(x.volatility * math.sqrt(dt))
    d = 1.0 / u
    growth = math.exp((x.rate - x.dividend_yield) * dt)
    p = (growth - d) / (u - d)
    if not 0.0 < p < 1.0:
        raise ValueError("invalid risk-neutral probability for the selected inputs")
    disc = math.exp(-x.rate * dt)

    j = np.arange(steps + 1)
    spots = x.spot * (u ** (steps - j)) * (d ** j)
    if x.option_type == "call":
        values = np.maximum(spots - x.strike, 0.0)
    else:
        values = np.maximum(x.strike - spots, 0.0)

    for i in range(steps - 1, -1, -1):
        values = disc * (p * values[:-1] + (1 - p) * values[1:])
        j = np.arange(i + 1)
        spots = x.spot * (u ** (i - j)) * (d ** j)
        if x.option_type == "call":
            exercise = np.maximum(spots - x.strike, 0.0)
        else:
            exercise = np.maximum(x.strike - spots, 0.0)
        values = np.maximum(values, exercise)
    return float(values[0])
