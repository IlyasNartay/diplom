import enum

from sqlalchemy import Enum, String
from sqlalchemy.orm import Mapped, mapped_column

from common.database import Base


class Role(str, enum.Enum):
    user = "user"
    admin = "admin"


class User(Base):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(100), nullable=True)

    role: Mapped[Role] = mapped_column(Enum(Role), default=Role.user, nullable=False)
