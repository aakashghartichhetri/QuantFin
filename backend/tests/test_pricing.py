import math
from app.services.pricing import OptionInputs, black_scholes_price, implied_volatility, monte_carlo_european, binomial_american


def test_black_scholes_known_call_value():
    x = OptionInputs(spot=100, strike=100, rate=0.05, volatility=0.2, maturity=1, option_type="call")
    assert math.isclose(black_scholes_price(x), 10.4506, rel_tol=1e-4)


def test_implied_vol_round_trip():
    x = OptionInputs(spot=100, strike=105, rate=0.03, volatility=0.27, maturity=0.75, option_type="put")
    price = black_scholes_price(x)
    iv = implied_volatility(price, x)
    assert math.isclose(iv, 0.27, rel_tol=1e-5)


def test_monte_carlo_is_close_to_black_scholes():
    x = OptionInputs(spot=100, strike=100, rate=0.02, volatility=0.2, maturity=1, option_type="call")
    bs = black_scholes_price(x)
    mc = monte_carlo_european(x, simulations=150_000, seed=7)
    assert abs(mc["price"] - bs) < 0.15


def test_american_put_at_least_european_put():
    x = OptionInputs(spot=100, strike=105, rate=0.05, volatility=0.25, maturity=1, option_type="put")
    assert binomial_american(x, steps=500) >= black_scholes_price(x) - 1e-8
