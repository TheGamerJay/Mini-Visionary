#!/usr/bin/env python3
"""
Database setup script - Run this once to create tables and indexes
Can be run from Railway shell or locally with DATABASE_URL set
"""
import os
import sys

try:
    from sqlalchemy import create_engine, text
except ImportError:
    sys.stderr.write("Installing required package...\n")
    os.system("pip install sqlalchemy psycopg2-binary")
    from sqlalchemy import create_engine, text

# Get DATABASE_URL from environment
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    sys.stderr.write("\n❌ ERROR: DATABASE_URL not set\n")
    sys.stderr.write("\nTo run locally:\n")
    sys.stderr.write("  export DATABASE_URL='postgresql://...'\n")
    sys.stderr.write("  python setup_db.py\n")
    sys.stderr.write("\nOr run in Railway shell:\n")
    sys.stderr.write("  railway shell\n")
    sys.stderr.write("  python setup_db.py\n")
    sys.exit(1)

sys.stderr.write("🔗 Connecting to database...\n")
try:
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
except Exception as e:
    sys.stderr.write(f"❌ Connection failed: {e}\n")
    sys.exit(1)

# Migration SQL (inline for easy deployment)
MIGRATION_SQL = """
-- Create users table
CREATE TABLE IF NOT EXISTS users (
  id SERIAL PRIMARY KEY,
  email VARCHAR(255) UNIQUE NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  credits INT NOT NULL DEFAULT 20,
  created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
);

-- Create image_jobs table
CREATE TABLE IF NOT EXISTS image_jobs (
  id SERIAL PRIMARY KEY,
  user_id INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  kind VARCHAR(32) NOT NULL,
  prompt TEXT NOT NULL,
  size VARCHAR(16) DEFAULT '1024x1024',
  image_png BYTEA NOT NULL,
  credits_used INT NOT NULL DEFAULT 0,
  created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
);

-- Performance indexes
CREATE INDEX IF NOT EXISTS idx_image_jobs_user_created ON image_jobs (user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- Update existing users
UPDATE users SET credits = COALESCE(credits, 0) WHERE credits IS NULL;
"""

sys.stderr.write("📝 Running migration...\n")
try:
    with engine.begin() as conn:
        for stmt in MIGRATION_SQL.split(";"):
            stmt = stmt.strip()
            if stmt and not stmt.startswith("--"):
                conn.execute(text(stmt))
    sys.stderr.write("✅ Migration completed!\n")
except Exception as e:
    sys.stderr.write(f"❌ Migration failed: {e}\n")
    sys.exit(1)

# Verify
sys.stderr.write("\n🔍 Verifying tables...\n")
try:
    with engine.begin() as conn:
        result = conn.execute(text("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name IN ('users', 'image_jobs')
            ORDER BY table_name
        """))
        tables = [row[0] for row in result]

        if len(tables) == 2:
            sys.stderr.write(f"✅ Tables created: {', '.join(tables)}\n")

            # Check user count
            user_count = conn.execute(text("SELECT COUNT(*) FROM users")).scalar()
            job_count = conn.execute(text("SELECT COUNT(*) FROM image_jobs")).scalar()
            sys.stderr.write(f"📊 Database stats:\n")
            sys.stderr.write(f"   - Users: {user_count}\n")
            sys.stderr.write(f"   - Images: {job_count}\n")
        else:
            sys.stderr.write(f"⚠️  Warning: Expected 2 tables, found {len(tables)}: {tables}\n")

except Exception as e:
    sys.stderr.write(f"❌ Verification failed: {e}\n")
    sys.exit(1)

sys.stderr.write("\n✅ Database setup complete!\n")
sys.stderr.write("\n📝 Next steps:\n")
sys.stderr.write("   1. Deploy your Flask app\n")
sys.stderr.write("   2. Test with: curl https://your-api/api/health\n")
sys.stderr.write("   3. Register a user: POST /api/auth/register\n")
