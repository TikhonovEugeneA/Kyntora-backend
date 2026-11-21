from dataclasses import dataclass, field
from uuid import UUID, uuid4
from pydantic import SecretStr


@dataclass(kw_only=True)
class User:
    id: UUID = field(default_factory=uuid4)
    first_name: str
    last_name: str
    login: str
    hash_password: SecretStr
