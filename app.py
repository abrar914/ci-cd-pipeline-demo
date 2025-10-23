import os
from flask import Flask, render_template, request, redirect, url_for
from prometheus_client import Counter, generate_latest, CONTENT_TYPE_LATEST

app = Flask(__name__)

# --- Version / Environment labels (shown in UI) ---
APP_VERSION = os.getenv("APP_VERSION", "v1.0.0")
GIT_SHA = os.getenv("GIT_SHA", "local-dev")
ENV_NAME = os.getenv("ENV_NAME", "dev")

# --- Simple in-memory notes (demo only) ---
NOTES = []

# --- Prometheus metrics ---
REQUESTS = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"]
)

def count_request(endpoint, status="200"):
    REQUESTS.labels(method=request.method, endpoint=endpoint, status=status).inc()

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
    # Example static release notes
    data = [
        {"version": "v1.0.0", "desc": "Initial multi-page app"},
        {"version": "v1.1.0", "desc": "Added Prometheus and notes feature"},
    ]
    return render_template("releases.html", releases=data,
                           version=APP_VERSION, sha=GIT_SHA, env=ENV_NAME)

@app.route("/notes", methods=["GET", "POST"])
def notes():
    if request.method == "POST":
        text = request.form.get("text", "").strip()
        if text:
            NOTES.append(text)
    count_request("/notes")
    return render_template("notes.html", notes=NOTES,
                           version=APP_VERSION, sha=GIT_SHA, env=ENV_NAME)

@app.route("/health")
def health():
    # ALB health check
    return {"status": "ok"}, 200

@app.route("/metrics")
def metrics():
    # Prometheus scrape endpoint
    return generate_latest(), 200, {"Content-Type": CONTENT_TYPE_LATEST}

if __name__ == "__main__":
    # Local run (CI/CD uses gunicorn)
    app.run(host="0.0.0.0", port=8000)
