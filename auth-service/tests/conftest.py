from datetime import UTC, datetime, timedelta

import pytest
from pydantic import SecretStr

from app.core.security import JWTManager, PasswordHasher
from app.db.repositories import UserRepository
from app.models.tokens import RefreshTokenPayload
from app.models.user import User
from app.services.auth import AuthService

PASSWORD = "password123"
STORED_HASH = "stored-hash"
HASHED_PASSWORD = "hashed-password"
ACCESS_TOKEN = "access-token"
REFRESH_TOKEN = "refresh-token"


@pytest.fixture
def session(mocker):
    s = mocker.MagicMock(spec_set=["commit", "rollback", "add", "flush", "execute"])
    s.commit = mocker.AsyncMock()
    s.rollback = mocker.AsyncMock()
    s.flush = mocker.AsyncMock()
    s.execute = mocker.AsyncMock()
    return s


@pytest.fixture
def repository(mocker):
    repo = mocker.MagicMock(spec_set=UserRepository)
    repo.get_by_login = mocker.AsyncMock(return_value=None)
    repo.get_by_id = mocker.AsyncMock(return_value=None)
    repo.save = mocker.AsyncMock()
    return repo


@pytest.fixture
def password_hasher(mocker):
    hasher = mocker.MagicMock(spec_set=PasswordHasher)
    hasher.hashing_password = mocker.AsyncMock(return_value=HASHED_PASSWORD)
    hasher.verify_password = mocker.AsyncMock(return_value=True)
    return hasher


@pytest.fixture
def jwt_manager(mocker):
    jwt = mocker.MagicMock(spec_set=JWTManager)
    jwt.create_access_token = mocker.MagicMock(return_value=ACCESS_TOKEN)
    jwt.create_refresh_token = mocker.MagicMock(return_value=REFRESH_TOKEN)
    jwt.decode_refresh_token = mocker.MagicMock()
    jwt.decode_access_token = mocker.MagicMock()
    return jwt


@pytest.fixture
def service(session, repository, password_hasher, jwt_manager):
    return AuthService(session, repository, password_hasher, jwt_manager)


@pytest.fixture
def existing_user():
    return User(
        first_name="Ivan",
        last_name="Petrov",
        login="ivan@mail.com",
        hash_password=SecretStr(STORED_HASH),
    )


@pytest.fixture
def refresh_payload(existing_user):
    return RefreshTokenPayload(
        sub=existing_user.id, exp=datetime.now(UTC) + timedelta(days=30)
    )
