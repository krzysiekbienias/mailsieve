from dataclasses import dataclass
from enum import StrEnum


class Category(StrEnum):
    JOB = "job"
    SHOPPING = "shopping"
    NEWSLETTER = "newsletter"
    TRANSACTIONAL = "transactional"
    OTHER = "other"


@dataclass(frozen=True, slots=True)
class Sender:
    address: str
    name: str = ""


@dataclass(frozen=True, slots=True)
class SenderCount:
    sender: Sender
    count: int


@dataclass(frozen=True, slots=True)
class MessageInfo:
    sender: Sender
    subject: str


@dataclass(frozen=True, slots=True)
class SenderProfile:
    address: str
    name: str
    subjects: tuple[str, ...]
    message_count: int


@dataclass(frozen=True, slots=True)
class Classification:
    address: str
    category: Category | None
    confidence: float
    needs_review: bool
    reason: str = ""
