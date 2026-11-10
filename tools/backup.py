"""SQLite online backup and offline integrity verification; never overwrite files."""

import argparse
import sqlite3
from pathlib import Path


def backup(source: Path, destination: Path) -> None:
    if not source.is_file():
        raise ValueError("Source database does not exist")
    # Exclusive creation protects existing backups. On error preserve the failed
    # artifact for inspection; do not silently delete user files.
    with destination.open("xb"):
        pass
    with sqlite3.connect(source.resolve().as_uri() + "?mode=ro", uri=True, timeout=5) as original:
        with sqlite3.connect(destination) as copy:
            original.backup(copy)
            result = copy.execute("PRAGMA integrity_check").fetchone()[0]
            if result != "ok":
                raise ValueError("Backup integrity verification failed")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    backup(args.source, args.destination)
    print("Backup completed and integrity_check passed")


if __name__ == "__main__":
    main()
