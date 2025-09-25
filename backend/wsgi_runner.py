from flask import Flask, send_from_directory
import os

app = Flask(__name__, static_folder="static", static_url_path="/")

@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def spa(path):
    file_path = os.path.join(app.static_folder, path)
    if path and os.path.exists(file_path):
        return send_from_directory(app.static_folder, path)
    return send_from_directory(app.static_folder, "index.html")

if __name__ == "__main__":
    app.run()
@app.get("/healthz")
def healthz():
    return {"ok": True}, 200
