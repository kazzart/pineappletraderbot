from enum import Enum


class Role(Enum):
    ADMIN = 1
    MODERATOR = 2
    USER = 3


class Mode(Enum):
    LEFT = 1
    RIGHT = 2
    ANY = 3
