import time

from opencensus.trace import execution_context
from opencensus.trace.exporters import print_exporter
from opencensus.trace.exporters.jaeger_exporter import JaegerExporter
from opencensus.trace.tracer import Tracer
from opencensus.trace.samplers import always_on


def function_to_trace():
    time.sleep(1)


def main():
    sampler = always_on.AlwaysOnSampler()
    exporter = print_exporter.PrintExporter()
    #tracer = Tracer(sampler=sampler, exporter=exporter)
    je = JaegerExporter(service_name="pitoncito", host_name='jaeger-server', port=9411, endpoint='/api/traces')
    tracer=Tracer(exporter=je,sampler=always_on.AlwaysOnSampler())

    with tracer.span(name='root'):
        tracer.add_attribute_to_current_span(
            attribute_key='miclave', attribute_value='mivalor')
        function_to_trace()
        with tracer.span(name='child'):
            function_to_trace()

    # Get the current tracer
    tracer = execution_context.get_opencensus_tracer()

    # Explicitly create spans
    tracer.start_span()

    # Get current span
    execution_context.get_current_span()

    # Explicitly end span
    tracer.end_span()


if __name__ == '__main__':
  main()