from __future__ import annotations
from typing import Literal
from pydantic import BaseModel, Field


class OptionRequest(BaseModel):
    spot: float = Field(gt=0)
    strike: float = Field(gt=0)
    rate: float
    volatility: float = Field(gt=0, le=5)
    maturity: float = Field(gt=0, le=50)
    dividend_yield: float = 0.0
    option_type: Literal["call", "put"] = "call"


class MonteCarloRequest(OptionRequest):
    simulations: int = Field(default=100_000, ge=1_000, le=2_000_000)
    seed: int = 42


class ImpliedVolRequest(BaseModel):
    market_price: float = Field(gt=0)
    spot: float = Field(gt=0)
    strike: float = Field(gt=0)
    rate: float
    maturity: float = Field(gt=0, le=50)
    dividend_yield: float = 0.0
    option_type: Literal["call", "put"] = "call"


class AmericanRequest(OptionRequest):
    steps: int = Field(default=300, ge=10, le=5000)


class VarRequest(BaseModel):
    returns: list[float]
    confidence: float = Field(default=0.95, gt=0.5, lt=0.999)
    notional: float = Field(default=1_000_000, gt=0)


class ScenarioRequest(BaseModel):
    delta: float
    gamma: float
    vega: float
    spot: float = Field(gt=0)
    spot_shocks: list[float] = [-0.10, -0.05, 0.0, 0.05, 0.10]
    vol_shocks: list[float] = [-0.05, 0.0, 0.05]


class BufferedNoteRequest(BaseModel):
    initial_spot: float = Field(gt=0)
    terminal_min: float = Field(ge=0)
    terminal_max: float = Field(gt=0)
    points: int = Field(default=101, ge=10, le=1000)
    notional: float = Field(default=1000.0, gt=0)
    upside_participation: float = Field(default=1.2, ge=0)
    buffer: float = Field(default=0.15, ge=0, lt=1)
    cap: float | None = Field(default=0.30, ge=0)


class AutocallableRequest(BaseModel):
    initial_spot: float = Field(gt=0)
    rate: float
    volatility: float = Field(gt=0, le=5)
    maturity: float = Field(default=1.0, gt=0, le=10)
    observations: int = Field(default=4, ge=1, le=24)
    autocall_barrier: float = Field(default=1.0, gt=0, le=2.0)
    protection_barrier: float = Field(default=0.70, gt=0, le=1.0)
    coupon_per_period: float = Field(default=0.025, ge=0, le=1.0)
    notional: float = Field(default=1000.0, gt=0)
    simulations: int = Field(default=100_000, ge=1_000, le=1_000_000)
    seed: int = 42
