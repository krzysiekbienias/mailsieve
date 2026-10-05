from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Sender:
    address: str
    name: str = ""


@dataclass(frozen=True, slots=True)
class SenderCount:
    sender: Sender
    count: int
