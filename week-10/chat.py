"""Talk to the University Assistant agent.

Usage:
    python chat.py --user maria "Which of my courses still have seats?"
    python chat.py --user maria "Enroll me in Databases"
Users: maria, ivan, elena (students), registrar (admin).
"""
import sys
if sys.version_info < (3, 10):
    sys.exit("Нужен е Python 3.10+ / Python 3.10+ is required (you have %d.%d)." % sys.version_info[:2])
try:
    sys.stdout.reconfigure(errors="replace")      # consoles without UTF-8 (e.g. cp1251) must not crash
except (AttributeError, ValueError):
    pass

from pathlib import Path

import agent
import llm_client
from identity import USERS
from platform_api import Platform
from tools import build_tools


def ask_human(description):
    return input(f"The assistant wants to: {description}. Allow? [y/N] ").strip().lower() == "y"


def main(argv):
    if len(argv) != 3 or argv[0] != "--user" or argv[1] not in USERS:
        print(__doc__)
        return 1
    platform = Platform(Path(__file__).parent / "knowledge")
    result = agent.run(argv[2], USERS[argv[1]], build_tools(platform), llm_client.generate, ask_human)
    for entry in result.trace:
        print(f"  step {entry['step']}: {entry['call']:<45} {entry['verdict']:<15} → {entry['result']}")
    print(result.answer)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
