import os
import sqlite3
from typing import TYPE_CHECKING, Any

from fastapi import APIRouter, Depends

try:
    from sqlalchemy import text as sql_text
    from sqlalchemy.orm import Session
except Exception:  # pragma: no cover
    if TYPE_CHECKING:
        from sqlalchemy.orm import Session  # type: ignore
    else:
        Session = Any  # type: ignore

    def text(sql: str) -> str:  # type: ignore
        return sql


# Try to import get_db, mock if missing
try:
    from src.grid.persistence.database import get_db  # type: ignore[import-not-found]
except ImportError:

    def get_db() -> Any:
        return None


router = APIRouter(prefix="/performance", tags=["performance"])


def get_db_connection():
    # Helper to get raw sqlite connection for fallback
    db_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), "grid.db"
    )
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def execute_fallback(query_str: str):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(query_str)
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    except Exception as e:
        print(f"Fallback query failed: {e}")
        return []


@router.get("/sales")
async def get_sales_data(db: Any = Depends(get_db)):
    sql = """
        SELECT
            strftime('%Y', sale_date) AS year,
            strftime('%m', sale_date) AS month,
            product_id,
            product_name,
            COUNT(*) AS units_sold,
            SUM(revenue) AS total_revenue,
            AVG(revenue) AS avg_revenue_per_unit
        FROM
            sales
        WHERE
            sale_date >= date('now', '-3 years')
        GROUP BY
            year, month, product_id, product_name
        ORDER BY
            year DESC, month DESC, total_revenue DESC;
    """
    try:
        # Try SQLAlchemy first
        if callable(sql_text):
            result = db.execute(sql_text(sql)).fetchall()
            return [dict(row._mapping) for row in result]
        else:
            return execute_fallback(sql)
    except Exception as e:
        print(f"Primary DB Method failed: {e}. Using fallback.")
        return execute_fallback(sql)


@router.get("/user-behavior")
async def get_user_behavior(db: Any = Depends(get_db)):
    sql = """
        SELECT
            u.user_id,
            u.username,
            COUNT(DISTINCT s.session_id) AS total_sessions,
            AVG(s.duration_seconds) AS avg_session_duration,
            COUNT(DISTINCT f.feature_id) AS features_used,
            MAX(s.session_end) AS last_active
        FROM
            users u
        LEFT JOIN
            sessions s ON u.user_id = s.user_id
        LEFT JOIN
            feature_usage f ON u.user_id = f.user_id
        WHERE
            s.session_end >= date('now', '-1 year') OR s.session_end IS NULL
        GROUP BY
            u.user_id, u.username
        ORDER BY
            total_sessions DESC;
    """
    try:
        if callable(sql_text):
            result = db.execute(sql_text(sql)).fetchall()
            return [dict(row._mapping) for row in result]
        else:
            return execute_fallback(sql)
    except Exception:
        return execute_fallback(sql)


@router.get("/product-data")
async def get_product_data(db: Any = Depends(get_db)):
    sql = """
        SELECT
            f.feature_id,
            f.feature_name,
            COUNT(DISTINCT fu.user_id) AS unique_users,
            COUNT(fu.usage_id) AS total_usage,
            COUNT(b.bug_id) AS total_bugs,
            COUNT(CASE WHEN b.severity = 'high' THEN 1 END) AS high_severity_bugs,
            COUNT(CASE WHEN b.status = 'open' THEN 1 END) AS open_bugs
        FROM
            features f
        LEFT JOIN
            feature_usage fu ON f.feature_id = fu.feature_id
        LEFT JOIN
            bugs b ON f.feature_id = b.feature_id
        GROUP BY
            f.feature_id, f.feature_name
        ORDER BY
            total_usage DESC;
    """
    try:
        if callable(sql_text):
            result = db.execute(sql_text(sql)).fetchall()
            return [dict(row._mapping) for row in result]
        else:
            return execute_fallback(sql)
    except Exception:
        return execute_fallback(sql)


@router.get("/development-data")
async def get_development_data(db: Any = Depends(get_db)):
    sql = """
        SELECT
            p.project_id,
            p.project_name,
            COUNT(t.task_id) AS total_tasks,
            COUNT(CASE WHEN t.status = 'completed' THEN 1 END) AS completed_tasks,
            COUNT(CASE WHEN t.status = 'in_progress' THEN 1 END) AS in_progress_tasks,
            COUNT(CASE WHEN t.status = 'open' THEN 1 END) AS open_tasks,
            MIN(t.start_date) AS project_start,
            MAX(t.end_date) AS project_end
        FROM
            projects p
        LEFT JOIN
            tasks t ON p.project_id = t.project_id
        GROUP BY
            p.project_id, p.project_name
        ORDER BY
            project_start DESC;
    """
    try:
        if callable(sql_text):
            result = db.execute(sql_text(sql)).fetchall()
            return [dict(row._mapping) for row in result]
        else:
            return execute_fallback(sql)
    except Exception:
        return execute_fallback(sql)
