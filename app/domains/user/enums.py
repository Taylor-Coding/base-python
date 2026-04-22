from enum import StrEnum


class UserRole(StrEnum):
    MASTER = "master"
    ADMIN = "admin"
    USER = "user"
