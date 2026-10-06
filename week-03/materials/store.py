"""The contract every material store must fulfil. The rest of the app depends only on this."""
from typing import Protocol


class MaterialStore(Protocol):
    def list(self, course_id: int) -> list[str]:
        """Names of the files of a course (empty list if none)."""

    def read(self, course_id: int, name: str) -> bytes:
        """Content of one file."""

    def write(self, course_id: int, name: str, data: bytes) -> None:
        """Store (or replace) one file."""
