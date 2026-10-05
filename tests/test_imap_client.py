import imaplib

import pytest

from mailsieve.config import Settings
from mailsieve.imap_client import ImapClient, MailboxError


@pytest.fixture
def settings():
    return Settings(gmail_address="a@gmail.com", gmail_app_password="secret")


def test_login_failure_raises_and_closes_connection(monkeypatch, settings):
    created = []

    class FakeImap:
        def __init__(self, host):
            self.state = "NONAUTH"
            self.logged_out = False
            created.append(self)

        def login(self, user, password):
            raise imaplib.IMAP4.error("[AUTHENTICATIONFAILED] Invalid credentials")

        def logout(self):
            self.logged_out = True

    monkeypatch.setattr(imaplib, "IMAP4_SSL", FakeImap)

    with pytest.raises(MailboxError, match="Login failed"), ImapClient(settings):
        pass

    assert created[0].logged_out


def test_close_without_connect_is_safe(settings):
    ImapClient(settings).close()


def test_iter_senders_fetches_in_batches(settings):
    fetched_sets = []

    class FakeConn:
        def uid(self, command, *args):
            if command == "SEARCH":
                return "OK", [b"1 2 3"]
            uid_set = args[0]
            fetched_sets.append(uid_set)
            data = []
            for uid in uid_set.split(","):
                header = f"From: User {uid} <user{uid}@example.com>\r\n\r\n".encode()
                data.append(
                    (f"{uid} (UID {uid} BODY[HEADER.FIELDS (FROM)])".encode(), header)
                )
                data.append(b")")
            return "OK", data

    client = ImapClient(settings)
    client._conn = FakeConn()

    senders = list(client.iter_senders(batch_size=2))

    assert fetched_sets == ["1,2", "3"]
    assert [s.address for s in senders] == [
        "user1@example.com",
        "user2@example.com",
        "user3@example.com",
    ]
