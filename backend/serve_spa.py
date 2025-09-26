import os
from flask import send_from_directory, abort
from app import app as flask_app

app = flask_app
app.static_folder = "static"
app.static_url_path = "/static"

# Friendly direct URL for the standalone auth page
@app.get("/auth.html", endpoint="auth_page")
def auth_page():
    return send_from_directory(app.static_folder, "auth.html")

@app.get("/terms.html", endpoint="terms_page")
def terms_page():
    return send_from_directory(app.static_folder, "terms.html")

@app.get("/privacy.html", endpoint="privacy_page")
def privacy_page():
    return send_from_directory(app.static_folder, "privacy.html")

# SPA catch-all that won't swallow real files
@app.route("/", defaults={"path": ""}, endpoint="spa_frontend")
@app.route("/<path:path>", endpoint="spa_frontend")
def spa_frontend(path):
    # never hijack API
    if path.startswith("api/"):
        abort(404)

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

    # SPA fallback
    return send_from_directory(app.static_folder, "index.html")

@app.get("/healthz", endpoint="healthcheck")
def healthcheck():
    return {"ok": True}, 200