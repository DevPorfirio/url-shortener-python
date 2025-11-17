from datetime import UTC, datetime

from app.core.security import create_access_token, create_refresh_token, decode_token
from app.schemas.auth import TokenPayload


class TokenService:
    def create_tokens(self, subject: str) -> tuple[str, str]:
        return create_access_token(subject), create_refresh_token(subject)

    def decode(self, token: str) -> TokenPayload:
        payload = decode_token(token)
        return TokenPayload(**payload)

    def verify_token(self, token: str, expected_type: str = "access") -> TokenPayload:
        payload = self.decode(token)
        if payload.type != expected_type:
            raise ValueError("Invalid token type")
        expiration = (
            payload.exp
            if isinstance(payload.exp, datetime)
            else datetime.fromtimestamp(payload.exp, tz=UTC)
        )
        if expiration <= datetime.now(UTC):
            raise ValueError("Token expired")
        return payload
