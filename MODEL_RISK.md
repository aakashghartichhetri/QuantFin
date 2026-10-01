# Model Risk & Limitations

This repository is a quantitative research and portfolio implementation designed to demonstrate derivatives analytics and software-engineering discipline. It is **not approved for live trading, client valuation, valuation control, regulatory capital, suitability, or real-money risk management**.

## Model assumptions

### Black-Scholes
- Lognormal underlying dynamics
- Constant volatility
- Constant risk-free rate
- Continuous hedging idealization
- Frictionless markets
- European exercise
- Continuous dividend yield when supplied

### Monte Carlo
- Geometric Brownian motion under the risk-neutral measure
- Constant volatility and rate
- Pseudo-random simulation
- No volatility smile/skew calibration
- No issuer credit spread, liquidity premium, transaction costs, or funding spread

### Historical VaR / CVaR
- Future loss behavior is proxied by the supplied validation return series
- No explicit volatility scaling or regime adjustment
- No liquidity-horizon or stress-scenario overlay
- No dependency model for multi-asset portfolios

### Structured products
The buffered note and autocallable are intentionally scoped payoff and pricing engines. They omit many features found in institutional issuance, including legal terms, observation conventions, issuer credit, coupon memory, knock-in conventions, business-day rules, settlement mechanics, dividends, funding, hedging costs, and volatility-surface calibration.

## Controls implemented
- Input validation through Pydantic and explicit model checks
- Deterministic random seeds for reproducible validation runs
- Closed-form benchmark testing for Black-Scholes
- Implied-volatility round-trip validation
- Monte Carlo convergence check against Black-Scholes
- American-put lower-bound check versus the European put
- Structured-product payoff tests
- Automated test execution in CI
- Explicit model limitations in the interface and documentation

## Requirements before institutional use
- Independent model validation
- Governed market-data controls and lineage
- Volatility-surface construction and calibration controls
- Curve construction and dividend modeling
- Credit/funding adjustments where applicable
- Stress testing and backtesting
- Versioned model governance and approval workflows
- Entitlements, audit logging, secrets management, monitoring, and incident response
- Reconciliation against trusted pricing libraries or front-office systems
- Legal, compliance, risk, and suitability review
