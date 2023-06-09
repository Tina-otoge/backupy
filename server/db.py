import secrets
from contextlib import contextmanager
from pathlib import Path

from sqlalchemy import ForeignKey, create_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped as Column
from sqlalchemy.orm import MappedAsDataclass, Session, declared_attr
from sqlalchemy.orm import mapped_column as column
from sqlalchemy.orm import relationship

from .config import SQL_ECHO


class Base(DeclarativeBase, MappedAsDataclass):
    @declared_attr.directive
    def __tablename__(cls) -> str:
        return cls.__name__.lower() + "s"


class File(Base):
    hash: Column[str] = column(primary_key=True)
    path: Column[str]


class User(Base):
    id: Column[int] = column(init=False, primary_key=True)
    name: Column[str]

    tokens: Column[list["Token"]] = relationship(
        default_factory=list, back_populates="user"
    )


class Token(Base):
    id: Column[int] = column(init=False, primary_key=True)
    user_id: Column[int] = column(ForeignKey("users.id"), init=False)
    random: Column[str] = column(default_factory=lambda: secrets.token_hex(16))

    user: Column["User"] = relationship(
        "User", uselist=False, default=None, back_populates="tokens"
    )

    def token(self) -> str:
        return f"{self.id}:{self.random}"

    @classmethod
    def from_token(cls, session, token: str):
        id, random = token.split(":")
        token = session.get(cls, int(id))
        if token is None or token.random != random:
            raise ValueError("Invalid token")
        return token


var_dir = Path("./var")
var_dir.mkdir(exist_ok=True)

engine = create_engine("sqlite+pysqlite:///./var/backupy.db", echo=SQL_ECHO)

Base.metadata.create_all(engine)


@contextmanager
def session() -> Session:
    with Session(engine) as s:
        with s.begin():
            yield s
