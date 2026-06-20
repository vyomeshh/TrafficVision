"""
TrafficVision AI - Database Connection
========================================
Provides PostgreSQL connectivity with automatic SQLite fallback for
local development environments where PostgreSQL is unavailable.
"""

import os
import json
import logging
import sqlite3
from pathlib import Path

try:
    import psycopg2
    import psycopg2.extras
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
DATABASE_URL: str = os.environ.get(
    'DATABASE_URL',
    'postgresql://postgres:postgres@localhost:5432/trafficvision',
)

# SQLite fallback path (lives beside the database package)
_SQLITE_PATH: Path = Path(__file__).resolve().parent / 'trafficvision.db'

# Module-level flag so callers can check which backend is active
_using_sqlite: bool = False

# ---------------------------------------------------------------------------
# SQL Schemas
# ---------------------------------------------------------------------------
_POSTGRES_SCHEMA = """
CREATE TABLE IF NOT EXISTS violations (
    id SERIAL PRIMARY KEY,
    detection_id VARCHAR(50) UNIQUE NOT NULL,
    license_plate VARCHAR(20),
    vehicle_type VARCHAR(30),
    violation_type VARCHAR(50),
    confidence FLOAT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    location VARCHAR(100) DEFAULT 'Junction Zone 4',
    image_path VARCHAR(255),
    annotated_image_path VARCHAR(255),
    bbox_data JSONB,
    status VARCHAR(20) DEFAULT 'PENDING'
);

CREATE TABLE IF NOT EXISTS analytics_summary (
    id SERIAL PRIMARY KEY,
    date DATE DEFAULT CURRENT_DATE,
    violation_type VARCHAR(50),
    count INTEGER DEFAULT 0,
    avg_confidence FLOAT
);
"""

_SQLITE_SCHEMA = """
CREATE TABLE IF NOT EXISTS violations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    detection_id VARCHAR(50) UNIQUE NOT NULL,
    license_plate VARCHAR(20),
    vehicle_type VARCHAR(30),
    violation_type VARCHAR(50),
    confidence REAL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    location VARCHAR(100) DEFAULT 'Junction Zone 4',
    image_path VARCHAR(255),
    annotated_image_path VARCHAR(255),
    bbox_data TEXT,
    status VARCHAR(20) DEFAULT 'PENDING'
);

CREATE TABLE IF NOT EXISTS analytics_summary (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date DATE DEFAULT (DATE('now')),
    violation_type VARCHAR(50),
    count INTEGER DEFAULT 0,
    avg_confidence REAL
);
"""


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def init_db() -> None:
    """Create the required tables if they do not already exist.

    Attempts PostgreSQL first.  If ``psycopg2`` is not installed or the
    server is unreachable, falls back to a local SQLite database.
    """
    global _using_sqlite

    if PSYCOPG2_AVAILABLE:
        try:
            conn = psycopg2.connect(DATABASE_URL)
            conn.autocommit = True
            cur = conn.cursor()

            # Execute each statement separately (psycopg2 doesn't support
            # multi-statement strings reliably in all versions).
            for statement in _POSTGRES_SCHEMA.strip().split(';'):
                statement = statement.strip()
                if statement:
                    cur.execute(statement)

            cur.close()
            conn.close()
            _using_sqlite = False
            logger.info("PostgreSQL database initialised successfully.")
            return
        except Exception as exc:
            logger.warning(
                "PostgreSQL connection failed (%s). Falling back to SQLite.", exc,
            )

    # SQLite fallback
    _using_sqlite = True
    logger.info("Using SQLite database at %s", _SQLITE_PATH)

    conn = sqlite3.connect(str(_SQLITE_PATH))
    cur = conn.cursor()
    cur.executescript(_SQLITE_SCHEMA)
    conn.commit()
    conn.close()
    logger.info("SQLite database initialised successfully.")


def get_connection():
    """Return a new database connection.

    Returns
    -------
    psycopg2.connection | sqlite3.Connection
        A connection object for the active backend.  The caller is
        responsible for calling :func:`close_connection` when done.
    """
    global _using_sqlite

    if not _using_sqlite and PSYCOPG2_AVAILABLE:
        try:
            conn = psycopg2.connect(DATABASE_URL)
            logger.debug("Opened PostgreSQL connection.")
            return conn
        except Exception as exc:
            logger.warning(
                "PostgreSQL unavailable (%s) – falling back to SQLite.", exc,
            )
            _using_sqlite = True

    # SQLite
    conn = sqlite3.connect(str(_SQLITE_PATH))
    conn.row_factory = sqlite3.Row  # enables dict-like access on rows
    logger.debug("Opened SQLite connection (%s).", _SQLITE_PATH)
    return conn


def close_connection(conn) -> None:
    """Safely close a database connection.

    Parameters
    ----------
    conn : psycopg2.connection | sqlite3.Connection
        The connection to close.
    """
    if conn is None:
        return
    try:
        conn.close()
        logger.debug("Database connection closed.")
    except Exception as exc:
        logger.error("Error closing connection: %s", exc)


def is_using_sqlite() -> bool:
    """Return ``True`` if the module is currently using the SQLite fallback."""
    return _using_sqlite
