import os
import time
from flask import request, jsonify, Flask
from config import setup_logging, get_model

# OpenTelemetry imports
from opentelemetry import trace
from opentelemetry.sdk.resources import Resource, SERVICE_NAME
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.trace import get_tracer_provider
from opentelemetry.sdk.trace import TracerProvider as SDKTracerProvider

import logging
from prometheus_client import start_http_server, Counter, Histogram

# === Flask App ===
app = Flask(__name__)

# === OpenTelemetry Setup ===

OTLP_ENDPOINT = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://otel-collector.otel-demo:4317")
resource = Resource.create({SERVICE_NAME: "my-llm-app"})

trace_provider = TracerProvider(resource=resource)

# ✅ Prevent TracerProvider override in child processes
if not isinstance(get_tracer_provider(), SDKTracerProvider):
    trace.set_tracer_provider(trace_provider)

span_exporter = OTLPSpanExporter(endpoint=OTLP_ENDPOINT, insecure=True)
trace_provider.add_span_processor(BatchSpanProcessor(span_exporter))
tracer = trace.get_tracer(__name__)

# Instrument Flask and Logging
FlaskInstrumentor().instrument_app(app)
LoggingInstrumentor().instrument(set_logging_format=True)

# Setup loggers
logger1, logger2 = setup_logging()

# === Load Model Once at Startup ===

logger1.info("Loading model and tokenizer at startup...")
tokenizer, model, generator = get_model(logger1, logger2)
logger1.info("Model and tokenizer loaded at startup.")

# === Prometheus Metrics Setup ===

REQUESTS_TOTAL = Counter('requests_total', 'Total HTTP requests to /ask_bot')
REQUEST_LATENCY_MS = Histogram('request_latency_ms', 'Latency of /ask_bot requests in ms')

# ✅ Guard against "port already in use" crash
try:
    start_http_server(8000)
    logger1.info("Prometheus metrics server started on port 8000.")
except OSError as e:
    logger2.warning(f"Could not start Prometheus metrics server: {e}")

# === Flask Routes ===

@app.route('/ask_bot', methods=['GET'])
def generate_sql():
    start_time = time.time()
    with tracer.start_as_current_span("ask_bot_request"):
        REQUESTS_TOTAL.inc()
        logger1.info("Inside /ask_bot endpoint")

        try:
            with tracer.start_as_current_span("get_model"):
                logger1.info("Model already preloaded, skipping reinitialization.")

            model_size = sum(p.numel() for p in model.parameters()) / 1e6
            logger1.info(f"Model size: {model_size:.2f} million parameters")

            prompt = request.args.get("prompt", "Write an SQL query to list all employees in the HR department.")
            logger1.info(f"Generating text for prompt: {prompt}")

            with tracer.start_as_current_span("inference"):
                output = generator(prompt, max_length=100, num_return_sequences=1)[0]['generated_text']

            duration_ms = (time.time() - start_time) * 1000
            REQUEST_LATENCY_MS.observe(duration_ms)
            logger1.info(f"Request processed in {duration_ms:.2f} ms")

            return jsonify({
                "prompt": prompt,
                "output": output,
                "model_size_million_params": model_size
            })

        except Exception as e:
            logger2.error(f"Exception occurred: {e}", exc_info=True)
            return jsonify({"error": str(e)}), 500

# === Main Entry Point ===

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=1999)
