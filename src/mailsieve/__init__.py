from mailsieve.config import ConfigError, Settings
from mailsieve.imap_client import ImapClient, MailboxError


def main() -> None:
    try:
        settings = Settings.from_env()
        with ImapClient(settings) as client:
            count = client.select_mailbox("INBOX")
    except (ConfigError, MailboxError) as exc:
        raise SystemExit(f"Error: {exc}") from None

    print(
        f"Connected as {settings.gmail_address}: INBOX has {count} messages (read-only)"
    )
