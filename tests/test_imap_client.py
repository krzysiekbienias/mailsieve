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
