from app.services.risk import historical_var_cvar
from app.services.structured import buffered_note_payoff


def test_var_cvar_ordering():
    returns = [(-0.03 + i * 0.002) for i in range(40)]
    out = historical_var_cvar(returns, confidence=0.95, notional=1_000_000)
    assert out["cvar"] >= out["var"]


def test_buffer_protects_first_15_percent():
    payoff = buffered_note_payoff(100, 90, notional=1000, buffer=0.15)
    assert payoff == 1000


def test_loss_beyond_buffer():
    payoff = buffered_note_payoff(100, 70, notional=1000, buffer=0.15)
    assert payoff == 850


def test_autocallable_outputs_are_probabilities():
    from app.services.structured import price_autocallable_gbm
    out = price_autocallable_gbm(
        initial_spot=100,
        rate=0.03,
        volatility=0.20,
        simulations=20_000,
        seed=11,
    )
    assert out["present_value"] > 0
    assert 0 <= out["autocall_probability"] <= 1
    assert 0 <= out["capital_loss_probability"] <= 1
    assert 0 < out["expected_redemption_years"] <= 1.0
