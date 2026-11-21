from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, ClassVar, Self
from uuid import UUID


class TokenType(StrEnum):
    ACCESS = "ACCESS"
    REFRESH = "REFRESH"


def _utcnow() -> datetime:
    return datetime.now(UTC)


@dataclass(frozen=True, kw_only=True)
class Payload:

    type: ClassVar[TokenType]
    sub: UUID
    exp: datetime
    iat: datetime = field(default_factory=_utcnow)

    def __post_init__(self) -> None:
        if self.iat.tzinfo is None or self.exp.tzinfo is None:
            raise ValueError("iat и exp должны быть timezone-aware")
        if self.exp <= self.iat:
            raise ValueError("exp должен быть позже iat")

    def to_claims(self) -> dict[str, Any]:
        return {
            "sub": str(self.sub),
            "type": self.type.value,
            "iat": int(self.iat.timestamp()),
            "exp": int(self.exp.timestamp()),
        }

    @classmethod
    def _common_kwargs(cls, claims: dict[str, Any]) -> dict[str, Any]:
        if claims.get("type") != cls.type:
            raise ValueError(f"Ожидался {cls.type} токен")
        return {
            "sub": UUID(claims["sub"]),
            "iat": datetime.fromtimestamp(claims["iat"], UTC),
            "exp": datetime.fromtimestamp(claims["exp"], UTC),
        }


@dataclass(frozen=True, kw_only=True)
class AccessTokenPayload(Payload):

    type: ClassVar[TokenType] = TokenType.ACCESS
    first_name: str
    last_name: str

    def to_claims(self) -> dict[str, Any]:
        return {
            **super().to_claims(),
            "first_name": self.first_name,
            "last_name": self.last_name,
        }

    @classmethod
    def from_claims(cls, claims: dict[str, Any]) -> Self:
        return cls(
            **cls._common_kwargs(claims),
            first_name=claims["first_name"],
            last_name=claims["last_name"],
        )


@dataclass(frozen=True, kw_only=True)
class RefreshTokenPayload(Payload):

    type: ClassVar[TokenType] = TokenType.REFRESH

    @classmethod
    def from_claims(cls, claims: dict[str, Any]) -> Self:
        return cls(**cls._common_kwargs(claims))


@dataclass
class TokenPair:
    access_token: str
    refresh_token: str
