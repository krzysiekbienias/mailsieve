from email import policy
from email.parser import BytesHeaderParser

from mailsieve.domain import MessageInfo, Sender

_parser = BytesHeaderParser(policy=policy.default)


def parse_message(raw_header: bytes) -> MessageInfo | None:
    try:
        message = _parser.parsebytes(raw_header)
        from_header = message["From"]
        addresses = from_header.addresses if from_header is not None else ()
        subject = str(message["Subject"] or "")
    except (ValueError, IndexError, AttributeError):
        return None

    if not addresses or not addresses[0].addr_spec:
        return None

    first = addresses[0]
    sender = Sender(address=first.addr_spec.lower(), name=first.display_name)
    return MessageInfo(sender=sender, subject=subject.strip())


def parse_sender(raw_header: bytes) -> Sender | None:
    message = parse_message(raw_header)
    return message.sender if message is not None else None
