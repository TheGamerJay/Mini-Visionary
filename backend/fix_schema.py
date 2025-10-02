#!/usr/bin/env python3
"""Fix user_style_preferences schema issue"""
import os
import sys
from sqlalchemy import create_engine, text

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    sys.stderr.write("DATABASE_URL not set\n")
    sys.exit(1)

engine = create_engine(DATABASE_URL)

sys.stderr.write("Fixing user_style_preferences table schema...\n")

with engine.begin() as conn:
    # Drop the problematic table - it will be recreated properly if needed
    conn.execute(text("DROP TABLE IF EXISTS user_style_preferences CASCADE"))
    sys.stderr.write("✅ Dropped user_style_preferences table\n")

sys.stderr.write("Schema fix complete!\n")
