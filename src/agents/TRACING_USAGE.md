# OpenTelemetry Tracing Usage

## Overview

The agent system includes optional OpenTelemetry tracing for observability. Traces are sent to Jaeger for visualization.

## Setup

1. **Start Jaeger** (in a separate terminal):
```bash
docker run -p 6831:6831/udp -p 16686:16686 jaegertracing/all-in-one:latest
```

2. **Enable tracing**:
```bash
export TRACING_ENABLED=true
```

3. **Run the traced agent**:
```bash
python src/agents/graph_traced.py
```

4. **View traces**:
Open http://localhost:16686 in your browser

## Usage Examples

### Basic Usage

```python
from src.agents.graph_traced import run_traced_agent

# Tracing will be enabled if TRACING_ENABLED=true
result = run_traced_agent("What feeds into revenue?")
```

### Programmatic Usage

```python
from src.agents.graph_traced import create_traced_agent_graph
from src.agents.state import create_initial_state

graph = create_traced_agent_graph()
state = create_initial_state("What feeds into revenue?")
result = graph.invoke(state)
```

### Disable Tracing

```bash
unset TRACING_ENABLED
# or
export TRACING_ENABLED=false
```

When tracing is disabled, all tracing functions become no-ops with zero overhead.

## Trace Hierarchy

Traces follow this structure:

```
agent_execution (root span)
├── plan_node
│   └── llm_inference
├── investigate_node  
│   └── llm_inference
├── tool_node
│   └── tool_{tool_name}
└── synthesize_node
    └── llm_inference
```

## Span Attributes

### Agent Execution
- `query`: User query
- `status`: started/completed/failed
- `confidence`: Final confidence score
- `tools_used`: Number of tools executed
- `final_step`: Final step name
- `total_steps`: Total steps taken

### Node Spans
- `query`: User query
- `step`: Current step count
- `tool_count`: Number of tools used (for investigate/synthesize)
- `plan_length`: Length of plan (for plan_node)
- `tool_choice`: Selected tool (for investigate_node)
- `confidence`: Final confidence (for synthesize_node)

### LLM Spans
- `model`: Model name (e.g., "mistral")
- `prompt_length`: Length of prompt
- `response_length`: Length of response
- `latency_ms`: Execution time in milliseconds
- `max_tokens`: Maximum tokens requested

### Tool Spans
- `tool_name`: Name of the tool
- `tool_input`: JSON string of input parameters
- `success`: Boolean indicating success
- `latency_ms`: Execution time in milliseconds
- `result_count`: Number of results (if applicable)
- `error`: Error message (if failed)

## Performance

- **Tracing disabled**: Zero overhead - all functions are no-ops
- **Tracing enabled**: Minimal overhead (~1-2ms per span)

## Troubleshooting

### No traces appearing in Jaeger

1. Verify Jaeger is running: `docker ps | grep jaeger`
2. Check tracing is enabled: `echo $TRACING_ENABLED`
3. Verify port 6831 is accessible
4. Check Jaeger UI at http://localhost:16686

### Import errors

Ensure all dependencies are installed:
```bash
pip install -r requirements.txt
```

Required packages:
- `opentelemetry-api==1.21.0`
- `opentelemetry-sdk==1.21.0`
- `opentelemetry-exporter-jaeger==1.21.0`

