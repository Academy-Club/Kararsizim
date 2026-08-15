import hashlib
import secrets
import string

from django.conf import settings

_PUBLIC_ID_ALPHABET = string.ascii_letters + string.digits  # base62


def generate_public_id(length: int = 12) -> str:
    return "".join(secrets.choice(_PUBLIC_ID_ALPHABET) for _ in range(length))


def get_voter_key(request):
    if not request.session.session_key:
        request.session.save()
    raw = f"{request.session.session_key}{settings.VOTER_KEY_SALT}"
    return hashlib.sha256(raw.encode()).hexdigest()
