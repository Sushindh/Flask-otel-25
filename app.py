from flask import Flask, request  # <-- add 'request' here
import time
time.sleep(5)
from opentelemetry import trace, metrics
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
from opentelemetry.instrumentation.flask import FlaskInstrumentor

app = Flask(__name__)
FlaskInstrumentor().instrument_app(app)

# Resources
resource = Resource(attributes={
    SERVICE_NAME: "flask-otel-app"
})

# Tracer
trace.set_tracer_provider(TracerProvider(resource=resource))
tracer = trace.get_tracer(__name__)
span_processor = BatchSpanProcessor(
    OTLPSpanExporter(endpoint="http://otel-collector:4318/v1/traces")
)
trace.get_tracer_provider().add_span_processor(span_processor)



reader = PeriodicExportingMetricReader(
    OTLPMetricExporter(endpoint="http://otel-collector:4318/v1/metrics")  
)
metrics.set_meter_provider(MeterProvider(resource=resource, metric_readers=[reader]))
meter = metrics.get_meter(__name__)
counter = meter.create_counter("app_requests", unit="1", description="Count all incoming requests")

@app.route("/health")
def health():
    return "OK", 200

@app.route("/")
def hello():
    counter.add(1, {"endpoint": request.path})  # use request.path here safely
    print("Incremented counter for /")
    return "Hello, OpenTelemetry!"


@app.route("/create")
def create():
    counter.add(1, {"endpoint": request.path})  # use request.path here too
    with tracer.start_as_current_span("create-work"):
        time.sleep(1)
    return "Created something!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)


