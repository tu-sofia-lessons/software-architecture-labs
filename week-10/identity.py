"""Who is using the assistant (provided). In W8 this came from a verified token."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Principal:
    user: str
    role: str                 # "student" | "admin"
    student_id: int | None    # set for students only


USERS = {
    "maria": Principal("maria", "student", 1),
    "ivan": Principal("ivan", "student", 2),
    "elena": Principal("elena", "student", 4),
    "registrar": Principal("registrar", "admin", None),
}
