"""Schemas for the final synthesised research note.

The Synthesizer must produce JSON that validates against ``NoteDraft``. Any
field tagged with a ``Claim`` carries its own citations, which is how the
note enforces "every claim is traceable to a source hash" end-to-end.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from src.models.state import SourceCitation


class Claim(BaseModel):
    """A single sourced statement.

    A claim with an empty citation list is treated as unsupported by the
    critique agent and may force a synthesizer rerun.
    """

    model_config = ConfigDict(frozen=True)

    statement: str = Field(min_length=1)
    citations: tuple[SourceCitation, ...] = ()

    def is_supported(self) -> bool:
        return bool(self.citations)


class MarketSnapshot(BaseModel):
    model_config = ConfigDict(frozen=True)

    last_price: float | None = None
    currency: str = "USD"
    market_cap_usd: float | None = None
    return_1m_pct: float | None = None
    return_3m_pct: float | None = None
    return_1y_pct: float | None = None
    realized_vol_pct: float | None = None
    beta_vs_spx: float | None = None
    max_drawdown_pct: float | None = None


class NoteDraft(BaseModel):
    model_config = ConfigDict(frozen=True)

    ticker: str
    executive_summary: str
    investment_theses: tuple[Claim, ...] = ()
    key_risks: tuple[Claim, ...] = ()
    catalysts: tuple[Claim, ...] = ()
    market_snapshot: MarketSnapshot | None = None
    disclaimer: str = (
        "Automated research support, not investment advice. This note was "
        "produced by a hierarchical multi-agent system over public data only."
    )

    def unsupported_claims(self) -> tuple[Claim, ...]:
        return tuple(
            claim
            for bucket in (self.investment_theses, self.key_risks, self.catalysts)
            for claim in bucket
            if not claim.is_supported()
        )
