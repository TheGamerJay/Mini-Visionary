import os
from flask import send_from_directory, abort, redirect
from app import app as flask_app  # this imports your real API app

# Reuse the real app instance, but ensure static paths are correct
app = flask_app
app.static_folder = "static"
app.static_url_path = "/static"

# SPA fallback: only for non-API paths
@app.route("/", defaults={"path": ""}, endpoint="spa_frontend")
@app.route("/<path:path>", endpoint="spa_frontend")
def spa_frontend(path):
    # Normalize /index.html -> /
    if path == "index.html":
        return redirect("/", code=301)

    # Let real API routes handle /api/*
    if path.startswith("api/"):
        abort(404)

    file_path = os.path.join(app.static_folder, path)
    if path and os.path.exists(file_path):
        return send_from_directory(app.static_folder, path)
    return send_from_directory(app.static_folder, "index.html")

@app.get("/healthz", endpoint="healthcheck")
def healthcheck():
    return {"ok": True}, 200
