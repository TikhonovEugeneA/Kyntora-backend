import pytest
from pydantic import SecretStr
from sqlalchemy.exc import IntegrityError

from app.core.exceptions import UserAlreadyExists

from .conftest import HASHED_PASSWORD, PASSWORD


async def sign_up(
    service, *, login="ivan@mail.com", first_name="Ivan", last_name="Petrov"
):
    return await service.sign_up(
        first_name=first_name, last_name=last_name, login=login, password=PASSWORD
    )


async def test_saves_user_with_hashed_password_and_commits(
    service, repository, password_hasher, session
):
    user = await sign_up(service)

    password_hasher.hashing_password.assert_awaited_once_with(PASSWORD)
    repository.save.assert_awaited_once()
    saved = repository.save.await_args.args[0]
    assert saved is user
    assert (saved.first_name, saved.last_name, saved.login) == (
        "Ivan",
        "Petrov",
        "ivan@mail.com",
    )
    assert isinstance(saved.hash_password, SecretStr)
    assert saved.hash_password.get_secret_value() == HASHED_PASSWORD
    session.commit.assert_awaited_once()


async def test_plain_password_is_never_stored(service, repository):
    await sign_up(service)

    saved = repository.save.await_args.args[0]
    assert saved.hash_password.get_secret_value() != PASSWORD


async def test_saves_then_commits_in_that_order(service, repository, session):
    calls: list[str] = []
    repository.save.side_effect = lambda _user: calls.append("save")
    session.commit.side_effect = lambda: calls.append("commit")

    await sign_up(service)

    assert calls == ["save", "commit"]


@pytest.mark.parametrize(
    "raw_login", ["Ivan@Mail.com", "  ivan@mail.com  ", "IVAN@MAIL.COM"]
)
async def test_login_is_normalized_before_lookup_and_persist(
    service, repository, raw_login
):
    user = await sign_up(service, login=raw_login)

    repository.get_by_login.assert_awaited_once_with("ivan@mail.com")
    saved = repository.save.await_args.args[0]
    assert saved.login == "ivan@mail.com"
    assert user.login == "ivan@mail.com"


async def test_names_are_trimmed(service):
    user = await sign_up(service, first_name="  Ivan ", last_name=" Petrov  ")

    assert (user.first_name, user.last_name) == ("Ivan", "Petrov")


async def test_sign_up_does_not_issue_tokens(service, jwt_manager):
    await sign_up(service)

    jwt_manager.create_access_token.assert_not_called()
    jwt_manager.create_refresh_token.assert_not_called()


async def test_existing_login_is_rejected_before_hashing_or_saving(
    service, repository, password_hasher, session, existing_user
):
    repository.get_by_login.return_value = existing_user

    with pytest.raises(UserAlreadyExists):
        await sign_up(service, login="IVAN@mail.com")

    password_hasher.hashing_password.assert_not_awaited()
    repository.save.assert_not_awaited()
    session.commit.assert_not_awaited()


async def test_integrity_error_on_save_becomes_user_already_exists(
    service, repository, session
):
    repository.save.side_effect = IntegrityError("INSERT", {}, Exception("duplicate"))

    with pytest.raises(UserAlreadyExists):
        await sign_up(service)

    session.commit.assert_not_awaited()


async def test_integrity_error_on_commit_becomes_user_already_exists(
    service, repository, session
):
    session.commit.side_effect = IntegrityError("INSERT", {}, Exception("duplicate"))

    with pytest.raises(UserAlreadyExists):
        await sign_up(service)

    repository.save.assert_awaited_once()
    session.commit.assert_awaited_once()
