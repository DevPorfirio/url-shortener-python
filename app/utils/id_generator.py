import secrets
import string

ALPHABET = string.ascii_letters + string.digits


def generate_short_code(length: int = 8) -> str:
    if length < 4:
        raise ValueError("Short code length must be at least 4 characters")
    return "".join(secrets.choice(ALPHABET) for _ in range(length))
