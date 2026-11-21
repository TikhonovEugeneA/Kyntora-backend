from uuid import UUID, uuid4

from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String


class Base(DeclarativeBase):
    __abstract__ = True


class UserModel(Base):
    __tablename__ = "users"

    first_name: Mapped[str] = mapped_column(String(100))
    last_name: Mapped[str] = mapped_column(String(100))
    login: Mapped[str] = mapped_column(String(255), unique=True)
    hash_password: Mapped[str] = mapped_column(String(255))
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
