#!/bin/bash

# --- OpenTelemetry Environment Variables ---
export OTEL_SERVICE_NAME="flask-ml-app"
export OTEL_EXPORTER_OTLP_ENDPOINT="http://otel-collector:4317"
export OTEL_TRACES_EXPORTER="otlp"
export OTEL_METRICS_EXPORTER="none"  # you can enable this if OTEL metrics needed
export OTEL_LOGS_EXPORTER="none"     # logs go via stdout and Promtail
export OTEL_RESOURCE_ATTRIBUTES="service.namespace=gke,deployment.environment=prod"

# Optional: if you want to preload app into Gunicorn workers
export PYTHONUNBUFFERED=1

# 🔥 Start Gunicorn in background using Unix socket (used in Nginx config)
gunicorn -w 2 --threads 4 -b unix:/tmp/gunicorn.sock main:app &

# 🔥 Start Nginx in foreground
nginx -g 'daemon off;'
