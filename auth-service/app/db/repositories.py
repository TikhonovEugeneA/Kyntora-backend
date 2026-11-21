from pydantic import SecretStr
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import User
from app.db.models import UserModel


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, user_id: UUID) -> User | None:
        model = await self._session.get(UserModel, user_id)
        return self.to_entity(model) if model else None

    async def get_by_login(self, login: str) -> User | None:
        model = await self._session.scalar(
            select(UserModel).where(UserModel.login == login)
        )
        return self.to_entity(model) if model else None

    async def save(self, user: User) -> None:
        model = UserModel(
            id=user.id,
            first_name=user.first_name,
            last_name=user.last_name,
            login=user.login,
            hash_password=user.hash_password.get_secret_value(),
        )
        self._session.add(model)
        await self._session.flush()

    @staticmethod
    def to_entity(model: UserModel) -> User:
        return User(
            id=model.id,
            first_name=model.first_name,
            last_name=model.last_name,
            login=model.login,
            hash_password=SecretStr(model.hash_password),
        )
