from flask import Flask, send_from_directory
import os

# serve static at /static
app = Flask(__name__, static_folder="static", static_url_path="/static")

# SPA fallback: serve index.html for non-static routes
@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def spa(path):
    # If a real file exists under static, serve it (useful for direct asset hits)
    file_path = os.path.join(app.static_folder, path)
    if path and os.path.exists(file_path):
        return send_from_directory(app.static_folder, path)
    # Otherwise serve the SPA shell
    return send_from_directory(app.static_folder, "index.html")

@app.get("/healthz")
def healthz():
    return {"ok": True}, 200

if __name__ == "__main__":
    app.run()
