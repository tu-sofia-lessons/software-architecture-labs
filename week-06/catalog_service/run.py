"""Start the Catalogue Service:  python catalog_service/run.py [--port 8101]  (provided)."""
import sys
if sys.version_info < (3, 10):
    sys.exit("Нужен е Python 3.10+ / Python 3.10+ is required (you have %d.%d)." % sys.version_info[:2])
try:
    sys.stdout.reconfigure(errors="replace")      # consoles without UTF-8 (e.g. cp1251) must not crash
except (AttributeError, ValueError):
    pass

from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))   # to import httpkit
sys.path.insert(0, str(Path(__file__).parent))

import httpkit  # noqa: E402
from routes import ROUTES  # noqa: E402

if __name__ == "__main__":
    port = int(sys.argv[sys.argv.index("--port") + 1]) if "--port" in sys.argv else 8101
    print(f"Catalogue Service with {len(ROUTES)} route(s)", flush=True)
    httpkit.serve(ROUTES, port)
