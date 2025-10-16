from flask import Flask, Response
from prometheus_client import generate_latest, Counter, Histogram
import time

app = Flask(__name__)

# --- Prometheus Metrics Setup ---
# A Counter to count the total number of requests
REQUEST_COUNT = Counter(
    'http_requests_total', 'Total HTTP Requests',
    ['method', 'endpoint', 'http_status']
)

# A Histogram to measure request latency
REQUEST_LATENCY = Histogram(
    'http_request_duration_seconds', 'HTTP Request Latency',
    ['method', 'endpoint']
)
# --------------------------------

@app.route('/')
def hello_world():
    # Simulate some work time for latency measurement
    start_time = time.time()
    
    # Core app logic
    response_text = "Hello, CI/CD Pipeline! Your app is auto-deployed from GitHub Actions"
    
    # --- Metrics Collection ---
    REQUEST_COUNT.labels('GET', '/', 200).inc()
    REQUEST_LATENCY.labels('GET', '/').observe(time.time() - start_time)
    # --------------------------
    
    return response_text

# New route for Prometheus to scrape
@app.route('/metrics')
def metrics():
    # Return the metrics data
    return Response(generate_latest(), mimetype='text/plain')

if __name__ == '__main__':
    # Running on port 8000 as per Level 1 setup
    app.run(host='0.0.0.0', port=8000)