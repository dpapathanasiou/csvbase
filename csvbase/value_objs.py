from logging import getLogger
from typing import (
    Optional,
    Sequence,
    Type,
    Dict,
    Union,
    Mapping,
    List,
    Tuple,
    Set,
    cast,
    Any,
)
from typing_extensions import Literal
from uuid import UUID
from datetime import datetime, date, timedelta, timezone
from dataclasses import dataclass
import enum
import binascii

from dateutil.tz import gettz
from sqlalchemy import types as satypes

logger = getLogger(__name__)

# Preliminary version of a Row.  Another option would be to subclass tuple and
# implement __getattr__ to provide access by column
Row = Mapping["Column", Optional["PythonType"]]


@dataclass
class User:
    user_uuid: UUID
    username: str
    email: Optional[str]
    registered: datetime
    api_key: bytes
    timezone: str

    def hex_api_key(self) -> str:
        return binascii.hexlify(self.api_key).decode("utf-8")

    def tzfile(self) -> Any:
        """Returns the timezone "object" which you can pass as an argument into
        datetime.replace or datetime.now."""
        try:
            return gettz(self.timezone)
        except Exception as e:
            logger.exception("unable to load timezone for user, using UTC")
            return timezone.utc


@dataclass
class KeySet:
    """Used as a selector for keyset pagination

    https://use-the-index-luke.com/no-offset

    """

    columns: List["Column"]
    values: Tuple
    op: Literal["greater_than", "less_than"]
    size: int = 10


# sketch for filters
# @dataclass
# class KeySetNG:
#     filters: Sequence["BinaryFilter"]
#     size: Optional[int] = 10


# @dataclass
# class BinaryFilter:
#     lhs: Union["Column"]
#     rhs: Union["Column", "PythonType"]
#     op: "BinaryOp"


# @enum.unique
# class BinaryOp(enum.Enum):
#     EQ = 1
#     NQE = 2
#     GT = 3
#     GTE = 4
#     LT = 5
#     LTE = 6


@dataclass
class Page:
    """A page from a table"""

    # FIXME: This is pretty awful as an API.  eg it would be great to know if
    # row id X was in the page

    has_less: bool
    has_more: bool
    rows: Sequence[Row]

    def row_ids(self) -> Set[int]:
        return cast(Set[int], {row[ROW_ID_COLUMN] for row in self.rows})


@dataclass
class RowCount:
    exact: Optional[int]
    approx: int

    def best(self):
        return self.exact or self.approx


@dataclass
class Table:
    table_uuid: UUID
    username: str
    table_name: str
    is_public: bool
    caption: str
    data_licence: "DataLicence"
    columns: Sequence["Column"]
    created: datetime
    row_count: RowCount
    last_changed: datetime

    def has_caption(self) -> bool:
        return len(self.caption.strip()) > 0

    def user_columns(self) -> Sequence["Column"]:
        """Returns 'user_columns' - ie those not owned by csvbase."""
        return [
            column for column in self.columns if not column.name.startswith("csvbase_")
        ]

    def row_id_column(self) -> "Column":
        return self.columns[0]

    def age(self) -> timedelta:
        return self.created - datetime.now(timezone.utc)


@enum.unique
class DataLicence(enum.Enum):
    UNKNOWN = 0
    ALL_RIGHTS_RESERVED = 1
    PDDL = 2
    ODC_BY = 3
    ODBL = 4
    OGL = 5

    def render(self) -> str:
        return _DATA_LICENCE_PP_MAP[self]

    def short_render(self) -> str:
        return _DATA_LICENCE_SHORT_MAP[self]

    def is_free(self) -> bool:
        return self.value > 1


_DATA_LICENCE_PP_MAP = {
    DataLicence.UNKNOWN: "Unknown",
    DataLicence.ALL_RIGHTS_RESERVED: "All rights reserved",
    DataLicence.PDDL: "PDDL (public domain)",
    DataLicence.ODC_BY: "ODB-By (attribution required)",
    DataLicence.ODBL: "ODbl (attribution & sharealike)",
    DataLicence.OGL: "Open Government Licence",
}

_DATA_LICENCE_SHORT_MAP = {
    DataLicence.UNKNOWN: "Unknown",
    DataLicence.ALL_RIGHTS_RESERVED: "All rights reserved",
    DataLicence.PDDL: "Public domain",
    DataLicence.ODC_BY: "ODB-By",
    DataLicence.ODBL: "ODbl",
    DataLicence.OGL: "OGL",
}


@enum.unique
class ColumnType(enum.Enum):
    # These are ints because that int will eventually be used in a table
    # storing columns
    TEXT = 1
    INTEGER = 2
    FLOAT = 3
    BOOLEAN = 4
    DATE = 5

    def example(self) -> "PythonType":
        if self is ColumnType.TEXT:
            return "foo"
        elif self is ColumnType.INTEGER:
            return 1
        elif self is ColumnType.FLOAT:
            return 3.14
        elif self is ColumnType.BOOLEAN:
            return False
        else:
            return date(2018, 1, 3)

    @staticmethod
    def from_sql_type(sqla_type: str) -> "ColumnType":
        return _REVERSE_SQL_TYPE_MAP[sqla_type]

    def sqla_type(self) -> Type["SQLAlchemyType"]:
        """The equivalent SQLAlchemy type"""
        return _SQLA_TYPE_MAP[self]

    def pretty_name(self) -> str:
        """The presentation name of the type.  Intended for UIs."""
        return self.name.capitalize()

    def python_type(self) -> Type:
        return _PYTHON_TYPE_MAP[self]

    def pretty_type(self) -> str:
        """The "pretty" name of the type.  Intended for APIs."""
        return _PRETTY_TYPE_MAP[self]


PythonType = Union[int, bool, float, date, str, None]
SQLAlchemyType = Union[
    satypes.BigInteger,
    satypes.Boolean,
    satypes.Float,
    satypes.Date,
    satypes.Text,
]

_SQLA_TYPE_MAP: Dict["ColumnType", Type[SQLAlchemyType]] = {
    ColumnType.TEXT: satypes.Text,
    ColumnType.INTEGER: satypes.BigInteger,
    ColumnType.FLOAT: satypes.Float,
    ColumnType.BOOLEAN: satypes.Boolean,
    ColumnType.DATE: satypes.Date,
}

_REVERSE_SQL_TYPE_MAP = {
    "boolean": ColumnType.BOOLEAN,
    "bigint": ColumnType.INTEGER,
    "date": ColumnType.DATE,
    "double precision": ColumnType.FLOAT,
    "integer": ColumnType.INTEGER,
    "text": ColumnType.TEXT,
}

_PYTHON_TYPE_MAP = {
    ColumnType.TEXT: str,
    ColumnType.INTEGER: int,
    ColumnType.FLOAT: float,
    ColumnType.BOOLEAN: bool,
    ColumnType.DATE: date,
}

_PRETTY_TYPE_MAP = {
    ColumnType.TEXT: "string",
    ColumnType.INTEGER: "integer",
    ColumnType.FLOAT: "float",
    ColumnType.BOOLEAN: "boolean",
    ColumnType.DATE: "date",
}


@dataclass(frozen=True)
class Column:
    name: str
    type_: ColumnType


ROW_ID_COLUMN = Column("csvbase_row_id", type_=ColumnType.INTEGER)


@enum.unique
class ContentType(enum.Enum):
    CSV = "text/csv"
    HTML = "text/html"
    HTML_FORM = "application/x-www-form-urlencoded"
    JSON = "application/json"
    JSON_LINES = "application/x-jsonlines"  # no consensus
    PARQUET = "application/parquet"  # this is unofficial, but convenient
    XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

    @classmethod
    def from_file_extension(cls, file_extension: str) -> Optional["ContentType"]:
        return EXTENSION_MAP.get(file_extension)

    def pretty_name(self) -> str:
        return PRETTY_NAME_MAP[self]

    def file_extension(self) -> str:
        return EXTENSION_MAP_REVERSE[self]


EXTENSION_MAP: Mapping[str, ContentType] = {
    "html": ContentType.HTML,
    "csv": ContentType.CSV,
    "parquet": ContentType.PARQUET,
    "json": ContentType.JSON,
    "jsonl": ContentType.JSON_LINES,
    "xlsx": ContentType.XLSX,
}

EXTENSION_MAP_REVERSE = {v: k for k, v in EXTENSION_MAP.items()}


PRETTY_NAME_MAP: Mapping[ContentType, str] = {
    ContentType.HTML: "HTML",
    ContentType.CSV: "CSV",
    ContentType.PARQUET: "Parquet",
    ContentType.JSON: "JSON",
    ContentType.JSON_LINES: "JSON lines",
    ContentType.XLSX: "MS Excel",
}


@dataclass
class Quota:
    private_tables: int
    private_bytes: int


@dataclass
class Usage:
    """Represents the actual usage of a user - to be compared against their
    Quota.

    """

    public_tables: int
    public_bytes: int
    private_tables: int
    private_bytes: int

    def exceeds_quota(self, quota: Quota) -> bool:
        return (self.private_tables > quota.private_tables) or (
            self.private_bytes > quota.private_bytes
        )
