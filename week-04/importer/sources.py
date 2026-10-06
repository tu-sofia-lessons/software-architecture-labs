"""Reading source files (provided — not part of the lesson)."""
import csv


def read_csv(path, delimiter=","):
    """Return every row of a CSV file as a dict (column name -> raw text)."""
    with open(path, newline="", encoding="utf-8") as f:
        return [dict(row) for row in csv.DictReader(f, delimiter=delimiter)]
