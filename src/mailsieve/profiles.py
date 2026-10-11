from collections.abc import Iterable

from mailsieve.domain import MessageInfo, SenderProfile


def build_profiles(
    messages: Iterable[MessageInfo], max_subjects: int = 3
) -> list[SenderProfile]:
    names: dict[str, str] = {}
    subjects: dict[str, list[str]] = {}
    counts: dict[str, int] = {}

    for message in messages:
        address = message.sender.address
        counts[address] = counts.get(address, 0) + 1
        if message.sender.name:
            names[address] = message.sender.name
        bucket = subjects.setdefault(address, [])
        if message.subject and len(bucket) < max_subjects:
            bucket.append(message.subject)

    profiles = [
        SenderProfile(
            address=address,
            name=names.get(address, ""),
            subjects=tuple(subjects.get(address, [])),
            message_count=count,
        )
        for address, count in counts.items()
    ]
    return sorted(profiles, key=lambda p: p.message_count, reverse=True)
