#!/usr/bin/env python3
"""
PRODUCTION DATABASE CONFIGURATION
=================================

This file contains the correct production database connection details
for minivisionary.soulbridgeai.com

IMPORTANT: This is the REAL production database where:
- User aceelnene@gmail.com is ID 6
- Contains tables: users, wallet_transactions, posters
- Live website data is stored here

Connection Details:
- Host: maglev.proxy.rlwy.net
- Port: 22676
- Database: railway
- User: postgres
- Password: PtznVvouCSknyrDHjGYqRYwHjDteLqRZ

Full URL: postgresql://postgres:PtznVvouCSknyrDHjGYqRYwHjDteLqRZ@maglev.proxy.rlwy.net:22676/railway

Usage:
    export DATABASE_URL="postgresql://postgres:PtznVvouCSknyrDHjGYqRYwHjDteLqRZ@maglev.proxy.rlwy.net:22676/railway"
    python your_script.py

Or in Windows:
    set DATABASE_URL=postgresql://postgres:PtznVvouCSknyrDHjGYqRYwHjDteLqRZ@maglev.proxy.rlwy.net:22676/railway
    python your_script.py

Note: This is the PUBLIC connection URL that can be accessed externally.
The production Railway app uses the internal URL: postgres.railway.internal:5432
"""

PRODUCTION_DATABASE_URL = "postgresql://postgres:PtznVvouCSknyrDHjGYqRYwHjDteLqRZ@maglev.proxy.rlwy.net:22676/railway"

def get_production_db_url():
    """Returns the production database URL"""
    return PRODUCTION_DATABASE_URL

if __name__ == "__main__":
    print("Production Database URL:")
    print(PRODUCTION_DATABASE_URL)