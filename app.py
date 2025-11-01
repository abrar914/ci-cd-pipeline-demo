import os, time, csv
from io import StringIO
from datetime import datetime, timezone
from flask import (
    Flask, render_template, request, redirect, url_for,
    flash, jsonify, Response
)
from prometheus_client import Counter, generate_latest, CONTENT_TYPE_LATEST

app = Flask(__name__)

# --- Config / Version labels (shown in UI & APIs) ---
APP_VERSION = os.getenv("APP_VERSION", "v1.0.0")
GIT_SHA = os.getenv("GIT_SHA", "local-dev")
ENV_NAME = os.getenv("ENV_NAME", "dev")
BUILD_TIME = os.getenv("BUILD_TIME", str(int(time.time())))
READ_ONLY = os.getenv("READ_ONLY", "false").lower() == "true"

# Flash messages need a secret key; keep dev-safe default for demos
app.secret_key = os.getenv("SECRET_KEY", "dev-key-change-me")

# --- Simple in-memory notes (demo only) ---
# Store dicts so we can keep timestamps (keeps demo stateless across pods)
NOTES = []   # each: {"text": str, "ts": int}

# --- Prometheus metrics ---
REQUESTS = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"]
)

def count_request(endpoint, status="200"):
    REQUESTS.labels(method=request.method, endpoint=endpoint, status=str(status)).inc()

# --- Helpful response headers (security & privacy) ---
@app.after_request
def set_headers(resp):
    resp.headers["X-Frame-Options"] = "SAMEORIGIN"
    resp.headers["X-Content-Type-Options"] = "nosniff"
    resp.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    resp.headers["Permissions-Policy"] = "geolocation=(), camera=()"
    return resp

# --- Jinja filter: format UNIX ts -> UTC string ---
@app.template_filter("datetime")
def fmt_dt(ts):
    return datetime.fromtimestamp(int(ts), tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

# ------------------ Views ------------------

@app.route("/")
def home():
    count_request("/")
    return render_template("home.html",
                           version=APP_VERSION, sha=GIT_SHA, env=ENV_NAME)

@app.route("/about")
def about():
    count_request("/about")
    return render_template("about.html",
                           version=APP_VERSION, sha=GIT_SHA, env=ENV_NAME)

@app.route("/releases")
def releases():
    count_request("/releases")
    data = [
        {"version": "v1.0.0", "desc": "Initial multi-page app"},
        {"version": "v1.1.0", "desc": "Added Prometheus and notes feature"},
    ]
    return render_template("releases.html", releases=data,
                           version=APP_VERSION, sha=GIT_SHA, env=ENV_NAME)

# Notes: add timestamps, search, delete, export, and flash messages
@app.route("/notes", methods=["GET", "POST"])
def notes():
    if request.method == "POST":
        if READ_ONLY:
            flash("Read-only mode: changes are disabled.", "warning")
            count_request("/notes", status=403)
            return redirect(url_for("notes"))
        text = (request.form.get("text") or "").strip()
        if text:
            NOTES.append({"text": text, "ts": int(time.time())})
            flash("Note added.", "success")
        else:
            flash("Please write something before adding.", "error")

    # Optional search (?q=...)
    q = (request.args.get("q") or "").strip().lower()
    results = [n for n in NOTES if q in n["text"].lower()] if q else NOTES

    count_request("/notes")
    return render_template("notes.html", notes=results, q=q, READ_ONLY=READ_ONLY,
                           version=APP_VERSION, sha=GIT_SHA, env=ENV_NAME)

@app.post("/notes/delete/<int:index>")
def delete_note(index):
    if READ_ONLY:
        flash("Read-only mode: changes are disabled.", "warning")
        count_request("/notes/delete", status=403)
        return redirect(url_for("notes"))
    if 0 <= index < len(NOTES):
        NOTES.pop(index)
        flash("Note deleted.", "success")
    else:
        flash("Note not found.", "error")
    count_request("/notes/delete")
    return redirect(url_for("notes"))

@app.get("/notes/export.json")
def export_json():
    count_request("/notes/export.json")
    return jsonify(notes=NOTES)

@app.get("/notes/export.csv")
def export_csv():
    sio = StringIO()
    w = csv.writer(sio)
    w.writerow(["text", "timestamp_iso"])
    for n in NOTES:
        w.writerow([n["text"], datetime.utcfromtimestamp(n["ts"]).isoformat() + "Z"])
    count_request("/notes/export.csv")
    return Response(
        sio.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=notes.csv"}
    )

# --- Health/Readiness/Version for ALB/monitoring ---
@app.route("/health")
def health():
    # ALB health check
    count_request("/health")
    return {"status": "ok"}, 200

@app.route("/ready")
def ready():
    # Cheap checks only; keep fast/always-true unless you add real deps
    count_request("/ready")
    return {"ready": True}, 200

@app.route("/version.json")
def version_json():
    count_request("/version.json")
    return jsonify(env=ENV_NAME, version=APP_VERSION, sha=GIT_SHA, build_time=BUILD_TIME)

# --- Prometheus scrape endpoint ---
@app.route("/metrics")
def metrics():
    count_request("/metrics")
    return generate_latest(), 200, {"Content-Type": CONTENT_TYPE_LATEST}

# --- Friendly 404 that also counts ---
@app.errorhandler(404)
def not_found(e):
    count_request("404", status=404)
    return render_template("404.html",
                           version=APP_VERSION, sha=GIT_SHA, env=ENV_NAME), 404

if __name__ == "__main__":
    # Local run (CI/CD uses gunicorn)
    app.run(host="0.0.0.0", port=8000)
