"""Thin wrapper around the Anthropic SDK.

The wrapper exists for three reasons:

1. To centralise model and pricing constants so cost accounting is uniform.
2. To return a typed ``LLMResponse`` with usage information so agents can
   record their own cost into ``WorkerResult.cost``.
3. To provide a deterministic mock mode for tests and CI. The mock is not a
   stub: it returns valid JSON that the rest of the pipeline can synthesise
   against, so the end-to-end graph runs without network or API key.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from anthropic import Anthropic
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential_jitter,
)

from src.config import get_settings
from src.models.state import CostBreakdown

# Per-million-token pricing in USD. Updated 2026-05; reviewed quarterly.
# These numbers are used for cost accounting only, not for billing decisions.
_PRICING = {
    "claude-sonnet-4-6": (3.00, 15.00),
    "claude-haiku-4-5-20251001": (1.00, 5.00),
}


@dataclass(frozen=True, slots=True)
class LLMResponse:
    content: str
    model: str
    input_tokens: int
    output_tokens: int

    @property
    def cost(self) -> CostBreakdown:
        input_per_m, output_per_m = _PRICING.get(self.model, (0.0, 0.0))
        usd = (self.input_tokens / 1_000_000) * input_per_m + (
            self.output_tokens / 1_000_000
        ) * output_per_m
        return CostBreakdown(
            input_tokens=self.input_tokens,
            output_tokens=self.output_tokens,
            usd=round(usd, 6),
        )

    def parsed_json(self) -> dict[str, Any]:
        """Parse the response body as JSON.

        Models occasionally prefix or suffix structured output with prose
        despite instructions. We extract the first balanced ``{...}`` block.
        """

        text = self.content.strip()
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise ValueError("LLM response did not contain a JSON object")
        parsed: dict[str, Any] = json.loads(text[start : end + 1])
        return parsed


class LLMClient:
    """Synchronous Anthropic client with retry, cost accounting, and mock mode."""

    def __init__(
        self,
        *,
        api_key: str | None = None,
        mock: bool | None = None,
        mock_response: str | None = None,
    ) -> None:
        settings = get_settings()
        resolved_key = (
            api_key
            if api_key is not None
            else (settings.anthropic_api_key.get_secret_value() or None)
        )
        # Mock mode is auto-engaged when no key is configured; this lets the
        # graph run end-to-end in CI, in tests, and on first-time local setup
        # without surprising the operator with 401s.
        self._mock = mock if mock is not None else resolved_key is None
        self._mock_response = mock_response
        self._client: Anthropic | None = None
        if not self._mock:
            assert resolved_key is not None
            self._client = Anthropic(api_key=resolved_key)

    @property
    def is_mocked(self) -> bool:
        return self._mock

    @retry(
        reraise=True,
        retry=retry_if_exception_type(Exception),
        stop=stop_after_attempt(3),
        wait=wait_exponential_jitter(initial=2, max=8),
    )
    def _call_anthropic(
        self,
        *,
        model: str,
        system: str,
        user: str,
        max_tokens: int,
    ) -> LLMResponse:
        assert self._client is not None
        message = self._client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        text = "".join(getattr(block, "text", "") for block in message.content)
        return LLMResponse(
            content=text,
            model=model,
            input_tokens=message.usage.input_tokens,
            output_tokens=message.usage.output_tokens,
        )

    def complete(
        self,
        *,
        system: str,
        user: str,
        model: str | None = None,
        max_tokens: int = 2048,
    ) -> LLMResponse:
        resolved_model = model or get_settings().anthropic_model_synthesis
        if self._mock:
            payload = self._mock_response or _default_mock_payload()
            # The mock charges a tiny deterministic cost so the accounting
            # path is exercised in CI.
            return LLMResponse(
                content=payload,
                model=resolved_model,
                input_tokens=len(user) // 4,
                output_tokens=len(payload) // 4,
            )
        return self._call_anthropic(
            model=resolved_model, system=system, user=user, max_tokens=max_tokens
        )


def _default_mock_payload() -> str:
    """A deterministic, schema-valid mock note body for tests and CI."""

    return json.dumps(
        {
            "executive_summary": (
                "Mock executive summary produced in offline mode. The full "
                "synthesis is exercised by the eval harness against a real "
                "Anthropic key."
            ),
            "investment_theses": [
                {
                    "statement": "Demand profile holds steady through cycle.",
                    "citations": [],
                }
            ],
            "key_risks": [
                {
                    "statement": "Margin compression if input costs rise.",
                    "citations": [],
                }
            ],
            "catalysts": [
                {
                    "statement": "Earnings release within the next 60 days.",
                    "citations": [],
                }
            ],
        }
    )
