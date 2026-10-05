
# mailsieve

A Python tool for analysing and cleaning up a Gmail inbox. It connects over IMAP
in **read-only** mode, finds which senders generate the most mail, and is being
built towards rule-based and LLM-assisted cleanup with human review.

## Status

Early development. Currently implemented:

- Secure configuration loading from `.env`
- Read-only IMAP connection to Gmail
- Batched fetching of sender headers
- Top-sender statistics for the whole inbox

## How it works

```
.env ──> Settings ──> ImapClient ──> parse_sender ──> SenderStats ──> report
                     (read-only,     (From header     (counts per
                      batched UIDs)   -> Sender)        address)
```

- Only the `From` header is fetched (`BODY.PEEK[HEADER.FIELDS (FROM)]`), never
  message bodies.
- The mailbox is opened with `readonly=True`, so no flags change and nothing is
  moved or deleted.
- Messages are addressed by UID and fetched in batches, so large inboxes
  (tens of thousands of messages) are processed as a stream.

## Requirements

- Python 3.12+
- [uv](https://docs.astral.sh/uv/)
- A Gmail account with 2-Step Verification enabled and an
  [app password](https://myaccount.google.com/apppasswords)

## Setup

```bash
git clone git@github.com:krzysiekbienias/mailsieve.git
cd mailsieve
uv sync
```

Create a `.env` file in the project root:

```
GMAIL_ADDRESS=you@gmail.com
GMAIL_APP_PASSWORD=your16charapppassword
```

Restrict its permissions:

```bash
chmod 600 .env
```

`.env` is listed in `.gitignore` and must never be committed.

## Usage

```bash
uv run mailsieve
```

Example output:

```
INBOX: 45574 messages, fetching senders...
  5000 processed
  ...

45574 messages from 1714 unique senders

   2097    4.6%  newsletter@example-bank.com                   Example Bank
   1346    3.0%  noreply@example-news.com                      Daily Digest
   ...
```

## Development

```bash
uv run pytest            # run tests
uv run ruff check .      # lint
uv run ruff format .     # format
```

Tests do not require network access; IMAP interactions are replaced with fakes.

## Project structure

```
src/mailsieve/
├── __init__.py      # entry point (main)
├── config.py        # Settings loaded from .env, secrets as SecretStr
├── domain.py        # plain domain objects: Sender, SenderCount
├── headers.py       # parsing of raw email headers
├── imap_client.py   # read-only IMAP client, batched fetching
└── stats.py         # sender aggregation
tests/
```

## Security notes

- Credentials are loaded from `.env` and held as `SecretStr`, so they never
  appear in logs or printed output.
- The app password grants full mailbox access; revoke it at any time from your
  Google Account settings.
- The tool is read-only by design. Any future cleanup actions will run in a
  dry-run mode first and require explicit confirmation.

## Roadmap

- [X] Top-sender statistics
- [ ] Statistics grouped by domain
- [ ] Rule-based cleanup with dry-run mode and an audit log
- [ ] LLM-assisted classification of ambiguous messages, with structured-output
  validation and human review
- [ ] Django web interface
