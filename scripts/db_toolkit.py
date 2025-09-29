#!/usr/bin/env python3
"""
Poster DB Toolkit
-----------------
CLI admin for public.posters

New commands:
  search "<text>" [--limit N]
  export <path> [--format json|ndjson] [--author ID] [--category CAT] [--published true|false]
  import <path> [--on-conflict url|id] [--dry-run]

Existing + extras:
  latest [N]              show latest N
  author <ID> [N]         list by author
  category <CAT> [N]      list by category
  publish <ID> [--by EMAIL]
  unpublish <ID>
  views <ID> [--inc N]
  likes <ID> [--inc N]
  get <ID>
  create --description ... [--tags ... --url ... --author ... --category ... --published]
  update <ID> [--description ... --tags ... --url ... --author ... --category ... --published]
  delete <ID>
  schema

DB connection:
  Uses DATABASE_URL if present (e.g., postgres://user:pass@host:port/db)
  Otherwise PGHOST/PGPORT/PGDATABASE/PGUSER/PGPASSWORD
"""

import argparse
import json
import os
import sys
from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional, Tuple

try:
    import psycopg2
    import psycopg2.extras
except Exception as e:
    print("psycopg2 is required. Install with: pip install psycopg2-binary", file=sys.stderr)
    raise

TABLE = "public.posters"

# ---------- DB UTIL ----------

def get_conn():
    url = os.getenv("DATABASE_URL")
    if url:
        return psycopg2.connect(url, cursor_factory=psycopg2.extras.RealDictCursor)
    # fallback to discrete env vars
    params = dict(
        host=os.getenv("PGHOST", "localhost"),
        port=os.getenv("PGPORT", "5432"),
        dbname=os.getenv("PGDATABASE"),
        user=os.getenv("PGUSER"),
        password=os.getenv("PGPASSWORD"),
    )
    # allow missing dbname -> try DATABASE
    if not params["dbname"]:
        print("Set DATABASE_URL or PGHOST/PGPORT/PGDATABASE/PGUSER/PGPASSWORD", file=sys.stderr)
        sys.exit(2)
    return psycopg2.connect(cursor_factory=psycopg2.extras.RealDictCursor, **params)

def q_select(sql: str, args: Tuple = ()) -> List[Dict[str, Any]]:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, args)
            return cur.fetchall()

def q_exec(sql: str, args: Tuple = ()) -> int:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, args)
            return cur.rowcount

def q_exec_returning(sql: str, args: Tuple = ()) -> Dict[str, Any]:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, args)
            row = cur.fetchone()
            return row

# ---------- PRINT HELPERS ----------

def print_rows(rows: List[Dict[str, Any]]):
    if not rows:
        print("(no rows)")
        return
    # compact table
    cols = list(rows[0].keys())
    # limit column widths for console sanity
    maxw = {c: min(max(len(c), *(len(str(r.get(c, ""))) for r in rows)), 80) for c in cols}
    # header
    line = " | ".join(c.ljust(maxw[c]) for c in cols)
    print(line)
    print("-" * len(line))
    for r in rows:
        print(" | ".join(str(r.get(c, "")).ljust(maxw[c]) for c in cols))

def parse_bool(val: Optional[str]) -> Optional[bool]:
    if val is None:
        return None
    v = str(val).strip().lower()
    if v in ("1","true","t","yes","y","on"):
        return True
    if v in ("0","false","f","no","n","off"):
        return False
    raise ValueError(f"Invalid boolean: {val}")

# ---------- COMMANDS ----------

def cmd_latest(args):
    limit = args.limit or 20
    rows = q_select(f"""
        SELECT * FROM {TABLE}
        ORDER BY created_at DESC
        LIMIT %s
    """, (limit,))
    print_rows(rows)

def cmd_author(args):
    limit = args.limit or 20
    rows = q_select(f"""
        SELECT * FROM {TABLE}
        WHERE author_id = %s
        ORDER BY created_at DESC
        LIMIT %s
    """, (args.author_id, limit))
    print_rows(rows)

def cmd_category(args):
    limit = args.limit or 20
    rows = q_select(f"""
        SELECT * FROM {TABLE}
        WHERE category = %s
        ORDER BY created_at DESC
        LIMIT %s
    """, (args.category, limit))
    print_rows(rows)

def cmd_publish(args):
    row = q_exec_returning(f"""
        UPDATE {TABLE}
        SET is_published = TRUE,
            updated_by = COALESCE(%s, updated_by),
            updated_at = NOW()
        WHERE id = %s
        RETURNING *;
    """, (args.by, args.id))
    if row:
        print_rows([row])
    else:
        print("(no such id)")

def cmd_unpublish(args):
    row = q_exec_returning(f"""
        UPDATE {TABLE}
        SET is_published = FALSE,
            updated_at = NOW()
        WHERE id = %s
        RETURNING *;
    """, (args.id,))
    if row:
        print_rows([row])
    else:
        print("(no such id)")

def cmd_inc(args, col: str):
    inc = args.inc or 1
    row = q_exec_returning(f"""
        UPDATE {TABLE}
        SET {col} = COALESCE({col}, 0) + %s,
            updated_at = NOW()
        WHERE id = %s
        RETURNING id, {col}, updated_at;
    """, (inc, args.id))
    if row:
        print_rows([row])
    else:
        print("(no such id)")

def cmd_views(args):  # views <id> [--inc N]
    cmd_inc(args, "views_count")

def cmd_likes(args):  # likes <id> [--inc N]
    cmd_inc(args, "likes_count")

def cmd_get(args):
    rows = q_select(f"SELECT * FROM {TABLE} WHERE id = %s", (args.id,))
    print_rows(rows)

def cmd_create(args):
    row = q_exec_returning(f"""
        INSERT INTO {TABLE}
        (description, tags, likes_count, views_count, shared_url, created_at, updated_at,
         author_id, category, is_published, updated_by)
        VALUES (%s, %s, 0, 0, %s, NOW(), NOW(), %s, %s, %s, %s)
        RETURNING *;
    """, (
        args.description,
        args.tags,
        args.url,
        args.author,
        args.category,
        parse_bool(args.published) if args.published is not None else False,
        args.updated_by
    ))
    print_rows([row])

def cmd_update(args):
    # Build dynamic SET
    fields = []
    params = []
    if args.description is not None:
        fields.append("description = %s"); params.append(args.description)
    if args.tags is not None:
        fields.append("tags = %s"); params.append(args.tags)
    if args.url is not None:
        fields.append("shared_url = %s"); params.append(args.url)
    if args.author is not None:
        fields.append("author_id = %s"); params.append(args.author)
    if args.category is not None:
        fields.append("category = %s"); params.append(args.category)
    if args.published is not None:
        fields.append("is_published = %s"); params.append(parse_bool(args.published))
    if args.updated_by is not None:
        fields.append("updated_by = %s"); params.append(args.updated_by)

    if not fields:
        print("Nothing to update. Provide at least one field.", file=sys.stderr)
        sys.exit(1)

    fields.append("updated_at = NOW()")
    sql = f"UPDATE {TABLE} SET " + ", ".join(fields) + " WHERE id = %s RETURNING *;"
    params.append(args.id)
    row = q_exec_returning(sql, tuple(params))
    if row:
        print_rows([row])
    else:
        print("(no such id)")

def cmd_delete(args):
    count = q_exec(f"DELETE FROM {TABLE} WHERE id = %s", (args.id,))
    print(f"deleted: {count}")

def cmd_schema(_args):
    rows = q_select("""
        SELECT column_name, data_type, is_nullable, column_default
        FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'posters'
        ORDER BY ordinal_position;
    """)
    print_rows(rows)

def cmd_search(args):
    limit = args.limit or 25
    q = f"%{args.text}%"
    rows = q_select(f"""
        SELECT *
        FROM {TABLE}
        WHERE COALESCE(description,'') ILIKE %s
           OR COALESCE(tags,'')        ILIKE %s
           OR COALESCE(category,'')    ILIKE %s
           OR COALESCE(shared_url,'')  ILIKE %s
        ORDER BY updated_at DESC
        LIMIT %s
    """, (q, q, q, q, limit))
    print_rows(rows)

def build_where(author: Optional[int], category: Optional[str], published: Optional[str]) -> Tuple[str, List[Any]]:
    clauses = []
    params: List[Any] = []
    if author is not None:
        clauses.append("author_id = %s"); params.append(author)
    if category is not None:
        clauses.append("category = %s"); params.append(category)
    if published is not None:
        clauses.append("is_published = %s"); params.append(parse_bool(published))
    where = " WHERE " + " AND ".join(clauses) if clauses else ""
    return where, params

def cmd_export(args):
    fmt = (args.format or "json").lower()
    if fmt not in ("json", "ndjson"):
        print("format must be json or ndjson", file=sys.stderr)
        sys.exit(2)

    where, params = build_where(args.author, args.category, args.published)
    rows = q_select(f"SELECT * FROM {TABLE}{where} ORDER BY id ASC", tuple(params))

    if fmt == "json":
        with open(args.path, "w", encoding="utf-8") as f:
            json.dump(rows, f, ensure_ascii=False, indent=2, default=str)
    else:
        with open(args.path, "w", encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False, default=str) + "\n")

    print(f"exported {len(rows)} rows -> {args.path}")

def iter_import_records(path: str) -> Iterable[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as f:
        first = f.read(1)
        f.seek(0)
        if first == "[":
            data = json.load(f)
            if not isinstance(data, list):
                raise ValueError("JSON array expected for import")
            for item in data:
                if isinstance(item, dict):
                    yield item
        else:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                yield json.loads(line)

def normalize_rec(rec: Dict[str, Any]) -> Dict[str, Any]:
    # ensure compatible keys
    out = {
        "id": rec.get("id"),
        "description": rec.get("description"),
        "tags": rec.get("tags"),
        "likes_count": rec.get("likes_count", 0),
        "views_count": rec.get("views_count", 0),
        "shared_url": rec.get("shared_url"),
        "created_at": rec.get("created_at"),
        "updated_at": rec.get("updated_at"),
        "author_id": rec.get("author_id"),
        "category": rec.get("category"),
        "is_published": rec.get("is_published", False),
        "updated_by": rec.get("updated_by"),
    }
    return out

def cmd_import(args):
    key = (args.on_conflict or "url").lower()
    if key not in ("url", "id"):
        print("on-conflict must be 'url' or 'id'", file=sys.stderr); sys.exit(2)

    dry = bool(args.dry_run)
    total = 0
    upserts = 0
    inserts = 0

    for rec in iter_import_records(args.path):
        total += 1
        r = normalize_rec(rec)

        # Convert timestamps if strings
        for ts_key in ("created_at", "updated_at"):
            v = r.get(ts_key)
            if isinstance(v, str):
                try:
                    # let postgres handle most formats, but keep as string
                    pass
                except Exception:
                    r[ts_key] = None

        if key == "url":
            if not r.get("shared_url"):
                print(f"[skip] row {total}: missing shared_url", file=sys.stderr)
                continue

            sql = f"""
                INSERT INTO {TABLE}
                (description, tags, likes_count, views_count, shared_url,
                 created_at, updated_at, author_id, category, is_published, updated_by)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (shared_url) DO UPDATE
                SET description = EXCLUDED.description,
                    tags = EXCLUDED.tags,
                    likes_count = EXCLUDED.likes_count,
                    views_count = EXCLUDED.views_count,
                    author_id = EXCLUDED.author_id,
                    category = EXCLUDED.category,
                    is_published = EXCLUDED.is_published,
                    updated_by = EXCLUDED.updated_by,
                    updated_at = COALESCE(EXCLUDED.updated_at, NOW())
                RETURNING id;
            """
            params = (
                r["description"], r["tags"], r["likes_count"], r["views_count"], r["shared_url"],
                r["created_at"], r["updated_at"], r["author_id"], r["category"], r["is_published"], r["updated_by"]
            )
        else:
            # conflict on id (requires id present)
            if not r.get("id"):
                print(f"[skip] row {total}: missing id for on-conflict=id", file=sys.stderr)
                continue
            sql = f"""
                INSERT INTO {TABLE}
                (id, description, tags, likes_count, views_count, shared_url,
                 created_at, updated_at, author_id, category, is_published, updated_by)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (id) DO UPDATE
                SET description = EXCLUDED.description,
                    tags = EXCLUDED.tags,
                    likes_count = EXCLUDED.likes_count,
                    views_count = EXCLUDED.views_count,
                    shared_url = EXCLUDED.shared_url,
                    author_id = EXCLUDED.author_id,
                    category = EXCLUDED.category,
                    is_published = EXCLUDED.is_published,
                    updated_by = EXCLUDED.updated_by,
                    updated_at = COALESCE(EXCLUDED.updated_at, NOW())
                RETURNING id;
            """
            params = (
                r["id"], r["description"], r["tags"], r["likes_count"], r["views_count"], r["shared_url"],
                r["created_at"], r["updated_at"], r["author_id"], r["category"], r["is_published"], r["updated_by"]
            )

        if dry:
            upserts += 1
            continue

        row = q_exec_returning(sql, params)
        if row:
            # Can't easily tell insert vs update without additional checks;
            # treat as upsert and count inserts by probing previous existence quickly
            if key == "url":
                existed = q_select(f"SELECT 1 FROM {TABLE} WHERE shared_url = %s", (r["shared_url"],))
            else:
                existed = q_select(f"SELECT 1 FROM {TABLE} WHERE id = %s", (r["id"],))
            if existed:
                upserts += 1
            else:
                inserts += 1

    if dry:
        print(f"(dry-run) would upsert {upserts} of {total} records")
    else:
        print(f"import complete: processed={total}, upserts={upserts}, inserts~={inserts}")

# ---------- ARGPARSE ----------

def build_parser():
    p = argparse.ArgumentParser(description="Poster DB Toolkit")
    sub = p.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("latest"); sp.add_argument("limit", nargs="?", type=int); sp.set_defaults(func=cmd_latest)
    sp = sub.add_parser("author"); sp.add_argument("author_id", type=int); sp.add_argument("limit", nargs="?", type=int); sp.set_defaults(func=cmd_author)
    sp = sub.add_parser("category"); sp.add_argument("category"); sp.add_argument("limit", nargs="?", type=int); sp.set_defaults(func=cmd_category)

    sp = sub.add_parser("publish"); sp.add_argument("id", type=int); sp.add_argument("--by"); sp.set_defaults(func=cmd_publish)
    sp = sub.add_parser("unpublish"); sp.add_argument("id", type=int); sp.set_defaults(func=cmd_unpublish)

    sp = sub.add_parser("views"); sp.add_argument("id", type=int); sp.add_argument("--inc", type=int); sp.set_defaults(func=cmd_views)
    sp = sub.add_parser("likes"); sp.add_argument("id", type=int); sp.add_argument("--inc", type=int); sp.set_defaults(func=cmd_likes)

    sp = sub.add_parser("get"); sp.add_argument("id", type=int); sp.set_defaults(func=cmd_get)

    sp = sub.add_parser("create")
    sp.add_argument("--description", required=True)
    sp.add_argument("--tags")
    sp.add_argument("--url", dest="url")
    sp.add_argument("--author", type=int)
    sp.add_argument("--category")
    sp.add_argument("--published")
    sp.add_argument("--updated-by", dest="updated_by")
    sp.set_defaults(func=cmd_create)

    sp = sub.add_parser("update")
    sp.add_argument("id", type=int)
    sp.add_argument("--description")
    sp.add_argument("--tags")
    sp.add_argument("--url", dest="url")
    sp.add_argument("--author", type=int)
    sp.add_argument("--category")
    sp.add_argument("--published")
    sp.add_argument("--updated-by", dest="updated_by")
    sp.set_defaults(func=cmd_update)

    sp = sub.add_parser("delete"); sp.add_argument("id", type=int); sp.set_defaults(func=cmd_delete)
    sp = sub.add_parser("schema"); sp.set_defaults(func=cmd_schema)

    sp = sub.add_parser("search"); sp.add_argument("text"); sp.add_argument("--limit", type=int); sp.set_defaults(func=cmd_search)

    sp = sub.add_parser("export")
    sp.add_argument("path")
    sp.add_argument("--format", choices=["json", "ndjson"])
    sp.add_argument("--author", type=int)
    sp.add_argument("--category")
    sp.add_argument("--published")
    sp.set_defaults(func=cmd_export)

    sp = sub.add_parser("import")
    sp.add_argument("path")
    sp.add_argument("--on-conflict", choices=["url", "id"], default="url")
    sp.add_argument("--dry-run", action="store_true")
    sp.set_defaults(func=cmd_import)

    return p

def main():
    parser = build_parser()
    args = parser.parse_args()
    try:
        args.func(args)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()