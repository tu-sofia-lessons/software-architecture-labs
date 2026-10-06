"""Reporting command-line tool of the University Platform.

Usage:
    python cli.py courses              # core function: list courses
    python cli.py reports              # list available reports
    python cli.py report <name>        # print one report
"""
import sys
if sys.version_info < (3, 10):
    sys.exit("Нужен е Python 3.10+ / Python 3.10+ is required (you have %d.%d)." % sys.version_info[:2])
try:
    sys.stdout.reconfigure(errors="replace")      # consoles without UTF-8 (e.g. cp1251) must not crash
except (AttributeError, ValueError):
    pass


import data
import reports
from core.report_data import build_report_data


def main(argv):
    if not argv:
        print(__doc__)
        return 1
    command, args = argv[0], argv[1:]

    if command == "courses":
        for c in data.COURSES:
            print(f"{c['id']:>3}  {c['code']}  {c['title']:<25} cap {c['capacity']}")
    elif command == "reports":
        for name in reports.AVAILABLE:
            print(name)
    elif command == "report" and len(args) == 1:
        try:
            print(reports.generate(args[0], build_report_data()), end="")
        except reports.UnknownReport:
            print(f"Unknown report: {args[0]}")
            return 1
    else:
        print(__doc__)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
