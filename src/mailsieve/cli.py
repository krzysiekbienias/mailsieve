import argparse
from collections import Counter

import anthropic

from mailsieve.cache import ClassificationCache
from mailsieve.classifier import ClassifierError, SenderClassifier
from mailsieve.config import ConfigError, Settings
from mailsieve.domain import Classification, SenderProfile
from mailsieve.imap_client import ImapClient, MailboxError
from mailsieve.profiles import build_profiles
from mailsieve.stats import SenderStats

TOP_N = 20
PROGRESS_EVERY = 5000


def run_stats(settings: Settings) -> None:
    stats = SenderStats()
    with ImapClient(settings) as client:
        count = client.select_mailbox("INBOX")
        print(f"INBOX: {count} messages, fetching senders...")
        for i, sender in enumerate(client.iter_senders(), start=1):
            stats.add(sender)
            if i % PROGRESS_EVERY == 0:
                print(f"  {i} processed", flush=True)

    if stats.total == 0:
        print("No senders found.")
        return

    print(f"\n{stats.total} messages from {stats.unique_senders} unique senders\n")
    for row in stats.top(TOP_N):
        share = row.count / stats.total
        print(
            f"{row.count:>7}  {share:>6.1%}  {row.sender.address:<45} {row.sender.name}"
        )


def run_classify(settings: Settings, sample: int) -> None:
    if settings.anthropic_api_key is None:
        raise ConfigError("ANTHROPIC_API_KEY is required for classify")

    with ImapClient(settings) as client:
        client.select_mailbox("INBOX")
        messages = list(client.iter_messages(limit=sample))

    profiles = build_profiles(messages)
    cache = ClassificationCache(settings.cache_dir / "classifications.json")

    cached = [c for p in profiles if (c := cache.get(p.address)) is not None]
    known = {c.address for c in cached}
    to_classify = [p for p in profiles if p.address not in known]

    classifier = SenderClassifier(
        client=anthropic.Anthropic(
            api_key=settings.anthropic_api_key.get_secret_value()
        ),
        model=settings.anthropic_model,
    )
    fresh = classifier.classify(to_classify) if to_classify else []

    for classification in fresh:
        cache.put(classification)
    cache.save()

    _print_report(
        messages_count=len(messages),
        profiles=profiles,
        results=cached + fresh,
        cached=len(cached),
        classifier=classifier,
    )


def _print_report(
    messages_count: int,
    profiles: list[SenderProfile],
    results: list[Classification],
    cached: int,
    classifier: SenderClassifier,
) -> None:
    counts = {p.address: p.message_count for p in profiles}
    senders_per_cat: Counter[str] = Counter()
    messages_per_cat: Counter[str] = Counter()
    for r in results:
        label = r.category.value if r.category else "unclassified"
        senders_per_cat[label] += 1
        messages_per_cat[label] += counts.get(r.address, 0)

    print(
        f"\nSample: {messages_count} messages from {len(profiles)} senders "
        f"({cached} cached, {len(profiles) - cached} sent to the model)"
    )
    print(
        f"API calls: {classifier.api_calls}, tokens in: {classifier.input_tokens}, "
        f"out: {classifier.output_tokens}\n"
    )

    print(f"{'Category':<15}{'Senders':>8}{'Messages':>10}")
    for label, n in messages_per_cat.most_common():
        print(f"{label:<15}{senders_per_cat[label]:>8}{n:>10}")

    review = [r for r in results if r.needs_review]
    if review:
        print(f"\nNeeds review ({len(review)}):")
        for r in review:
            label = r.category.value if r.category else "-"
            print(f"  {r.address:<45} {r.reason} ({r.confidence:.2f}) -> {label}")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="mailsieve")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("stats", help="Top senders for the whole inbox")
    classify = commands.add_parser("classify", help="Classify senders with an LLM")
    classify.add_argument("--sample", type=int, default=100)
    args = parser.parse_args(argv)

    try:
        settings = Settings.from_env()
        if args.command == "stats":
            run_stats(settings)
        else:
            run_classify(settings, args.sample)
    except (ConfigError, MailboxError, ClassifierError) as exc:
        raise SystemExit(f"Error: {exc}") from None
