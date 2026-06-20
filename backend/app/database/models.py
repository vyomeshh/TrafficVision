"""
TrafficVision AI - Database Models / Operations
=================================================
CRUD helpers and analytics queries for the ``violations`` and
``analytics_summary`` tables.  All functions handle both PostgreSQL
and SQLite backends transparently.
"""

import json
import logging
import sqlite3
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

try:
    import psycopg2
    import psycopg2.extras
except ImportError:
    psycopg2 = None  # type: ignore[assignment]

from .connection import get_connection, close_connection, is_using_sqlite

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _placeholder() -> str:
    """Return the correct parameter placeholder for the active backend."""
    return '?' if is_using_sqlite() else '%s'


def _row_to_dict(row, cursor=None) -> Dict[str, Any]:
    """Convert a database row to a plain dict.

    Works for both ``sqlite3.Row`` objects and ``psycopg2``
    ``RealDictCursor`` / regular tuples (when a cursor with
    ``description`` is provided).
    """
    if isinstance(row, dict):
        return row
    if isinstance(row, sqlite3.Row):
        return dict(row)
    # psycopg2 regular tuple – use cursor.description
    if cursor and hasattr(cursor, 'description') and cursor.description:
        columns = [col.name for col in cursor.description]
        return dict(zip(columns, row))
    return {'_raw': row}


def _json_dumps(obj) -> str:
    """Serialise *obj* to a JSON string (safe for SQLite TEXT columns)."""
    if obj is None:
        return None  # type: ignore[return-value]
    if isinstance(obj, str):
        return obj
    return json.dumps(obj)


def _json_loads(val):
    """Deserialise a JSON column value."""
    if val is None:
        return None
    if isinstance(val, dict):
        return val
    try:
        return json.loads(val)
    except (json.JSONDecodeError, TypeError):
        return val


# ---------------------------------------------------------------------------
# ID Generation
# ---------------------------------------------------------------------------

_id_counter: int = 0


def generate_detection_id() -> str:
    """Generate a unique detection ID in the format ``TR-YYYY-NNN``.

    The counter resets each time the process restarts; uniqueness within
    a persistent store is enforced by the ``UNIQUE`` constraint on the
    ``detection_id`` column.
    """
    global _id_counter
    _id_counter += 1
    year = datetime.now().year
    return f"TR-{year}-{_id_counter:03d}"


# ---------------------------------------------------------------------------
# CRUD – Violations
# ---------------------------------------------------------------------------

def insert_violation(data: Dict[str, Any]) -> str:
    """Insert a new violation record.

    Parameters
    ----------
    data : dict
        Keys may include: ``license_plate``, ``vehicle_type``,
        ``violation_type``, ``confidence``, ``location``, ``image_path``,
        ``annotated_image_path``, ``bbox_data``, ``status``.

    Returns
    -------
    str
        The ``detection_id`` assigned to the new record.
    """
    detection_id = data.get('detection_id') or generate_detection_id()
    ph = _placeholder()

    sql = (
        f"INSERT INTO violations "
        f"(detection_id, license_plate, vehicle_type, violation_type, "
        f"confidence, location, image_path, annotated_image_path, "
        f"bbox_data, status) "
        f"VALUES ({ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, "
        f"{ph}, {ph})"
    )

    bbox_data = data.get('bbox_data')
    if is_using_sqlite():
        bbox_data = _json_dumps(bbox_data)
    elif isinstance(bbox_data, (dict, list)):
        bbox_data = json.dumps(bbox_data)

    params = (
        detection_id,
        data.get('license_plate'),
        data.get('vehicle_type'),
        data.get('violation_type'),
        data.get('confidence'),
        data.get('location', 'Junction Zone 4'),
        data.get('image_path'),
        data.get('annotated_image_path'),
        bbox_data,
        data.get('status', 'PENDING'),
    )

    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(sql, params)
        conn.commit()
        logger.info("Inserted violation %s", detection_id)
    except Exception as exc:
        conn.rollback()
        logger.error("Failed to insert violation %s: %s", detection_id, exc)
        raise
    finally:
        close_connection(conn)

    return detection_id


def get_violations(
    filters: Optional[Dict[str, Any]] = None,
    limit: int = 50,
    offset: int = 0,
) -> List[Dict[str, Any]]:
    """Query violations with optional filters.

    Supported filter keys
    ---------------------
    - ``vehicle_type`` : exact match
    - ``violation_type`` : exact match
    - ``status`` : exact match
    - ``plate_search`` : ``LIKE %%value%%`` on ``license_plate``
    - ``date_from`` / ``date_to`` : date-range on ``timestamp``
      (ISO-8601 strings or ``datetime`` objects)

    Returns
    -------
    list[dict]
    """
    ph = _placeholder()
    clauses: List[str] = []
    params: List[Any] = []
    filters = filters or {}

    if filters.get('vehicle_type'):
        clauses.append(f"vehicle_type = {ph}")
        params.append(filters['vehicle_type'])

    if filters.get('violation_type'):
        clauses.append(f"violation_type = {ph}")
        params.append(filters['violation_type'])

    if filters.get('status'):
        clauses.append(f"status = {ph}")
        params.append(filters['status'])

    if filters.get('plate_search'):
        if is_using_sqlite():
            clauses.append(f"license_plate LIKE {ph}")
        else:
            clauses.append(f"license_plate ILIKE {ph}")
        params.append(f"%{filters['plate_search']}%")

    if filters.get('date_from'):
        clauses.append(f"timestamp >= {ph}")
        params.append(str(filters['date_from']))

    if filters.get('date_to'):
        clauses.append(f"timestamp <= {ph}")
        params.append(str(filters['date_to']))

    where = ''
    if clauses:
        where = 'WHERE ' + ' AND '.join(clauses)

    sql = (
        f"SELECT * FROM violations {where} "
        f"ORDER BY timestamp DESC LIMIT {ph} OFFSET {ph}"
    )
    params.extend([limit, offset])

    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(sql, params)
        rows = cur.fetchall()
        results = [_row_to_dict(r, cur) for r in rows]
        # Deserialise bbox_data JSON
        for r in results:
            if 'bbox_data' in r:
                r['bbox_data'] = _json_loads(r['bbox_data'])
        logger.debug("get_violations returned %d row(s).", len(results))
        return results
    except Exception as exc:
        logger.error("get_violations query failed: %s", exc)
        return []
    finally:
        close_connection(conn)


def get_violation_by_id(detection_id: str) -> Optional[Dict[str, Any]]:
    """Fetch a single violation by its ``detection_id``.

    Returns
    -------
    dict or None
    """
    ph = _placeholder()
    sql = f"SELECT * FROM violations WHERE detection_id = {ph}"

    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(sql, (detection_id,))
        row = cur.fetchone()
        if row is None:
            logger.debug("No violation found for id=%s", detection_id)
            return None
        result = _row_to_dict(row, cur)
        if 'bbox_data' in result:
            result['bbox_data'] = _json_loads(result['bbox_data'])
        return result
    except Exception as exc:
        logger.error("get_violation_by_id failed for %s: %s", detection_id, exc)
        return None
    finally:
        close_connection(conn)


# ---------------------------------------------------------------------------
# Analytics & Aggregations
# ---------------------------------------------------------------------------

def get_daily_counts(days: int = 7) -> List[Dict[str, Any]]:
    """Return violation counts grouped by date for the last *days* days.

    Returns
    -------
    list[dict]
        ``[{'date': '2026-06-20', 'count': 12}, ...]``
    """
    ph = _placeholder()
    conn = get_connection()

    try:
        cur = conn.cursor()

        if is_using_sqlite():
            sql = (
                "SELECT DATE(timestamp) AS date, COUNT(*) AS count "
                "FROM violations "
                f"WHERE timestamp >= DATE('now', '-' || {ph} || ' days') "
                "GROUP BY DATE(timestamp) "
                "ORDER BY date ASC"
            )
        else:
            sql = (
                "SELECT DATE(timestamp) AS date, COUNT(*) AS count "
                "FROM violations "
                f"WHERE timestamp >= CURRENT_DATE - INTERVAL '1 day' * {ph} "
                "GROUP BY DATE(timestamp) "
                "ORDER BY date ASC"
            )

        cur.execute(sql, (days,))
        rows = cur.fetchall()
        results = [_row_to_dict(r, cur) for r in rows]

        # Stringify dates for JSON serialisation
        for r in results:
            if 'date' in r and r['date'] is not None:
                r['date'] = str(r['date'])

        logger.debug("get_daily_counts(%d): %d row(s).", days, len(results))
        return results
    except Exception as exc:
        logger.error("get_daily_counts failed: %s", exc)
        return []
    finally:
        close_connection(conn)


def get_monthly_counts(months: int = 6) -> List[Dict[str, Any]]:
    """Return violation counts grouped by month for the last *months* months.

    Returns
    -------
    list[dict]
        ``[{'month': '2026-06', 'count': 45}, ...]``
    """
    ph = _placeholder()
    conn = get_connection()

    try:
        cur = conn.cursor()

        if is_using_sqlite():
            sql = (
                "SELECT STRFTIME('%Y-%m', timestamp) AS month, "
                "COUNT(*) AS count "
                "FROM violations "
                f"WHERE timestamp >= DATE('now', '-' || {ph} || ' months') "
                "GROUP BY month "
                "ORDER BY month ASC"
            )
        else:
            sql = (
                "SELECT TO_CHAR(timestamp, 'YYYY-MM') AS month, "
                "COUNT(*) AS count "
                "FROM violations "
                f"WHERE timestamp >= CURRENT_DATE - INTERVAL '1 month' * {ph} "
                "GROUP BY month "
                "ORDER BY month ASC"
            )

        cur.execute(sql, (months,))
        rows = cur.fetchall()
        results = [_row_to_dict(r, cur) for r in rows]
        logger.debug("get_monthly_counts(%d): %d row(s).", months, len(results))
        return results
    except Exception as exc:
        logger.error("get_monthly_counts failed: %s", exc)
        return []
    finally:
        close_connection(conn)


def get_total_stats() -> Dict[str, Any]:
    """High-level summary statistics.

    Returns
    -------
    dict
        ``{'total_vehicles': int, 'total_violations': int,
        'avg_confidence': float}``
    """
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT COUNT(*) AS total_violations, "
            "AVG(confidence) AS avg_confidence "
            "FROM violations"
        )
        row = cur.fetchone()
        result = _row_to_dict(row, cur)

        total_violations = result.get('total_violations', 0) or 0
        avg_confidence = result.get('avg_confidence', 0.0) or 0.0

        # Distinct vehicle count (unique plates)
        cur.execute(
            "SELECT COUNT(DISTINCT license_plate) AS total_vehicles "
            "FROM violations "
            "WHERE license_plate IS NOT NULL AND license_plate != ''"
        )
        veh_row = cur.fetchone()
        veh_result = _row_to_dict(veh_row, cur)
        total_vehicles = veh_result.get('total_vehicles', 0) or 0

        stats = {
            'total_vehicles': int(total_vehicles),
            'total_violations': int(total_violations),
            'avg_confidence': round(float(avg_confidence), 4),
        }
        logger.debug("get_total_stats: %s", stats)
        return stats
    except Exception as exc:
        logger.error("get_total_stats failed: %s", exc)
        return {
            'total_vehicles': 0,
            'total_violations': 0,
            'avg_confidence': 0.0,
        }
    finally:
        close_connection(conn)


def get_analytics() -> Dict[str, Any]:
    """Comprehensive analytics bundle for dashboard charts.

    Returns
    -------
    dict
        Keys: ``violation_type_counts``, ``vehicle_type_counts``,
        ``daily_counts``, ``monthly_counts``, ``total_stats``.
    """
    conn = get_connection()
    analytics: Dict[str, Any] = {
        'violation_type_counts': [],
        'vehicle_type_counts': [],
        'daily_counts': [],
        'monthly_counts': [],
        'total_stats': {},
    }

    try:
        cur = conn.cursor()

        # --- Violations by type ---
        cur.execute(
            "SELECT violation_type, COUNT(*) AS count, "
            "AVG(confidence) AS avg_confidence "
            "FROM violations "
            "GROUP BY violation_type "
            "ORDER BY count DESC"
        )
        analytics['violation_type_counts'] = [
            _row_to_dict(r, cur) for r in cur.fetchall()
        ]

        # --- Violations by vehicle type ---
        cur.execute(
            "SELECT vehicle_type, COUNT(*) AS count "
            "FROM violations "
            "GROUP BY vehicle_type "
            "ORDER BY count DESC"
        )
        analytics['vehicle_type_counts'] = [
            _row_to_dict(r, cur) for r in cur.fetchall()
        ]

    except Exception as exc:
        logger.error("get_analytics aggregate queries failed: %s", exc)
    finally:
        close_connection(conn)

    # Reuse standalone helpers for daily / monthly / totals
    analytics['daily_counts'] = get_daily_counts(days=7)
    analytics['monthly_counts'] = get_monthly_counts(months=6)
    analytics['total_stats'] = get_total_stats()

    logger.info("get_analytics: assembled analytics payload.")
    return analytics
