import pytest

from app.core.exceptions import InvalidCredentials
from app.models.tokens import TokenPair

from .conftest import ACCESS_TOKEN, PASSWORD, REFRESH_TOKEN, STORED_HASH


async def sign_in(service, *, login="ivan@mail.com", password=PASSWORD):
    return await service.sign_in(login=login, password=password)


@pytest.fixture
def known_user(repository, existing_user):
    repository.get_by_login.return_value = existing_user
    return existing_user


async def test_returns_token_pair(service, known_user):
    pair = await sign_in(service)

    assert pair == TokenPair(access_token=ACCESS_TOKEN, refresh_token=REFRESH_TOKEN)


async def test_verifies_password_against_stored_hash(
    service, known_user, password_hasher
):
    await sign_in(service)

    password_hasher.verify_password.assert_awaited_once_with(STORED_HASH, PASSWORD)


async def test_tokens_are_issued_for_this_user(service, known_user, jwt_manager):
    await sign_in(service)

    jwt_manager.create_access_token.assert_called_once_with(
        user_id=known_user.id, first_name="Ivan", last_name="Petrov"
    )
    jwt_manager.create_refresh_token.assert_called_once_with(user_id=known_user.id)


@pytest.mark.parametrize(
    "raw_login", ["Ivan@Mail.com", "  ivan@mail.com  ", "IVAN@MAIL.COM"]
)
async def test_login_is_normalized_before_lookup(
    service, repository, known_user, raw_login
):
    await sign_in(service, login=raw_login)

    repository.get_by_login.assert_awaited_once_with("ivan@mail.com")


async def test_sign_in_does_not_write_to_database(
    service, known_user, repository, session
):
    await sign_in(service)

    repository.save.assert_not_awaited()
    session.commit.assert_not_awaited()


async def test_wrong_password_is_rejected_and_no_tokens_issued(
    service, known_user, password_hasher, jwt_manager
):
    password_hasher.verify_password.return_value = False

    with pytest.raises(InvalidCredentials):
        await sign_in(service)

    jwt_manager.create_access_token.assert_not_called()
    jwt_manager.create_refresh_token.assert_not_called()


async def test_unknown_login_is_rejected_without_verifying_password(
    service, password_hasher, jwt_manager
):
    with pytest.raises(InvalidCredentials):
        await sign_in(service, login="nobody@mail.com")

    password_hasher.verify_password.assert_not_awaited()
    jwt_manager.create_access_token.assert_not_called()
    jwt_manager.create_refresh_token.assert_not_called()


async def test_does_not_reveal_whether_login_exists(
    service, repository, password_hasher, existing_user
):
    with pytest.raises(InvalidCredentials) as unknown_login:
        await sign_in(service, login="nobody@mail.com")

    repository.get_by_login.return_value = existing_user
    password_hasher.verify_password.return_value = False
    with pytest.raises(InvalidCredentials) as wrong_password:
        await sign_in(service)

    assert unknown_login.value.status_code == wrong_password.value.status_code
    assert unknown_login.value.detail == wrong_password.value.detail
