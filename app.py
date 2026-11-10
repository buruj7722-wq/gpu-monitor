"""Compatible entry point: python app.py (one worker, loopback only)."""

from monitor.api import create_app
from monitor.cli import main

app = create_app()

if __name__ == "__main__":
    main()
