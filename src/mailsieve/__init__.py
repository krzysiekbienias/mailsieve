from mailsieve.config import ConfigError, Settings
from mailsieve.imap_client import ImapClient, MailboxError

SAMPLE_LIMIT = 1000


def main() -> None:
    try:
        settings = Settings.from_env()
        with ImapClient(settings) as client:
            count = client.select_mailbox("INBOX")
            senders = list(client.iter_senders(limit=SAMPLE_LIMIT))
    except (ConfigError, MailboxError) as exc:
        raise SystemExit(f"Error: {exc}") from None

    print(
        f"INBOX: {count} messages, parsed {len(senders)} senders "
        f"from the latest {SAMPLE_LIMIT}"
    )
    for sender in senders[:10]:
        print(f"  {sender.name or '-'} <{sender.address}>")
