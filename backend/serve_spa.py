import os
from flask import send_from_directory, abort, request
from app import app as flask_app

app = flask_app
app.static_folder = "static"
app.static_url_path = "/static"

@app.route("/", defaults={"path": ""}, endpoint="spa_frontend")
@app.route("/<path:path>", endpoint="spa_frontend")
def spa_frontend(path):
    # 1) Never hijack API routes
    if path.startswith("api/"):
        abort(404)

    # 2) Serve real static files directly
    #    - /static/anything -> serve from static/
    #    - also handle top-level favicon and robots
    if path.startswith("static/"):
        # strip the leading "static/" before sending
        subpath = path[len("static/"):]
        return send_from_directory(app.static_folder, subpath)

    if path in ("favicon.ico", "robots.txt"):
        return send_from_directory(app.static_folder, path)

    # 3) If the request looks like a file (has a dot), try to serve it from /static
    if "." in path:
        candidate = os.path.join(app.static_folder, path)
        if os.path.exists(candidate):
            # e.g., /assets/index-*.js or /assets/*.css placed under /static
            return send_from_directory(app.static_folder, path)
        # Not a known file; let SPA handle below

    # 4) SPA fallback: send index.html for app routes (/, /login, /register, etc.)
    return send_from_directory(app.static_folder, "index.html")

@app.get("/healthz", endpoint="healthcheck")
def healthcheck():
    return {"ok": True}, 200