from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, SecretStr, field_validator

MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_LENGTH = 32


def _check_max(value: SecretStr) -> SecretStr:
    if len(value.get_secret_value()) > MAX_PASSWORD_LENGTH:
        raise ValueError(f"Пароль не длиннее {MAX_PASSWORD_LENGTH} символов")
    return value


class SignUpRequest(BaseModel):
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    login: str = Field(min_length=3, max_length=255)
    password: SecretStr

    @field_validator("password")
    @classmethod
    def _check_password(cls, v: SecretStr) -> SecretStr:
        if len(v.get_secret_value()) < MIN_PASSWORD_LENGTH:
            raise ValueError(f"Пароль не короче {MIN_PASSWORD_LENGTH} символов")
        return _check_max(v)


class SignInRequest(BaseModel):
    login: str = Field(max_length=255)
    password: SecretStr

    @field_validator("password")
    @classmethod
    def _check_password(cls, v: SecretStr) -> SecretStr:
        return _check_max(v)


class RefreshRequest(BaseModel):
    refresh_token: str


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    first_name: str
    last_name: str
    login: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
