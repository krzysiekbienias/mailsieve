from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Sender:
    address: str
    name: str = ""
