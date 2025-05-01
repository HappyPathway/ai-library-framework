"""Integration tests for monitoring utilities."""
import time
import pytest
from utils.monitoring import setup_monitoring

@pytest.fixture
def monitoring():
    """Create test monitoring instance."""
    return setup_monitoring('test_component', enable_debug=True)

def test_counter_metrics(monitoring):
    """Test counter metric tracking."""
    monitoring.increment('test_counter')
    monitoring.increment('test_counter', 2)
    
    metrics = monitoring.get_metrics()
    assert metrics['counters']['test_counter'] == 3

def test_success_tracking(monitoring):
    """Test success metric tracking."""
    metadata = {'status': 200, 'duration': 0.5}
    monitoring.track_success('test_operation', metadata)
    
    metrics = monitoring.get_metrics()
    assert metrics['success_counts']['test_operation'] == 1

def test_error_tracking(monitoring):
    """Test error metric tracking."""
    monitoring.track_error('test_operation', 'Test error')
    monitoring.track_error('test_operation', 'Test error')  # Duplicate error
    monitoring.track_error('test_operation', 'Different error')
    
    metrics = monitoring.get_metrics()
    error_counts = metrics['error_counts']['test_operation']
    assert error_counts['Test error'] == 2
    assert error_counts['Different error'] == 1

def test_timer_metrics(monitoring):
    """Test operation timing."""
    with monitoring.timer('test_timer'):
        time.sleep(0.1)  # Simulate work
    
    metrics = monitoring.get_metrics()
    assert 'test_timer' in metrics['timers']
    assert metrics['timers']['test_timer'] >= 0.1
