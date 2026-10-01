from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.services.pricing import OptionInputs, black_scholes_price  # noqa: E402
from app.services.structured import buffered_note_curve  # noqa: E402

REPORT_DIR = ROOT / "reports"
REPORT_DIR.mkdir(exist_ok=True)

# Buffered-note payoff profile
curve = buffered_note_curve(
    initial_spot=100,
    terminal_min=40,
    terminal_max=160,
    points=241,
    notional=1000,
    upside_participation=1.2,
    buffer=0.15,
    cap=0.30,
)
underlying_returns = [row["underlying_return_pct"] for row in curve]
note_returns = [row["note_return_pct"] for row in curve]

plt.figure(figsize=(8, 4.8))
plt.plot(underlying_returns, note_returns, label="Buffered note")
plt.plot(underlying_returns, underlying_returns, linestyle="--", label="Underlying")
plt.axhline(0, linewidth=0.8)
plt.axvline(0, linewidth=0.8)
plt.xlabel("Underlying return (%)")
plt.ylabel("Investor return (%)")
plt.title("Buffered Equity Note Payoff Profile")
plt.legend()
plt.tight_layout()
plt.savefig(REPORT_DIR / "buffered_note_payoff_profile.png", dpi=160)
plt.close()

# European-call sensitivity to spot and volatility
spots = np.linspace(70, 130, 61)
volatilities = [0.10, 0.20, 0.30, 0.40]

plt.figure(figsize=(8, 4.8))
for volatility in volatilities:
    prices = [
        black_scholes_price(
            OptionInputs(
                spot=float(spot),
                strike=100,
                rate=0.05,
                volatility=volatility,
                maturity=1.0,
                option_type="call",
            )
        )
        for spot in spots
    ]
    plt.plot(spots, prices, label=f"Vol {volatility:.0%}")

plt.xlabel("Spot")
plt.ylabel("Call value")
plt.title("European Call Sensitivity to Spot and Volatility")
plt.legend()
plt.tight_layout()
plt.savefig(REPORT_DIR / "european_option_sensitivity.png", dpi=160)
plt.close()

print(f"Analytics reports written to: {REPORT_DIR}")
