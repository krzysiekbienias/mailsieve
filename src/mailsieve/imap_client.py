from __future__ import annotations

import imaplib
from types import TracebackType
from typing import Self

from mailsieve.config import Settings


class MailboxError(Exception):
    """Raised when connecting to or reading the mailbox fails."""


class ImapClient:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._conn: imaplib.IMAP4_SSL | None = None

    def __enter__(self) -> Self:
        self.connect()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self.close()

    def connect(self) -> None:
        host = self._settings.imap_host
        try:
            self._conn = imaplib.IMAP4_SSL(host)
            self._conn.login(
                self._settings.gmail_address,
                self._settings.gmail_app_password.get_secret_value(),
            )
        except imaplib.IMAP4.error as exc:
            self.close()
            raise MailboxError(
                f"Login failed for {self._settings.gmail_address}: {exc}"
            ) from None
        except OSError as exc:
            self.close()
            raise MailboxError(f"Cannot reach {host}: {exc}") from None

    def select_mailbox(self, mailbox: str = "INBOX") -> int:
        status, data = self._require_conn().select(mailbox, readonly=True)
        if status != "OK":
            raise MailboxError(f"Cannot open mailbox {mailbox!r}: {data}")
        return int(data[0])

    def close(self) -> None:
        if self._conn is None:
            return
        try:
            if self._conn.state == "SELECTED":
                self._conn.close()
            self._conn.logout()
        except (imaplib.IMAP4.error, OSError):
            pass
        finally:
            self._conn = None

    def _require_conn(self) -> imaplib.IMAP4_SSL:
        if self._conn is None:
            raise MailboxError("Not connected")
        return self._conn
