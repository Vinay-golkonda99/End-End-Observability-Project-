# main.py (instrumented)

import os
from flask import request, jsonify, Flask
from config import setup_logging, get_model

# OpenTelemetry tracing and logging
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor

# Prometheus metrics
from prometheus_flask_exporter import PrometheusMetrics

# Set up OTEL trace provider
resource = Resource(attributes={"service.name": "flask-ml-app"})
trace.set_tracer_provider(TracerProvider(resource=resource))
otlp_exporter = OTLPSpanExporter(endpoint="http://otel-collector:4317", insecure=True)
span_processor = BatchSpanProcessor(otlp_exporter)
trace.get_tracer_provider().add_span_processor(span_processor)

# Flask app setup
app = Flask(__name__)
FlaskInstrumentor().instrument_app(app)
LoggingInstrumentor().instrument(set_logging_format=True)

# Prometheus metrics setup
metrics = PrometheusMetrics(app)

@app.route('/ask_bot', methods=['GET'])
def generate_sql():
    logger1, logger2 = setup_logging()
    logger1.info("Inside /ask_bot endpoint")

    try:
        tokenizer, model, generator = get_model(logger1, logger2)
        logger1.info("Model and tokenizer loaded successfully")

        model_size = sum(p.numel() for p in model.parameters()) / 1e6
        logger1.info(f"Model size: {model_size:.2f} million parameters")

        prompt = request.args.get("prompt", "Write an SQL query to list all employees in the HR department.")

        logger1.info(f"Generating text for prompt: {prompt}")
        output = generator(prompt, max_length=100, num_return_sequences=1)[0]['generated_text']

        return jsonify({
            "prompt": prompt,
            "output": output,
            "model_size_million_params": model_size
        })

    except Exception as e:
        logger2.error(f"Exception occurred: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=9091)