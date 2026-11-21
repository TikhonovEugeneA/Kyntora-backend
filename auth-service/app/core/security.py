from asyncio import to_thread
from datetime import UTC, datetime, timedelta
from typing import TypeVar
from uuid import UUID

from jwt import PyJWTError, ExpiredSignatureError, decode, encode
from pwdlib import PasswordHash

from app.core.exceptions import InvalidToken, ExpiredRefreshToken
from app.models.tokens import AccessTokenPayload, Payload, RefreshTokenPayload

P = TypeVar("P", bound=Payload)


class PasswordHasher:
    def __init__(self) -> None:
        self._hasher = PasswordHash.recommended()

    async def hashing_password(self, password: str) -> str:
        return await to_thread(self._hasher.hash, password)

    async def verify_password(self, hashed: str, plain_password: str) -> bool:
        return await to_thread(self._hasher.verify, plain_password, hashed)


class JWTManager:
    def __init__(
        self,
        *,
        secret: str,
        algorithm: str,
        access_ttl: timedelta,
        refresh_ttl: timedelta,
    ) -> None:
        self._secret = secret
        self._algorithm = algorithm
        self._access_ttl = access_ttl
        self._refresh_ttl = refresh_ttl

    def create_access_token(
        self,
        *,
        user_id: UUID,
        first_name: str,
        last_name: str,
    ) -> str:
        payload = AccessTokenPayload(
            sub=user_id,
            exp=datetime.now(UTC) + self._access_ttl,
            first_name=first_name,
            last_name=last_name,
        )
        return self._encode(payload)

    def create_refresh_token(self, *, user_id: UUID) -> str:
        payload = RefreshTokenPayload(
            sub=user_id, exp=datetime.now(UTC) + self._refresh_ttl
        )
        return self._encode(payload)

    def decode_access_token(self, token: str) -> AccessTokenPayload:
        return self._decode(token, AccessTokenPayload)

    def decode_refresh_token(self, token: str) -> RefreshTokenPayload:
        return self._decode(token, RefreshTokenPayload)

    def _encode(self, payload: Payload) -> str:
        return encode(payload.to_claims(), self._secret, algorithm=self._algorithm)

    def _decode(self, token: str, payload_cls: type[P]) -> P:
        try:
            claims = decode(
                token,
                self._secret,
                algorithms=[self._algorithm],
                options={"require": ["exp", "iat", "sub", "type"]},
            )
            return payload_cls.from_claims(claims)
        except ExpiredSignatureError:
            raise ExpiredRefreshToken()
        except (PyJWTError, ValueError, KeyError, TypeError) as e:
            raise InvalidToken() from e
