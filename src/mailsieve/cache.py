import json
from pathlib import Path

from mailsieve.domain import Category, Classification


class ClassificationCache:
    def __init__(self, path: Path) -> None:
        self._path = path
        self._data: dict[str, dict[str, object]] = {}
        if path.exists():
            self._data = json.loads(path.read_text(encoding="utf-8"))

    def get(self, address: str) -> Classification | None:
        entry = self._data.get(address)
        if entry is None:
            return None
        return Classification(
            address=address,
            category=Category(entry["category"]),
            confidence=float(entry["confidence"]),
            needs_review=bool(entry["needs_review"]),
            reason=str(entry.get("reason", "")),
        )

    def put(self, classification: Classification) -> None:
        if classification.category is None:
            return
        self._data[classification.address] = {
            "category": classification.category.value,
            "confidence": classification.confidence,
            "needs_review": classification.needs_review,
            "reason": classification.reason,
        }

    def save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(
            json.dumps(self._data, indent=2, ensure_ascii=False), encoding="utf-8"
        )
