from __future__ import annotations

import json
from collections.abc import Sequence
from itertools import batched
from typing import Any

import anthropic
from pydantic import BaseModel, Field, ValidationError

from mailsieve.domain import Category, Classification, SenderProfile

SYSTEM_PROMPT = """You classify email senders for an inbox cleanup tool.
For every sender you receive, choose exactly one category:
- job: job boards, recruiters, job alerts, professional networking notifications
- shopping: online shops, marketplaces, retail promotions and offers
- newsletter: content digests, media, courses, learning apps, communities
- transactional: banks, payments, invoices, bookings, account or security notices
- other: personal mail or anything that does not clearly fit the above
Use the address, display name and sample subjects.
Give a confidence between 0 and 1. Return one result for every sender."""

TOOL_NAME = "record_classifications"

TOOL: dict[str, Any] = {
    "name": TOOL_NAME,
    "description": "Record exactly one classification for every sender provided.",
    "input_schema": {
        "type": "object",
        "properties": {
            "results": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "address": {"type": "string"},
                        "category": {
                            "type": "string",
                            "enum": [c.value for c in Category],
                        },
                        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                    },
                    "required": ["address", "category", "confidence"],
                },
            }
        },
        "required": ["results"],
    },
}


class ClassifierError(Exception):
    """Raised when the classification API cannot be reached."""


class _ModelResult(BaseModel):
    address: str
    category: Category
    confidence: float = Field(ge=0, le=1)


class _ModelOutput(BaseModel):
    results: list[_ModelResult]


class SenderClassifier:
    def __init__(
        self,
        client: Any,
        model: str,
        batch_size: int = 25,
        min_confidence: float = 0.7,
    ) -> None:
        self._client = client
        self._model = model
        self._batch_size = batch_size
        self._min_confidence = min_confidence
        self.input_tokens = 0
        self.output_tokens = 0
        self.api_calls = 0

    def classify(self, profiles: Sequence[SenderProfile]) -> list[Classification]:
        results: list[Classification] = []
        for batch in batched(profiles, self._batch_size):
            results.extend(self._classify_batch(batch))
        return results

    def _classify_batch(self, batch: Sequence[SenderProfile]) -> list[Classification]:
        payload = [
            {"address": p.address, "name": p.name, "subjects": list(p.subjects)}
            for p in batch
        ]
        try:
            response = self._client.messages.create(
                model=self._model,
                max_tokens=2048,
                system=SYSTEM_PROMPT,
                tools=[TOOL],
                tool_choice={"type": "tool", "name": TOOL_NAME},
                messages=[
                    {"role": "user", "content": json.dumps(payload, ensure_ascii=False)}
                ],
            )
        except anthropic.APIError as exc:
            raise ClassifierError(f"Anthropic API call failed: {exc}") from None

        self.api_calls += 1
        self.input_tokens += response.usage.input_tokens
        self.output_tokens += response.usage.output_tokens

        raw = next(
            (block.input for block in response.content if block.type == "tool_use"),
            None,
        )
        try:
            output = _ModelOutput.model_validate(raw)
        except ValidationError:
            return [self._review(p.address, "invalid model output") for p in batch]

        by_address = {r.address.strip().lower(): r for r in output.results}
        return [self._to_classification(p, by_address.get(p.address)) for p in batch]

    def _to_classification(
        self, profile: SenderProfile, result: _ModelResult | None
    ) -> Classification:
        if result is None:
            return self._review(profile.address, "missing from model output")
        if result.confidence < self._min_confidence:
            return Classification(
                address=profile.address,
                category=result.category,
                confidence=result.confidence,
                needs_review=True,
                reason="low confidence",
            )
        return Classification(
            address=profile.address,
            category=result.category,
            confidence=result.confidence,
            needs_review=False,
        )

    @staticmethod
    def _review(address: str, reason: str) -> Classification:
        return Classification(
            address=address,
            category=None,
            confidence=0.0,
            needs_review=True,
            reason=reason,
        )
