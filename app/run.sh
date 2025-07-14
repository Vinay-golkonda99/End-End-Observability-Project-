export OTEL_EXPORTER_OTLP_ENDPOINT="http://otel-collector.observability:4317"
export OTEL_SERVICE_NAME="your-service-name"
# Any other OTEL env vars you need

gunicorn -w 1 --threads 4 -b unix:/tmp/gunicorn.sock --timeout 120 main:app &
nginx -g 'daemon off;'
