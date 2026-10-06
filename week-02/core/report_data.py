"""Builds the read-only snapshot that every report receives (provided)."""
from dataclasses import dataclass
from types import MappingProxyType

import data


@dataclass(frozen=True)
class ReportData:
    """What a report is allowed to see: read-only copies of students, courses, enrollments."""
    students: tuple
    courses: tuple
    enrollments: tuple


def _frozen(rows):
    return tuple(MappingProxyType(dict(row)) for row in rows)


def build_report_data() -> ReportData:
    """Take a read-only snapshot of the core data."""
    return ReportData(
        students=_frozen(data.STUDENTS),
        courses=_frozen(data.COURSES),
        enrollments=_frozen(data.ENROLLMENTS),
    )
