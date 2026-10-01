from __future__ import annotations

import os
from pathlib import Path

import pandas as pd
import requests
import streamlit as st

API = os.getenv("API_URL", "http://localhost:8000")
VALIDATION_DATA = Path(os.getenv("VALIDATION_DATA", "/app/data/market_returns_validation.csv"))

st.set_page_config(page_title="QuantFin Analytics", page_icon="📈", layout="wide")
st.title("QuantFin Structured Products Analytics")
st.caption(
    "Equity-derivatives pricing, volatility analysis, market risk, and structured-product analytics. "
    "Research implementation — not approved for live trading or client valuation."
)


def post(path: str, payload: dict):
    try:
        response = requests.post(f"{API}{path}", json=payload, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as exc:
        st.error(f"API request failed: {exc}")
        return None


def load_validation_returns() -> list[float]:
    if not VALIDATION_DATA.exists():
        return []
    frame = pd.read_csv(VALIDATION_DATA)
    if "return" not in frame.columns:
        return []
    return frame["return"].dropna().astype(float).tolist()


tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["Option Pricing", "Implied Volatility", "Market Risk", "Buffered Note", "Autocallable"]
)

with tab1:
    c1, c2, c3 = st.columns(3)
    with c1:
        spot = st.number_input("Spot", 1.0, 10000.0, 100.0, 1.0)
        strike = st.number_input("Strike", 1.0, 10000.0, 100.0, 1.0)
        option_type = st.selectbox("Option type", ["call", "put"])
    with c2:
        maturity = st.number_input("Maturity (years)", 0.01, 30.0, 1.0, 0.05)
        rate = st.number_input("Risk-free rate", -0.10, 0.50, 0.05, 0.005, format="%.3f")
        dividend_yield = st.number_input("Dividend yield", 0.0, 0.25, 0.0, 0.005, format="%.3f")
    with c3:
        volatility = st.number_input("Volatility", 0.01, 3.0, 0.20, 0.01, format="%.2f")
        simulations = st.number_input("Monte Carlo simulations", 1000, 1000000, 100000, 1000)

    option_payload = {
        "spot": spot,
        "strike": strike,
        "rate": rate,
        "volatility": volatility,
        "maturity": maturity,
        "dividend_yield": dividend_yield,
        "option_type": option_type,
    }
    if st.button("Price option", type="primary"):
        black_scholes = post("/pricing/black-scholes", option_payload)
        monte_carlo = post(
            "/pricing/monte-carlo",
            {**option_payload, "simulations": int(simulations), "seed": 42},
        )
        if black_scholes and monte_carlo:
            m1, m2, m3 = st.columns(3)
            m1.metric("Black-Scholes", f"${black_scholes['price']:.4f}")
            m2.metric("Monte Carlo", f"${monte_carlo['price']:.4f}")
            m3.metric("MC standard error", f"${monte_carlo['standard_error']:.4f}")
            st.subheader("Greeks")
            st.dataframe(pd.DataFrame([black_scholes["greeks"]]), use_container_width=True)

with tab2:
    st.write("Solve for the volatility that reproduces an observed option premium.")
    c1, c2 = st.columns(2)
    with c1:
        market_price = st.number_input("Observed option price", 0.01, 10000.0, 10.45, 0.1)
        iv_spot = st.number_input("IV spot", 1.0, 10000.0, 100.0, 1.0)
        iv_strike = st.number_input("IV strike", 1.0, 10000.0, 100.0, 1.0)
    with c2:
        iv_rate = st.number_input("IV rate", -0.10, 0.50, 0.05, 0.005, format="%.3f")
        iv_maturity = st.number_input("IV maturity", 0.01, 30.0, 1.0, 0.05)
        iv_type = st.selectbox("IV option type", ["call", "put"])
    if st.button("Solve implied volatility"):
        result = post(
            "/volatility/implied",
            {
                "market_price": market_price,
                "spot": iv_spot,
                "strike": iv_strike,
                "rate": iv_rate,
                "maturity": iv_maturity,
                "dividend_yield": 0.0,
                "option_type": iv_type,
            },
        )
        if result:
            st.metric("Implied volatility", f"{result['implied_volatility'] * 100:.2f}%")

with tab3:
    st.write("Upload a return series or use the packaged validation dataset for historical VaR/CVaR analysis.")
    confidence = st.slider("Confidence", 0.90, 0.99, 0.95, 0.01)
    notional = st.number_input("Portfolio notional", 1000.0, 100000000.0, 1000000.0, 10000.0)
    uploaded = st.file_uploader("CSV with a 'return' column", type=["csv"])

    if uploaded:
        uploaded_frame = pd.read_csv(uploaded)
        returns = (
            uploaded_frame["return"].dropna().astype(float).tolist()
            if "return" in uploaded_frame.columns
            else []
        )
        data_source = "Uploaded return series"
    else:
        returns = load_validation_returns()
        data_source = "Packaged validation dataset"

    if not returns:
        st.warning("No valid return observations are available.")
    elif st.button("Calculate VaR / CVaR"):
        result = post(
            "/risk/historical-var",
            {"returns": returns, "confidence": confidence, "notional": notional},
        )
        if result:
            left, right = st.columns(2)
            left.metric("Historical VaR", f"${result['var']:,.0f}")
            right.metric("Historical CVaR", f"${result['cvar']:,.0f}")
            st.caption(f"{data_source} · {result['observations']} observations")

with tab4:
    st.write("Analyze a buffered equity note with configurable downside protection, upside participation, and cap terms.")
    c1, c2, c3 = st.columns(3)
    with c1:
        initial_spot = st.number_input("Initial underlying", 1.0, 10000.0, 100.0, 1.0)
        buffer = st.slider("Downside buffer", 0.0, 0.50, 0.15, 0.01)
    with c2:
        participation = st.slider("Upside participation", 0.0, 3.0, 1.2, 0.05)
        cap = st.slider("Upside cap", 0.0, 1.0, 0.30, 0.01)
    with c3:
        note_notional = st.number_input("Note notional", 100.0, 1000000.0, 1000.0, 100.0)

    if st.button("Generate payoff profile"):
        result = post(
            "/structured/buffered-note",
            {
                "initial_spot": initial_spot,
                "terminal_min": 0.4 * initial_spot,
                "terminal_max": 1.6 * initial_spot,
                "points": 121,
                "notional": note_notional,
                "upside_participation": participation,
                "buffer": buffer,
                "cap": cap,
            },
        )
        if result:
            payoff_frame = pd.DataFrame(result["curve"])
            st.line_chart(payoff_frame.set_index("underlying_return_pct")["note_return_pct"])
            st.dataframe(payoff_frame.iloc[::12], use_container_width=True)

with tab5:
    st.write("Price a path-dependent autocallable under a constant-volatility geometric Brownian motion framework.")
    c1, c2, c3 = st.columns(3)
    with c1:
        ac_initial_spot = st.number_input("Autocall initial spot", 1.0, 10000.0, 100.0, 1.0)
        ac_rate = st.number_input("Autocall risk-free rate", -0.10, 0.50, 0.03, 0.005, format="%.3f")
        ac_volatility = st.number_input("Autocall volatility", 0.01, 3.0, 0.20, 0.01)
    with c2:
        autocall_barrier = st.slider("Autocall barrier (% of initial)", 0.70, 1.30, 1.00, 0.01)
        protection_barrier = st.slider("Protection barrier (% of initial)", 0.40, 1.00, 0.70, 0.01)
        coupon = st.slider("Coupon per observation", 0.0, 0.10, 0.025, 0.005)
    with c3:
        observations = st.selectbox("Observations per year", [1, 2, 4, 12], index=2)
        autocall_notional = st.number_input("Autocall notional", 100.0, 1000000.0, 1000.0, 100.0)
        autocall_simulations = st.number_input("Autocall simulations", 1000, 500000, 100000, 1000)

    if st.button("Price autocallable"):
        result = post(
            "/structured/autocallable",
            {
                "initial_spot": ac_initial_spot,
                "rate": ac_rate,
                "volatility": ac_volatility,
                "maturity": 1.0,
                "observations": int(observations),
                "autocall_barrier": autocall_barrier,
                "protection_barrier": protection_barrier,
                "coupon_per_period": coupon,
                "notional": autocall_notional,
                "simulations": int(autocall_simulations),
                "seed": 42,
            },
        )
        if result:
            m1, m2, m3 = st.columns(3)
            m1.metric("Present value", f"${result['present_value']:,.2f}")
            m2.metric("Autocall probability", f"{result['autocall_probability'] * 100:.1f}%")
            m3.metric("Capital-loss probability", f"{result['capital_loss_probability'] * 100:.1f}%")
            st.metric("Expected redemption time", f"{result['expected_redemption_years']:.2f} years")

st.divider()
st.caption(
    "Model scope: constant-volatility research assumptions with no live market-data feed, transaction-cost model, "
    "volatility-surface calibration, issuer-credit adjustment, or suitability workflow."
)
