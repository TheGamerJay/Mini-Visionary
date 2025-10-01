#!/usr/bin/env python3
"""
Audit Mini-Visionary: find unused assets, scripts, styles; spot orphaned HTML/JS; list Flask routes.

- Scans references in .html/.js/.css/.py
- Compares against files under backend/static and templates
- Emits JSON + markdown reports in tools/_reports/
"""
from __future__ import annotations
import os, re, json, hashlib, pathlib
from collections import defaultdict

ROOT = pathlib.Path(__file__).resolve().parents[1]
STATIC_DIR = ROOT / "backend" / "static"
TEMPLATES_DIR = ROOT / "backend" / "templates" if (ROOT / "backend" / "templates").exists() else ROOT / "backend" / "static"
BACKEND_DIR = ROOT / "backend"
REPORT_DIR = ROOT / "tools" / "_reports"
REPORT_DIR.mkdir(parents=True, exist_ok=True)

CODE_EXTS = (".py", ".js", ".ts", ".css", ".html")
ASSET_EXTS = (".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".ico", ".ttf", ".woff", ".woff2", ".mp3", ".wav", ".mp4")

def iter_files(base: pathlib.Path, exts: tuple[str,...]):
    for p in base.rglob("*"):
        if p.is_file() and p.suffix.lower() in exts:
            yield p

def sha1(path: pathlib.Path) -> str:
    h = hashlib.sha1()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()[:12]

def gather_all_assets():
    assets = []
    for p in iter_files(STATIC_DIR, ASSET_EXTS):
        rel = p.relative_to(ROOT).as_posix()
        assets.append({"path": rel, "size": p.stat().st_size, "hash": sha1(p)})
    return assets

# Very simple reference patterns (cover most cases)
ASSET_PAT = re.compile(r"""(?:src|href)\s*=\s*["']([^"']+)["']""")
CSS_URL_PAT = re.compile(r"""url\(\s*['"]?([^'")]+)['"]?\s*\)""")
IMPORT_PAT = re.compile(r"""import\s+.+?from\s+['"]([^'"]+)['"]|<script\s+.*?src=['"]([^'"]+)['"]""", re.I)
LINK_CSS_PAT = re.compile(r"""<link\s+[^>]*?href=['"]([^'"]+)['"]""", re.I)
ONCALL_PAT = re.compile(r"""on[a-z]+\s*=\s*["']\s*([a-zA-Z_]\w*)\(""")  # e.g., onclick="saveImage()"
FUNC_DEF_JS = re.compile(r"""function\s+([a-zA-Z_]\w*)\s*\(|const\s+([a-zA-Z_]\w*)\s*=\s*\(|let\s+([a-zA-Z_]\w*)\s*=\s*\(|var\s+([a-zA-Z_]\w*)\s*=\s*\(""")
FLASK_ROUTE_PAT = re.compile(r"""@app\.route\(\s*['"]([^'"]+)['"]\s*(?:,|\))|@\w+\.route\(\s*['"]([^'"]+)['"]\s*(?:,|\))""")

def normalize_ref(ref: str) -> str:
    ref = ref.split("?")[0].split("#")[0]
    if ref.startswith("/"):
        ref = ref.lstrip("/")
    return ref

def scan_code_refs():
    refs = set()
    js_funcs_called = set()
    for base in (BACKEND_DIR, STATIC_DIR, TEMPLATES_DIR):
        for p in iter_files(base, CODE_EXTS):
            try:
                txt = p.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            for m in ASSET_PAT.finditer(txt):
                refs.add(normalize_ref(m.group(1)))
            for m in CSS_URL_PAT.finditer(txt):
                refs.add(normalize_ref(m.group(1)))
            for m in IMPORT_PAT.finditer(txt):
                g = m.group(1) or m.group(2)
                if g: refs.add(normalize_ref(g))
            for m in LINK_CSS_PAT.finditer(txt):
                refs.add(normalize_ref(m.group(1)))
            for m in ONCALL_PAT.finditer(txt):
                js_funcs_called.add(m.group(1))
    return refs, js_funcs_called

def scan_js_defined_funcs():
    funcs = set()
    for p in iter_files(STATIC_DIR, (".js", ".ts", ".html")):
        try:
            txt = p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        for m in FUNC_DEF_JS.finditer(txt):
            for g in m.groups():
                if g:
                    funcs.add(g)
    return funcs

def list_flask_routes():
    routes = set()
    for p in iter_files(BACKEND_DIR, (".py",)):
        try:
            txt = p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        for m in FLASK_ROUTE_PAT.finditer(txt):
            route = m.group(1) or m.group(2)
            if route:
                routes.add(route)
    return sorted(routes)

def main():
    assets = gather_all_assets()
    asset_paths = {a["path"] for a in assets}

    refs, js_calls = scan_code_refs()
    js_defs = scan_js_defined_funcs()
    routes = list_flask_routes()

    # Map referenced paths to on-disk existence
    missing_refs = []
    referenced_assets = set()
    for r in refs:
        # Normalize relative static refs to backend/static
        absolute = (ROOT / r)
        if not absolute.exists():
            # Try common prefixes
            candidates = [
                ROOT / r,
                STATIC_DIR / r,
                STATIC_DIR / r.lstrip("backend/static/").lstrip("static/").lstrip("/"),
            ]
            if not any(c.exists() for c in candidates):
                missing_refs.append(r)
        else:
            try:
                referenced_assets.add(os.path.relpath(absolute, ROOT).replace("\\","/"))
            except:
                pass

    # Anything under static not referenced anywhere is "orphan"
    orphan_assets = sorted(asset_paths - referenced_assets)

    # JS usage gaps
    js_missing_impl = sorted(js_calls - js_defs)

    report = {
        "summary": {
            "asset_count": len(assets),
            "referenced_asset_count": len(referenced_assets),
            "orphan_asset_count": len(orphan_assets),
            "missing_reference_count": len(missing_refs),
            "js_called_functions_count": len(js_calls),
            "js_defined_functions_count": len(js_defs),
            "js_missing_implementations": len(js_missing_impl),
            "flask_routes_count": len(routes),
        },
        "orphans": orphan_assets,
        "missing_refs": sorted(set(missing_refs)),
        "js": {
            "called": sorted(js_calls),
            "defined": sorted(js_defs),
            "missing_implementations": js_missing_impl,
        },
        "assets": assets,
        "routes": routes,
    }

    (REPORT_DIR / "audit.json").write_text(json.dumps(report, indent=2), encoding="utf-8")

    # Also emit a human-readable checklist
    lines = []
    s = report["summary"]
    lines.append("# Mini-Visionary Audit Report\n")
    lines.append(f"- Assets: {s['asset_count']}")
    lines.append(f"- Referenced assets: {s['referenced_asset_count']}")
    lines.append(f"- Orphan assets: {s['orphan_asset_count']}")
    lines.append(f"- Missing references in code: {s['missing_reference_count']}")
    lines.append(f"- JS functions called (HTML on*): {s['js_called_functions_count']}")
    lines.append(f"- JS functions defined: {s['js_defined_functions_count']}")
    lines.append(f"- JS missing implementations: {s['js_missing_implementations']}")
    lines.append(f"- Flask routes discovered: {s['flask_routes_count']}\n")
    lines.append("## Flask routes discovered:")
    for r in report["routes"]:
        lines.append(f"- `{r}`")
    lines.append("\n## Orphan assets (safe to archive if truly unused):")
    for p in report["orphans"][:50]:  # Limit to first 50
        lines.append(f"- {p}")
    if len(report["orphans"]) > 50:
        lines.append(f"... and {len(report['orphans']) - 50} more (see audit.json)")
    lines.append("\n## Missing references (likely broken links/paths):")
    for r in report["missing_refs"][:50]:
        lines.append(f"- {r}")
    if len(report["missing_refs"]) > 50:
        lines.append(f"... and {len(report['missing_refs']) - 50} more (see audit.json)")
    lines.append("\n## JS functions used in HTML but not defined (wire up or remove):")
    for f in report["js"]["missing_implementations"]:
        lines.append(f"- {f}()")

    (REPORT_DIR / "audit.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"[OK] Wrote {REPORT_DIR/'audit.json'} and {REPORT_DIR/'audit.md'}")
    print(f"\n[SUMMARY]")
    print(f"   - Orphan assets: {s['orphan_asset_count']}")
    print(f"   - Missing references: {s['missing_reference_count']}")
    print(f"   - JS missing implementations: {s['js_missing_implementations']}")
    print(f"   - Flask routes: {s['flask_routes_count']}")

if __name__ == "__main__":
    main()
