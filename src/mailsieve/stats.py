from collections import Counter

from mailsieve.domain import Sender, SenderCount


class SenderStats:
    def __init__(self) -> None:
        self._counts: Counter[str] = Counter()
        self._names: dict[str, str] = {}

    def add(self, sender: Sender) -> None:
        self._counts[sender.address] += 1
        if sender.name:
            self._names[sender.address] = sender.name

    @property
    def total(self) -> int:
        return self._counts.total()

    @property
    def unique_senders(self) -> int:
        return len(self._counts)

    def top(self, n: int) -> list[SenderCount]:
        return [
            SenderCount(Sender(address, self._names.get(address, "")), count)
            for address, count in self._counts.most_common(n)
        ]
