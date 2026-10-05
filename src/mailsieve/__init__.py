from mailsieve.config import ConfigError, Settings
from mailsieve.imap_client import ImapClient, MailboxError
from mailsieve.stats import SenderStats

TOP_N = 20
PROGRESS_EVERY = 5000


def main() -> None:
    stats = SenderStats()
    try:
        settings = Settings.from_env()
        with ImapClient(settings) as client:
            count = client.select_mailbox("INBOX")
            print(f"INBOX: {count} messages, fetching senders...")
            for i, sender in enumerate(client.iter_senders(), start=1):
                stats.add(sender)
                if i % PROGRESS_EVERY == 0:
                    print(f"  {i} processed", flush=True)
    except (ConfigError, MailboxError) as exc:
        raise SystemExit(f"Error: {exc}") from None

    if stats.total == 0:
        print("No senders found.")
        return

    print(f"\n{stats.total} messages from {stats.unique_senders} unique senders\n")
    for row in stats.top(TOP_N):
        share = row.count / stats.total
        print(
            f"{row.count:>7}  {share:>6.1%}  {row.sender.address:<45} {row.sender.name}"
        )
