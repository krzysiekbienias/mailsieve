from mailsieve.domain import Sender, SenderCount
from mailsieve.stats import SenderStats


def test_counts_and_orders_senders():
    stats = SenderStats()
    for sender in [
        Sender("a@x.com", "A"),
        Sender("b@x.com", "B"),
        Sender("a@x.com", "A"),
    ]:
        stats.add(sender)

    assert stats.total == 3
    assert stats.unique_senders == 2
    assert stats.top(1) == [SenderCount(Sender("a@x.com", "A"), 2)]


def test_keeps_latest_non_empty_name():
    stats = SenderStats()
    stats.add(Sender("a@x.com", "Old Name"))
    stats.add(Sender("a@x.com", ""))
    stats.add(Sender("a@x.com", "New Name"))

    assert stats.top(1)[0].sender.name == "New Name"


def test_empty_stats():
    stats = SenderStats()
    assert stats.total == 0
    assert stats.top(5) == []
