import sys
from app.core.config import settings
from app.db.session import check_db_connection, engine
from sqlalchemy import text

print(f"Connecting to: {settings.DATABASE_URL.split('@')[-1] if '@' in settings.DATABASE_URL else '...'}")

try:
    with engine.connect() as conn:
        res = conn.execute(text("SELECT version();")).scalar()
        print(" Successfully connected to Supabase PostgreSQL!")
        print(f"PostgreSQL Version: {res}")
except Exception as e:
    print(f" Connection failed: {e}")
    sys.exit(1)
