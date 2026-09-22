from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import psycopg
from polymarket_history.infrastructure.settings import Settings

_MIGRATIONS_DIR = Path(__file__).resolve().parent / "migrations"


def main() -> int:
    settings = Settings.from_toml()
    dsn = settings.database.dsn.strip()
    if not dsn:
        print(
            "database.dsn is empty; set it in settings.toml to run migrations",
            file=sys.stderr,
        )
        return 1

    migrations = sorted(_MIGRATIONS_DIR.glob("*.sql"))
    if not migrations:
        print(f"no migrations found in {_MIGRATIONS_DIR}", file=sys.stderr)
        return 1

    try:
        with psycopg.connect(dsn, connect_timeout=5) as conn:
            _ensure_schema_migrations(conn)
            applied = _applied_versions(conn)
            for path in migrations:
                version = path.name
                if version in applied:
                    print(f"skip {version}")
                    continue
                sql = path.read_text(encoding="utf-8")
                with conn.transaction(), conn.cursor() as cur:
                    cur.execute(sql)
                    cur.execute(
                        "INSERT INTO schema_migrations (version) VALUES (%s)",
                        (version,),
                    )
                print(f"applied {version}")
    except psycopg.Error as exc:
        print(f"migration failed: {exc}", file=sys.stderr)
        return 1

    return 0


def _ensure_schema_migrations(conn: psycopg.Connection[Any]) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version TEXT PRIMARY KEY,
                applied_at TIMESTAMPTZ NOT NULL DEFAULT now()
            )
            """
        )
    conn.commit()


def _applied_versions(conn: psycopg.Connection[Any]) -> set[str]:
    with conn.cursor() as cur:
        cur.execute("SELECT version FROM schema_migrations")
        return {row[0] for row in cur.fetchall()}


if __name__ == "__main__":
    raise SystemExit(main())
