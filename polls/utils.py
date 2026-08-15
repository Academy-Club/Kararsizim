import secrets
import string

_PUBLIC_ID_ALPHABET = string.ascii_letters + string.digits  # base62


def generate_public_id(length: int = 12) -> str:
    return "".join(secrets.choice(_PUBLIC_ID_ALPHABET) for _ in range(length))
