from collections.abc import AsyncIterator
from datetime import timedelta

from dishka import Provider, Scope, provide
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)


from app.core.security import JWTManager, PasswordHasher
from app.core.settings import Settings, get_settings
from app.db.repositories import UserRepository
from app.services.auth import AuthService


class AppProvider(Provider):
    @provide(scope=Scope.APP)
    def settings(self) -> Settings:
        return get_settings()

    @provide(scope=Scope.APP)
    async def engine(self, settings: Settings) -> AsyncIterator[AsyncEngine]:
        database = settings.database
        engine = create_async_engine(
            database.url.get_secret_value(),
            echo=database.echo,
            echo_pool=database.echo_pool,
            pool_pre_ping=database.pool_pre_ping,
            pool_size=database.pool_size,
            max_overflow=database.max_overflow,
        )
        yield engine
        await engine.dispose()

    @provide(scope=Scope.APP)
    def session_factory(self, engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
        return async_sessionmaker(engine, expire_on_commit=False)

    @provide(scope=Scope.APP)
    def jwt_manager(self, settings: Settings) -> JWTManager:
        auth = settings.auth
        return JWTManager(
            secret=auth.secret_key.get_secret_value(),
            algorithm=auth.algorithm,
            access_ttl=timedelta(minutes=auth.access_token_expire_minutes),
            refresh_ttl=timedelta(days=auth.refresh_token_expire_days),
        )

    password_hasher = provide(PasswordHasher, scope=Scope.APP)

    @provide(scope=Scope.REQUEST)
    async def session(
        self, factory: async_sessionmaker[AsyncSession]
    ) -> AsyncIterator[AsyncSession]:
        async with factory() as session:
            yield session

    user_repository = provide(UserRepository, scope=Scope.REQUEST)
    auth_service = provide(AuthService, scope=Scope.REQUEST)
