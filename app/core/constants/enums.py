from enum import StrEnum


class UserRole(StrEnum):
    MASTER = "MASTER"
    ADMIN = "ADMIN"
    USER = "USER"


class ActiveStatus(StrEnum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    DELETED = "DELETED"
