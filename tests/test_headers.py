from mailsieve.domain import Sender
from mailsieve.headers import parse_sender


def test_parses_plain_sender():
    raw = b"From: Jan Kowalski <Jan@Example.com>\r\n\r\n"
    assert parse_sender(raw) == Sender(address="jan@example.com", name="Jan Kowalski")


def test_decodes_encoded_display_name():
    raw = b"From: =?UTF-8?Q?Pawe=C5=82_Nowak?= <pawel@example.com>\r\n\r\n"
    assert parse_sender(raw) == Sender(address="pawel@example.com", name="Paweł Nowak")


def test_missing_from_returns_none():
    assert parse_sender(b"Subject: hello\r\n\r\n") is None
