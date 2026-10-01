from __future__ import annotations
from fastapi import APIRouter, HTTPException

from app.models.schemas import (
    AmericanRequest,
    AutocallableRequest,
    BufferedNoteRequest,
    ImpliedVolRequest,
    MonteCarloRequest,
    OptionRequest,
    ScenarioRequest,
    VarRequest,
)
from app.services.pricing import (
    OptionInputs,
    binomial_american,
    black_scholes_greeks,
    black_scholes_price,
    implied_volatility,
    monte_carlo_european,
)
from app.services.risk import historical_var_cvar, pnl_scenarios
from app.services.structured import buffered_note_curve, price_autocallable_gbm

router = APIRouter()


def to_inputs(req: OptionRequest) -> OptionInputs:
    return OptionInputs(**req.model_dump(exclude={"simulations", "seed", "steps"}))


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/pricing/black-scholes")
def price_black_scholes(req: OptionRequest):
    try:
        x = to_inputs(req)
        return {"price": black_scholes_price(x), "greeks": black_scholes_greeks(x)}
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/pricing/monte-carlo")
def price_monte_carlo(req: MonteCarloRequest):
    try:
        return monte_carlo_european(to_inputs(req), req.simulations, req.seed)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/pricing/american-binomial")
def price_american(req: AmericanRequest):
    try:
        return {"price": binomial_american(to_inputs(req), req.steps)}
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/volatility/implied")
def calc_implied_vol(req: ImpliedVolRequest):
    try:
        x = OptionInputs(
            spot=req.spot,
            strike=req.strike,
            rate=req.rate,
            volatility=0.2,
            maturity=req.maturity,
            dividend_yield=req.dividend_yield,
            option_type=req.option_type,
        )
        return {"implied_volatility": implied_volatility(req.market_price, x)}
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/risk/historical-var")
def calc_var(req: VarRequest):
    try:
        return historical_var_cvar(req.returns, req.confidence, req.notional)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/risk/greeks-scenarios")
def calc_scenarios(req: ScenarioRequest):
    try:
        return {"scenarios": pnl_scenarios(req.delta, req.gamma, req.vega, req.spot, req.spot_shocks, req.vol_shocks)}
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/structured/buffered-note")
def calc_buffered_note(req: BufferedNoteRequest):
    try:
        if req.terminal_max <= req.terminal_min:
            raise ValueError("terminal_max must exceed terminal_min")
        return {
            "curve": buffered_note_curve(
                initial_spot=req.initial_spot,
                terminal_min=req.terminal_min,
                terminal_max=req.terminal_max,
                points=req.points,
                notional=req.notional,
                upside_participation=req.upside_participation,
                buffer=req.buffer,
                cap=req.cap,
            )
        }
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/structured/autocallable")
def calc_autocallable(req: AutocallableRequest):
    try:
        return price_autocallable_gbm(**req.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
