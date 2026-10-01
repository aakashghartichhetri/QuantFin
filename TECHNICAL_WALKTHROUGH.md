# Technical Walkthrough

## 30-second overview

“I built a structured-products analytics platform in Python. FastAPI exposes derivatives pricing, volatility, market-risk, and structured-payoff models as typed REST services, while Streamlit provides an interactive analytics interface. The platform supports Black-Scholes and Monte Carlo pricing, Greeks, implied volatility, historical VaR/CVaR, buffered notes, and a path-dependent autocallable. I containerized the services and added automated model-validation tests and CI so the system is reproducible and reviewable.”

## Two-minute walkthrough

1. **Vanilla pricing** — price a European call using Black-Scholes.
2. **Independent numerical check** — price the same contract with Monte Carlo and compare the estimate and standard error.
3. **Volatility analysis** — solve implied volatility from an observed premium.
4. **Risk analytics** — review Delta/Gamma/Vega and historical VaR/CVaR.
5. **Payoff structuring** — adjust a buffered-note buffer and participation rate and explain the resulting payoff profile.
6. **Path-dependent pricing** — review autocall probability, capital-loss probability, and expected redemption time.
7. **Engineering controls** — show FastAPI `/docs`, automated tests, Docker Compose, CI, input validation, and documented model limitations.

## Questions to be ready for

- What assumptions does Black-Scholes make?
- Why does higher volatility generally increase vanilla option value?
- What does Delta mean for a call option?
- Why can an American put be worth more than a European put?
- What is the difference between VaR and CVaR?
- What are the limitations of historical VaR?
- How does path dependence change autocallable pricing?
- How would you calibrate to a volatility smile or surface rather than use constant volatility?
- What controls would be required before institutional use?
