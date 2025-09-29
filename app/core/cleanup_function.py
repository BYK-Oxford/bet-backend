# app/core/cleanup.py
import logging
from sqlalchemy import text
from app.core.database import engine

logger = logging.getLogger(__name__)

def cleanup_connections():
    """Terminate idle PostgreSQL connections to avoid pool exhaustion"""
    try:
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT pg_terminate_backend(pid)
                FROM pg_stat_activity
                WHERE usename NOT IN ('supabase_admin', 'authenticator', 'supabase_storage_admin', 'pgbouncer')
                AND state IN ('idle', 'idle in transaction')
                AND pid <> pg_backend_pid();
            """))
            logger.info(f"⚡ Terminated {result.rowcount} idle connections")
    except Exception as e:
        logger.error(f"❌ Error cleaning up idle connections: {e}")
