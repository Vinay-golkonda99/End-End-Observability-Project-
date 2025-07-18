import time
from flask import Flask, request, jsonify
from transformers import pipeline
from opentelemetry import trace, metrics
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from prometheus_client import make_wsgi_app

# Setup
OTLP_ENDPOINT = "http://otel-collector.observability:4318"

# Resource info
resource = Resource(attributes={
    SERVICE_NAME: "llm-app"
})

# --- TRACES ---
trace_provider = TracerProvider(resource=resource)
trace.set_tracer_provider(trace_provider)

span_exporter = OTLPSpanExporter(endpoint=OTLP_ENDPOINT, insecure=True)
trace_provider.add_span_processor(BatchSpanProcessor(span_exporter))

tracer = trace.get_tracer(__name__)

# --- METRICS ---
otlp_metric_exporter = OTLPMetricExporter(endpoint=OTLP_ENDPOINT, insecure=True)
reader = PeriodicExportingMetricReader(otlp_metric_exporter)

meter_provider = MeterProvider(resource=resource, metric_readers=[reader])
metrics.set_meter_provider(meter_provider)

meter = metrics.get_meter(__name__)
REQUESTS_TOTAL = meter.create_counter(
    name="llm_requests_total",
    unit="1",
    description="Total number of requests"
)

REQUEST_LATENCY_MS = meter.create_histogram(
    name="llm_request_latency_ms",
    unit="ms",
    description="Request latency in milliseconds"
)

# --- APP + PROMETHEUS ---
app = Flask(__name__)
FlaskInstrumentor().instrument_app(app)
LoggingInstrumentor().instrument(set_logging_format=True)
app.wsgi_app = DispatcherMiddleware(app.wsgi_app, {
    '/metrics': make_wsgi_app()
})

classifier = pipeline("text-classification", model="distilbert-base-uncased-finetuned-sst-2-english")

@app.route('/ask', methods=['POST'])
def ask_bot():
    start_time = time.time()
    REQUESTS_TOTAL.add(1)

    with tracer.start_as_current_span("ask_bot_request"):
        data = request.get_json()
        question = data.get("question", "")

        with tracer.start_as_current_span("inference"):
            answer = classifier(question)[0]['label']

        latency = (time.time() - start_time) * 1000  # in ms
        REQUEST_LATENCY_MS.record(latency)

        return jsonify({"answer": answer})

@app.route('/')
def index():
    return "LLM Bot is running"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
