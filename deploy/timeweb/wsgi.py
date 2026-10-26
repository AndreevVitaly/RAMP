"""Copy to SITE_DIR/public_html/wsgi.py on Timeweb virtual hosting."""

import os
import sys
from pathlib import Path


site_dir = Path(__file__).resolve().parent.parent
activate_this = site_dir / "venv" / "bin" / "activate_this.py"
if not activate_this.is_file():
    raise RuntimeError(f"Virtualenv activation script not found: {activate_this}")
exec(compile(activate_this.read_bytes(), str(activate_this), "exec"), {"__file__": str(activate_this)})

backend_dir = site_dir / "ramp" / "backend"
sys.path.insert(0, str(backend_dir))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

# Timeweb's Python 3.10 mod_wsgi can stall on the standard sqlite3 module.
# Load the private configuration before Django so PostgreSQL deployments do
# not require this Timeweb-specific SQLite replacement.
from dotenv import load_dotenv

load_dotenv(backend_dir / ".env")
if os.getenv("USE_SQLITE", "false").lower() == "true":
    __import__("pysqlite3")
    sys.modules["sqlite3"] = sys.modules.pop("pysqlite3")

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()
