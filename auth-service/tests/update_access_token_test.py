import pytest

from app.core.exceptions import InvalidToken
from app.models.tokens import TokenPair

from .conftest import ACCESS_TOKEN

REFRESH_TOKEN_INPUT = "some-refresh-token"


@pytest.fixture
def valid_refresh(jwt_manager, repository, refresh_payload, existing_user):
    jwt_manager.decode_refresh_token.return_value = refresh_payload
    repository.get_by_id.return_value = existing_user
    return refresh_payload


async def test_returns_new_token_pair(service, valid_refresh, jwt_manager):
    jwt_manager.create_refresh_token.return_value = "new-refresh-token"

    pair = await service.update_access_token(REFRESH_TOKEN_INPUT)

    assert pair == TokenPair(
        access_token=ACCESS_TOKEN, refresh_token="new-refresh-token"
    )


async def test_user_is_looked_up_by_id_from_token(
    service, valid_refresh, jwt_manager, repository
):
    await service.update_access_token(REFRESH_TOKEN_INPUT)

    jwt_manager.decode_refresh_token.assert_called_once_with(REFRESH_TOKEN_INPUT)
    repository.get_by_id.assert_awaited_once_with(valid_refresh.sub)


async def test_new_tokens_are_issued_for_the_token_owner(
    service, valid_refresh, jwt_manager, existing_user
):
    await service.update_access_token(REFRESH_TOKEN_INPUT)

    jwt_manager.create_access_token.assert_called_once_with(
        user_id=existing_user.id, first_name="Ivan", last_name="Petrov"
    )
    jwt_manager.create_refresh_token.assert_called_once_with(user_id=existing_user.id)


async def test_refresh_does_not_write_to_database(
    service, valid_refresh, repository, session
):
    await service.update_access_token(REFRESH_TOKEN_INPUT)

    repository.save.assert_not_awaited()
    session.commit.assert_not_awaited()


async def test_invalid_or_expired_token_is_rejected_without_touching_database(
    service, jwt_manager, repository
):
    jwt_manager.decode_refresh_token.side_effect = InvalidToken()

    with pytest.raises(InvalidToken):
        await service.update_access_token(REFRESH_TOKEN_INPUT)

    repository.get_by_id.assert_not_awaited()
    jwt_manager.create_access_token.assert_not_called()
    jwt_manager.create_refresh_token.assert_not_called()


async def test_token_of_deleted_user_is_rejected(
    service, jwt_manager, repository, refresh_payload
):
    jwt_manager.decode_refresh_token.return_value = refresh_payload
    repository.get_by_id.return_value = None

    with pytest.raises(InvalidToken):
        await service.update_access_token(REFRESH_TOKEN_INPUT)

    jwt_manager.create_access_token.assert_not_called()
    jwt_manager.create_refresh_token.assert_not_called()
