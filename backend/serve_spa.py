import os
from flask import send_from_directory, abort
from app_secure import app as flask_app

app = flask_app
app.static_folder = "static"
app.static_url_path = "/static"

# Auth routes are defined in app.py to avoid duplicates

# SPA catch-all that won't swallow real files
# NOTE: This MUST be registered AFTER all API blueprints to avoid hijacking API routes
@app.route("/", defaults={"path": ""}, endpoint="spa_frontend")
@app.route("/<path:path>", endpoint="spa_frontend_path")
def spa_frontend(path=""):
    # Skip API routes - they're handled by blueprints registered before this catch-all
    # Flask matches routes in order, so blueprint routes will match first

    # serve explicit static files
    if path.startswith("static/"):
        subpath = path[len("static/"):]
        return send_from_directory(app.static_folder, subpath)

    if path in ("favicon.ico", "robots.txt"):
        return send_from_directory(app.static_folder, path)

    # if it looks like a file, try to serve it from /static
    if "." in path:
        candidate = os.path.join(app.static_folder, path)
        if os.path.exists(candidate):
            return send_from_directory(app.static_folder, path)

    # SPA fallback for all other routes
    return send_from_directory(app.static_folder, "index.html")

@app.get("/healthz", endpoint="healthcheck")
def healthcheck():
    return {"ok": True}, 200