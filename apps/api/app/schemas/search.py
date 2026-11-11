from enum import Enum


class SortByEnum(str, Enum):
    """Allowlisted sorting fields to prevent ORM/SQL column injection."""
    CREATED_AT = "created_at"
    CODE = "code"


class SortOrderEnum(str, Enum):
    """Allowlisted sorting order directions."""
    ASC = "asc"
    DESC = "desc"
