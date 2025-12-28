from dataclasses import dataclass

@dataclass(frozen=True)
class User:
    id: int
    username: str
    role: str  # "student" | "mentor"

@dataclass(frozen=True)
class Exhibition:
    id: int
    theme: str
    description: str

@dataclass(frozen=True)
class Artwork:
    id: int
    exhibition_id: int
    filename: str
    path: str
