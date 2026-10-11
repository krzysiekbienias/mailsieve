from types import SimpleNamespace

from mailsieve.classifier import SenderClassifier
from mailsieve.domain import Category, SenderProfile


def make_response(tool_input):
    block = SimpleNamespace(type="tool_use", input=tool_input)
    usage = SimpleNamespace(input_tokens=100, output_tokens=20)
    return SimpleNamespace(content=[block], usage=usage)


class FakeClient:
    def __init__(self, tool_input):
        self.calls = 0
        self.messages = SimpleNamespace(create=self._create)
        self._tool_input = tool_input

    def _create(self, **kwargs):
        self.calls += 1
        return make_response(self._tool_input)


def profile(address):
    return SenderProfile(address=address, name="", subjects=(), message_count=1)


def test_valid_output_is_accepted():
    client = FakeClient(
        {"results": [{"address": "a@x.com", "category": "job", "confidence": 0.9}]}
    )
    result = SenderClassifier(client, "model").classify([profile("a@x.com")])

    assert result[0].category is Category.JOB
    assert not result[0].needs_review


def test_low_confidence_is_flagged():
    client = FakeClient(
        {"results": [{"address": "a@x.com", "category": "other", "confidence": 0.4}]}
    )
    result = SenderClassifier(client, "model").classify([profile("a@x.com")])

    assert result[0].needs_review
    assert result[0].reason == "low confidence"


def test_missing_sender_is_flagged():
    client = FakeClient({"results": []})
    result = SenderClassifier(client, "model").classify([profile("a@x.com")])

    assert result[0].needs_review
    assert result[0].category is None


def test_invalid_category_is_flagged_not_raised():
    client = FakeClient(
        {"results": [{"address": "a@x.com", "category": "spam", "confidence": 0.9}]}
    )
    result = SenderClassifier(client, "model").classify([profile("a@x.com")])

    assert result[0].needs_review
    assert result[0].reason == "invalid model output"


def test_batches_and_counts_tokens():
    client = FakeClient({"results": []})
    classifier = SenderClassifier(client, "model", batch_size=2)
    classifier.classify([profile(f"{i}@x.com") for i in range(5)])

    assert client.calls == 3
    assert classifier.input_tokens == 300
