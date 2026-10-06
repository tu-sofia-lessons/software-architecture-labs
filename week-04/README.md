# Week 4 — starter: Student import (one big function)

Registrar's import tool. Admissions works through one legacy function; Erasmus is not supported yet.
Python 3.10+, no installs (Windows: `py -3` instead of `python`).

    python import_cli.py admissions
    python import_cli.py erasmus
    python verify.py                     # REQ lines are graded, [path] lines are hints

Files: data/*.csv (sources), importer/pipeline.py (provided runner), importer/legacy_import.py (the blob).
Second Punch: the assistant releases punch-04.zip at 15:50; unzip it here, then `python verify.py --punch`.
Your lab guide: weeks/week-04/student-guide.md
