"""Performance Monitoring and Metrics Collection

This module provides centralized monitoring configuration with built-in support for:
- Metrics collection
- Performance tracking
- Error monitoring
- Success rate tracking
- Custom dimensions
- AI operation statistics
- Feature tracking
- Multiple logging backends (via ailf.core.logging)

Example Usage:
    ```python
    from ailf.core.monitoring import setup_monitoring

    monitoring = setup_monitoring('my_feature')

    monitoring.increment('api_calls')
    with monitoring.timer('request_duration'):
        result = make_request()
    monitoring.track_success('api_call', {'status': 200})
    ```

For AI-specific monitoring:
    ```python
    from ailf.core.monitoring import AIStats, Feature

    stats = AIStats(feature=Feature.TEXT_GENERATION)
    stats.log_tokens(prompt_tokens=100, completion_tokens=50)
    stats.log_latency(1.25)  # seconds
    ```

For monitoring with a specific backend:
    ```python
    # With JSON logging for Kubernetes
    monitoring = setup_monitoring('my_feature', backend='json')
    
    # With Google Cloud Logging
    monitoring = setup_monitoring('my_service', backend='gcp', project_id='my-gcp-project')
    
    # With AWS CloudWatch
    monitoring = setup_monitoring('my_app', backend='aws', log_group='my-logs')
    
    # With Logfire
    monitoring = setup_monitoring('my_component', backend='logfire')
    ```

Use this module to implement systematic monitoring across your application.
"""
import importlib.util
import os
import time
import enum
from abc import ABC, abstractmethod
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Union, cast, Type, Protocol, Callable
import logfire
import prometheus_client

from .logging import setup_logging, LogBackend

# Check for optional dependencies
LOGFIRE_AVAILABLE = importlib.util.find_spec("logfire") is not None
OPENTELEMETRY_AVAILABLE = importlib.util.find_spec("opentelemetry") is not None
PROMETHEUS_AVAILABLE = importlib.util.find_spec("prometheus_client") is not None
GCP_MONITORING_AVAILABLE = importlib.util.find_spec("google.cloud.monitoring") is not None
AWS_CLOUDWATCH_AVAILABLE = importlib.util.find_spec("boto3") is not None

# Setup logger with auto-detection of environment
backend_name = os.environ.get('LOG_BACKEND', 'console')
logger = setup_logging('monitoring', backend=backend_name)


class MonitoringBackend(str, enum.Enum):
    """Supported monitoring backends for metrics export."""
    NONE = 'none'           # No metrics export
    CONSOLE = 'console'     # Log metrics to console (default)
    LOGFIRE = 'logfire'     # Export to Logfire
    OPENTELEMETRY = 'otel'  # Export to OpenTelemetry
    PROMETHEUS = 'prom'     # Export to Prometheus
    GCP = 'gcp'             # Export to Google Cloud Monitoring
    AWS = 'aws'             # Export to AWS CloudWatch Metrics


@dataclass
class MetricsCollector:
    """Collector for tracking various metrics."""
    name: str
    counters: Dict[str, int] = field(default_factory=dict)
    timers: Dict[str, float] = field(default_factory=dict)
    success_counts: Dict[str, int] = field(default_factory=dict)
    error_counts: Dict[str, Dict[str, int]] = field(default_factory=dict)

    def increment(self, metric: str, value: int = 1) -> None:
        """Increment a counter metric."""
        if metric not in self.counters:
            self.counters[metric] = 0
        self.counters[metric] += value
        logger.debug(f"{self.name} - {metric}: {self.counters[metric]}")

    def increment_success(self, operation: str) -> None:
        """Increment success counter for an operation."""
        if operation not in self.success_counts:
            self.success_counts[operation] = 0
        self.success_counts[operation] += 1
        logger.debug(
            f"{self.name} - Success {operation}: {self.success_counts[operation]}")

    def track_success(self, operation: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Track a successful operation."""
        if operation not in self.success_counts:
            self.success_counts[operation] = 0
        self.success_counts[operation] += 1
        if metadata:
            logger.info(f"{self.name} - Success {operation}: {metadata}")

    def track_error(self, operation: str, error: str) -> None:
        """Track an operation error."""
        if operation not in self.error_counts:
            self.error_counts[operation] = {}
        if error not in self.error_counts[operation]:
            self.error_counts[operation][error] = 0
        self.error_counts[operation][error] += 1
        logger.error(f"{self.name} - Error in {operation}: {error}")

    @contextmanager
    def timer(self, metric: str):
        """Time an operation.

        Example:
            ```python
            with monitoring.timer('request_duration'):
                result = make_request()
            ```
        """
        start_time = time.time()
        try:
            yield
        finally:
            duration = time.time() - start_time
            if metric not in self.timers:
                self.timers[metric] = 0
            self.timers[metric] = duration
            logger.debug(f"{self.name} - {metric} duration: {duration:.2f}s")

    def get_metrics(self) -> Dict[str, Any]:
        """Get all collected metrics."""
        return {
            'counters': self.counters,
            'timers': self.timers,
            'success_counts': self.success_counts,
            'error_counts': self.error_counts
        }


# Alias for backward compatibility with existing code
Metrics = MetricsCollector


def setup_monitoring(
    component_name: str,
    enable_debug: bool = False,
    backend: Optional[Union[str, MonitoringBackend]] = None,
    export_interval: int = 60,
    **backend_kwargs
) -> MetricsCollector:
    """Set up monitoring for a component.

    Args:
        component_name: Name of the component being monitored
        enable_debug: Whether to enable debug logging
        backend: Optional monitoring backend for metrics export
            ('none', 'console', 'logfire', 'otel', 'prom', 'gcp', 'aws')
        export_interval: Interval in seconds to export metrics (default: 60)
        **backend_kwargs: Additional keyword arguments for the backend initialization
            - For 'logfire': api_key (str)
            - For 'prom': port (int), endpoint (str)
            - For 'gcp': project_id (str)
            - For 'aws': region_name (str), namespace (str)

    Returns:
        MetricsCollector instance
    """
    if enable_debug:
        logger.setLevel('DEBUG')
    
    # Create the metrics collector
    collector = MetricsCollector(name=component_name)
    
    # If no backend specified, check environment variable
    if backend is None:
        backend_env = os.environ.get('MONITORING_BACKEND', 'none')
        try:
            backend = MonitoringBackend(backend_env.lower())
        except ValueError:
            logger.warning(f"Unknown monitoring backend: {backend_env}, defaulting to 'none'")
            backend = MonitoringBackend.NONE
    elif isinstance(backend, str):
        try:
            backend = MonitoringBackend(backend.lower())
        except ValueError:
            logger.warning(f"Unknown monitoring backend: {backend}, defaulting to 'none'")
            backend = MonitoringBackend.NONE
    
    # Initialize the appropriate exporter based on the backend
    if backend == MonitoringBackend.CONSOLE:
        logger.info(f"Metrics for {component_name} will be exported to console")
        exporter = ConsoleMetricsExporter()
    
    elif backend == MonitoringBackend.LOGFIRE and LOGFIRE_AVAILABLE:
        try:
            api_key = backend_kwargs.get('api_key') or os.environ.get('LOGFIRE_API_KEY')
            exporter = LogfireMetricsExporter(api_key=api_key)
            logger.info(f"Metrics for {component_name} will be exported to Logfire")
        except ImportError:
            logger.warning("Logfire not available. Defaulting to console exporter.")
            exporter = ConsoleMetricsExporter()
    
    elif backend == MonitoringBackend.PROMETHEUS and PROMETHEUS_AVAILABLE:
        try:
            port = backend_kwargs.get('port', 8000)
            endpoint = backend_kwargs.get('endpoint', '/metrics')
            exporter = PrometheusMetricsExporter(port=port, endpoint=endpoint)
            logger.info(f"Metrics for {component_name} will be exposed for Prometheus on port {port}")
        except ImportError:
            logger.warning("Prometheus client not available. Defaulting to console exporter.")
            exporter = ConsoleMetricsExporter()
    
    elif backend == MonitoringBackend.GCP and GCP_MONITORING_AVAILABLE:
        logger.warning("Google Cloud Monitoring exporter not implemented yet. Defaulting to console.")
        exporter = ConsoleMetricsExporter()
    
    elif backend == MonitoringBackend.AWS and AWS_CLOUDWATCH_AVAILABLE:
        logger.warning("AWS CloudWatch exporter not implemented yet. Defaulting to console.")
        exporter = ConsoleMetricsExporter()
    
    elif backend == MonitoringBackend.OPENTELEMETRY and OPENTELEMETRY_AVAILABLE:
        logger.warning("OpenTelemetry exporter not implemented yet. Defaulting to console.")
        exporter = ConsoleMetricsExporter()
    
    else:
        # Default to no exporter for MonitoringBackend.NONE or unsupported backends
        return collector
    
    # Set up a background thread to periodically export metrics
    # This could be implemented with threading.Timer or a similar mechanism
    # For now, we'll just return the collector
    
    return collector

import enum


class Feature(enum.Enum):
    """Enumeration of AI features for monitoring."""
    TEXT_GENERATION = "text_generation"
    TEXT_EMBEDDING = "text_embedding"
    IMAGE_GENERATION = "image_generation"
    SPEECH_TO_TEXT = "speech_to_text"
    TEXT_TO_SPEECH = "text_to_speech"
    CHAT_COMPLETION = "chat_completion"
    CLASSIFICATION = "classification"
    SUMMARIZATION = "summarization"
    TRANSLATION = "translation"
    QUESTION_ANSWERING = "question_answering"
    AGENT_EXECUTION = "agent_execution"
    FUNCTION_CALLING = "function_calling"
    CUSTOM = "custom"


@dataclass
class AIStats:
    """Collector for AI-specific performance statistics."""
    feature: Feature
    token_counts: Dict[str, int] = field(default_factory=dict)
    latencies: List[float] = field(default_factory=list)
    costs: List[float] = field(default_factory=list)
    error_counts: Dict[str, int] = field(default_factory=dict)
    context_metrics: Dict[str, Any] = field(default_factory=dict)

    def log_tokens(self, prompt_tokens: int = 0, completion_tokens: int = 0) -> None:
        """Log token usage for an AI operation.

        Args:
            prompt_tokens: Number of tokens in the prompt
            completion_tokens: Number of tokens in the completion
        """
        if 'prompt_tokens' not in self.token_counts:
            self.token_counts['prompt_tokens'] = 0
        if 'completion_tokens' not in self.token_counts:
            self.token_counts['completion_tokens'] = 0
        if 'total_tokens' not in self.token_counts:
            self.token_counts['total_tokens'] = 0
            
        self.token_counts['prompt_tokens'] += prompt_tokens
        self.token_counts['completion_tokens'] += completion_tokens
        self.token_counts['total_tokens'] += prompt_tokens + completion_tokens
        
        logger.debug(f"AI {self.feature.value} - Tokens used: {prompt_tokens} prompt, "
                    f"{completion_tokens} completion, "
                    f"{prompt_tokens + completion_tokens} total")

    def log_latency(self, seconds: float) -> None:
        """Log latency for an AI operation.

        Args:
            seconds: Operation duration in seconds
        """
        self.latencies.append(seconds)
        logger.debug(f"AI {self.feature.value} - Latency: {seconds:.2f}s")

    def log_cost(self, amount: float, currency: str = "USD") -> None:
        """Log cost for an AI operation.

        Args:
            amount: Cost amount
            currency: Currency code (default: USD)
        """
        self.costs.append(amount)
        logger.debug(f"AI {self.feature.value} - Cost: {amount:.6f} {currency}")

    def log_error(self, error_type: str) -> None:
        """Log an error encountered during an AI operation.

        Args:
            error_type: Type of error encountered
        """
        if error_type not in self.error_counts:
            self.error_counts[error_type] = 0
        self.error_counts[error_type] += 1
        logger.error(f"AI {self.feature.value} - Error: {error_type}")

    def add_context(self, key: str, value: Any) -> None:
        """Add context information to the metrics.

        Args:
            key: Context key
            value: Context value
        """
        self.context_metrics[key] = value
        
    def get_stats(self) -> Dict[str, Any]:
        """Get all collected statistics.

        Returns:
            Dict containing all AI statistics
        """
        return {
            'feature': self.feature.value,
            'token_counts': self.token_counts,
            'latencies': self.latencies,
            'avg_latency': sum(self.latencies) / len(self.latencies) if self.latencies else 0,
            'costs': self.costs,
            'total_cost': sum(self.costs),
            'error_counts': self.error_counts,
            'context': self.context_metrics
        }


class MetricsExporter(ABC):
    """Base class for exporting metrics to various monitoring systems."""
    
    @abstractmethod
    def export_counters(self, name: str, counters: Dict[str, int]) -> None:
        """Export counter metrics."""
        pass
    
    @abstractmethod
    def export_timers(self, name: str, timers: Dict[str, float]) -> None:
        """Export timer metrics."""
        pass
    
    @abstractmethod
    def export_ai_stats(self, stats: 'AIStats') -> None:
        """Export AI-specific stats."""
        pass


class ConsoleMetricsExporter(MetricsExporter):
    """Simple exporter that logs metrics to the console."""
    
    def export_counters(self, name: str, counters: Dict[str, int]) -> None:
        """Export counter metrics to console."""
        for key, value in counters.items():
            logger.info(f"METRIC - {name} - Counter - {key}: {value}")
    
    def export_timers(self, name: str, timers: Dict[str, float]) -> None:
        """Export timer metrics to console."""
        for key, value in timers.items():
            logger.info(f"METRIC - {name} - Timer - {key}: {value:.2f}s")
    
    def export_ai_stats(self, stats: 'AIStats') -> None:
        """Export AI-specific stats to console."""
        stat_data = stats.get_stats()
        logger.info(f"AI METRICS - {stat_data['feature']} - "
                    f"Tokens: {stat_data['token_counts'].get('total_tokens', 0)}, "
                    f"Avg Latency: {stat_data['avg_latency']:.2f}s, "
                    f"Total Cost: {stat_data['total_cost']}")


class LogfireMetricsExporter(MetricsExporter):
    """Exporter that sends metrics to Logfire."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the Logfire exporter.
        
        Args:
            api_key: Optional Logfire API key. If not provided,
                    will use LOGFIRE_API_KEY environment variable.
        """
        if not LOGFIRE_AVAILABLE:
            raise ImportError("Logfire is not available. Install with 'pip install logfire'")
        
        
        self.api_key = api_key or os.environ.get('LOGFIRE_API_KEY')
        if self.api_key:
            logfire.init(api_key=self.api_key)
        else:
            logfire.init()
    
    def export_counters(self, name: str, counters: Dict[str, int]) -> None:
        """Export counter metrics to Logfire."""
        
        for key, value in counters.items():
            logfire.log(
                "counter_metric: {component} {metric_name} = {value}",
                component=name,
                metric_name=key,
                value=value
            )
    
    def export_timers(self, name: str, timers: Dict[str, float]) -> None:
        """Export timer metrics to Logfire."""
       
        for key, value in timers.items():
            logfire.log(
                "timer_metric: {component} {metric_name} = {duration_seconds:.2f}s",
                component=name,
                metric_name=key,
                duration_seconds=value
            )
    
    def export_ai_stats(self, stats: 'AIStats') -> None:
        """Export AI-specific stats to Logfire."""
       
        stat_data = stats.get_stats()
        logfire.log(
            "ai_metrics: feature={feature} tokens={token_counts} latency={latency:.2f}s cost={total_cost}",
            feature=stat_data['feature'],
            token_counts=stat_data['token_counts'],
            latency=stat_data['avg_latency'],
            total_cost=stat_data['total_cost'],
            error_counts=stat_data['error_counts'],
            **stat_data['context']
        )


class PrometheusMetricsExporter(MetricsExporter):
    """Exporter that exposes metrics for Prometheus scraping."""
    
    def __init__(self, port: int = 8000, endpoint: str = '/metrics'):
        """Initialize the Prometheus exporter.
        
        Args:
            port: Port to expose metrics on
            endpoint: HTTP endpoint for metrics
        """
        if not PROMETHEUS_AVAILABLE:
            raise ImportError("Prometheus client is not available. Install with 'pip install prometheus_client'")
        
        self.port = port
        self.endpoint = endpoint
        self.counters = {}
        self.gauges = {}
        self.histograms = {}
        
        # Start the server
        prometheus_client.start_http_server(port)
        logger.info(f"Prometheus metrics server started on port {port}, endpoint {endpoint}")
    
    def export_counters(self, name: str, counters: Dict[str, int]) -> None:
        """Export counter metrics to Prometheus."""
       
        for key, value in counters.items():
            metric_name = f"{name}_{key}"
            if metric_name not in self.counters:
                self.counters[metric_name] = prometheus_client.Counter(
                    metric_name, f"Counter metric for {key}"
                )
            
            # Calculate the increment from the last value
            current = self.counters[metric_name]._value.get()
            increment = max(0, value - current)  # Ensure we don't decrement counters
            if increment > 0:
                self.counters[metric_name].inc(increment)
    
    def export_timers(self, name: str, timers: Dict[str, float]) -> None:
        """Export timer metrics to Prometheus."""
       
        for key, value in timers.items():
            metric_name = f"{name}_{key}_seconds"
            if metric_name not in self.gauges:
                self.gauges[metric_name] = prometheus_client.Gauge(
                    metric_name, f"Timer metric for {key} in seconds"
                )
            
            self.gauges[metric_name].set(value)
    
    def export_ai_stats(self, stats: 'AIStats') -> None:
        """Export AI-specific stats to Prometheus."""
        
        stat_data = stats.get_stats()
        feature = stat_data['feature']
        
        # Token counts
        for token_type, count in stat_data['token_counts'].items():
            metric_name = f"ai_{feature}_tokens_{token_type}"
            if metric_name not in self.counters:
                self.counters[metric_name] = prometheus_client.Counter(
                    metric_name, f"Token count for {token_type} in {feature}"
                )
            
            current = self.counters[metric_name]._value.get()
            increment = max(0, count - current)
            if increment > 0:
                self.counters[metric_name].inc(increment)
        
        # Latency
        latency_name = f"ai_{feature}_latency_seconds"
        if stat_data['latencies'] and stat_data['latencies'][-1] is not None:
            if latency_name not in self.histograms:
                self.histograms[latency_name] = prometheus_client.Histogram(
                    latency_name, f"Latency for {feature} operations",
                    buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0)
                )
            
            self.histograms[latency_name].observe(stat_data['latencies'][-1])
        
        # Cost
        cost_name = f"ai_{feature}_cost_total"
        if cost_name not in self.counters:
            self.counters[cost_name] = prometheus_client.Counter(
                cost_name, f"Total cost for {feature} operations"
            )
        
        current_cost = self.counters[cost_name]._value.get()
        cost_increment = max(0, stat_data['total_cost'] - current_cost)
        if cost_increment > 0:
            self.counters[cost_name].inc(cost_increment)


__all__ = ['MetricsCollector', 'Metrics', 'setup_monitoring', 'AIStats', 'Feature', 
          'MetricsExporter', 'MonitoringBackend', 'ConsoleMetricsExporter', 
          'LogfireMetricsExporter', 'PrometheusMetricsExporter']
