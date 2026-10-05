from email import policy
from email.parser import BytesHeaderParser

from mailsieve.domain import Sender

_parser = BytesHeaderParser(policy=policy.default)


def parse_sender(raw_header: bytes) -> Sender | None:
    try:
        header = _parser.parsebytes(raw_header)["From"]
        addresses = header.addresses if header is not None else ()
    except (ValueError, IndexError, AttributeError):
        return None

    if not addresses or not addresses[0].addr_spec:
        return None

    first = addresses[0]
    return Sender(address=first.addr_spec.lower(), name=first.display_name)
