from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.services.pricing import (  # noqa: E402
    OptionInputs,
    binomial_american,
    black_scholes_greeks,
    black_scholes_price,
    implied_volatility,
    monte_carlo_european,
)
from app.services.risk import historical_var_cvar  # noqa: E402
from app.services.structured import (  # noqa: E402
    buffered_note_payoff,
    price_autocallable_gbm,
)

VALIDATION_DATA = ROOT / "data" / "validation" / "market_returns_validation.csv"
REPORT_PATH = ROOT / "reports" / "model_validation_summary.txt"


def build_validation_report() -> str:
    option = OptionInputs(
        spot=100,
        strike=100,
        rate=0.05,
        volatility=0.20,
        maturity=1.0,
        option_type="call",
    )
    black_scholes = black_scholes_price(option)
    greeks = black_scholes_greeks(option)
    monte_carlo = monte_carlo_european(option, simulations=100_000, seed=42)
    implied_vol = implied_volatility(black_scholes, option)

    american_put = OptionInputs(
        spot=100,
        strike=105,
        rate=0.05,
        volatility=0.25,
        maturity=1.0,
        option_type="put",
    )
    american_value = binomial_american(american_put, steps=500)

    returns_df = pd.read_csv(VALIDATION_DATA)
    returns = returns_df["return"].dropna().astype(float).tolist()
    risk = historical_var_cvar(returns, confidence=0.95, notional=1_000_000)

    buffered_redemption = buffered_note_payoff(
        100,
        80,
        notional=1000,
        upside_participation=1.2,
        buffer=0.15,
        cap=0.30,
    )
    autocall = price_autocallable_gbm(
        initial_spot=100,
        rate=0.03,
        volatility=0.20,
        observations=4,
        autocall_barrier=1.0,
        protection_barrier=0.70,
        coupon_per_period=0.025,
        notional=1000,
        simulations=100_000,
        seed=42,
    )

    lines = [
        "QuantFin Model Validation Summary",
        "=================================",
        f"Black-Scholes call value: {black_scholes:.4f}",
        f"Monte Carlo call value:   {monte_carlo['price']:.4f}",
        f"Monte Carlo 95% interval half-width: {1.96 * monte_carlo['standard_error']:.4f}",
        f"Implied-volatility round trip: {implied_vol:.4%}",
        f"Greeks: { {k: round(v, 6) for k, v in greeks.items()} }",
        f"American put value (binomial): {american_value:.4f}",
        f"95% historical VaR: ${risk['var']:,.0f}",
        f"95% historical CVaR: ${risk['cvar']:,.0f}",
        f"Validation return observations: {risk['observations']}",
        f"Buffered-note redemption at S_T=80: ${buffered_redemption:,.2f}",
        f"Autocallable present value: ${autocall['present_value']:,.2f}",
        f"Autocall probability: {autocall['autocall_probability']:.1%}",
        f"Capital-loss probability: {autocall['capital_loss_probability']:.1%}",
        f"Expected redemption time: {autocall['expected_redemption_years']:.2f} years",
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    report = build_validation_report()
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(report, encoding="utf-8")
    print(report, end="")
    print(f"\nValidation report written to: {REPORT_PATH}")


if __name__ == "__main__":
    main()
