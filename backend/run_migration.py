"""Run database migration for secure auth system"""
import os
import sys
from sqlalchemy import create_engine, text

# Get DATABASE_URL from environment
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    sys.stderr.write("ERROR: DATABASE_URL not set in environment\n")
    exit(1)

sys.stderr.write("Connecting to database...\n")
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

# Read migration SQL
with open("migrations/001_secure_auth.sql", "r") as f:
    migration_sql = f.read()

# Split into individual statements (simple split by semicolon)
statements = [s.strip() for s in migration_sql.split(";") if s.strip() and not s.strip().startswith("--")]

sys.stderr.write(f"Running {len(statements)} migration statements...\n")

try:
    with engine.begin() as conn:
        for i, stmt in enumerate(statements, 1):
            if stmt.strip():
                sys.stderr.write(f"  [{i}/{len(statements)}] Executing: {stmt[:60]}...\n")
                conn.execute(text(stmt))

    sys.stderr.write("✅ Migration completed successfully!\n")

    # Verify tables exist
    with engine.begin() as conn:
        result = conn.execute(text("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name IN ('users', 'image_jobs')
        """))
        tables = [row[0] for row in result]
        sys.stderr.write(f"\n✅ Verified tables created: {', '.join(tables)}\n")

except Exception as e:
    sys.stderr.write(f"❌ Migration failed: {e}\n")
    exit(1)
