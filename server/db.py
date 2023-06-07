from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped as Column
from sqlalchemy.orm import declared_attr
from sqlalchemy.orm import mapped_column as column


class Base(DeclarativeBase):
    @declared_attr.directive
    def __tablename__(cls) -> str:
        return cls.__name__.lower() + "s"


class File(Base):
    hash: Column[str] = column(primary_key=True)
    path: Column[str]


var_dir = Path("./var")
var_dir.mkdir(exist_ok=True)

engine = create_engine("sqlite+pysqlite:///./var/backupy.db", echo=True)

Base.metadata.create_all(engine)
