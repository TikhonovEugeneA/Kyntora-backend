from pydantic import SecretStr

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.core.exceptions import InvalidToken, InvalidCredentials, UserAlreadyExists
from app.core.security import JWTManager, PasswordHasher
from app.db.repositories import UserRepository
from app.models.tokens import TokenPair
from app.models.user import User


class AuthService:
    def __init__(
        self,
        session: AsyncSession,
        repository: UserRepository,
        password_hasher: PasswordHasher,
        jwtmanager: JWTManager,
    ) -> None:
        self._session = session
        self._repository = repository
        self._password_hasher = password_hasher
        self._jwtmanager = jwtmanager

    @staticmethod
    def _normalize_login(login: str) -> str:
        return login.strip().lower()

    def _issue_tokens(self, user: User) -> TokenPair:
        return TokenPair(
            access_token=self._jwtmanager.create_access_token(
                user_id=user.id, first_name=user.first_name, last_name=user.last_name
            ),
            refresh_token=self._jwtmanager.create_refresh_token(user_id=user.id),
        )

    async def sign_up(
        self, first_name: str, last_name: str, login: str, password: str
    ) -> User:
        login = self._normalize_login(login)
        if await self._repository.get_by_login(login):
            raise UserAlreadyExists()
        user = User(
            first_name=first_name.strip(),
            last_name=last_name.strip(),
            login=login,
            hash_password=SecretStr(
                await self._password_hasher.hashing_password(password)
            ),
        )
        try:
            await self._repository.save(user)
            await self._session.commit()
        except IntegrityError as e:
            raise UserAlreadyExists() from e
        return user

    async def sign_in(self, *, login: str, password: str) -> TokenPair:
        login = self._normalize_login(login)
        user = await self._repository.get_by_login(login)
        if user is None:
            raise InvalidCredentials()
        is_valid = await self._password_hasher.verify_password(
            user.hash_password.get_secret_value(), password
        )
        if not is_valid:
            raise InvalidCredentials()
        return self._issue_tokens(user)

    async def update_access_token(self, refresh_token: str) -> TokenPair:
        payload = self._jwtmanager.decode_refresh_token(refresh_token)
        user = await self._repository.get_by_id(payload.sub)
        if user is None:
            raise InvalidToken()
        return self._issue_tokens(user)

    async def get_current_user(self, access_token: str) -> User:
        payload = self._jwtmanager.decode_access_token(access_token)
        user = await self._repository.get_by_id(payload.sub)
        if user is None:
            raise InvalidToken()
        return user
