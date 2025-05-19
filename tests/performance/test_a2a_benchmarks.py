"""Benchmark tests for A2A protocol components.

This module contains performance benchmark tests for A2A protocol components
to measure throughput, latency, and resource usage.
"""
import asyncio
import json
import time
from datetime import datetime, UTC
from typing import Dict, List, Optional, Any, AsyncIterator
import statistics

import pytest
import pytest_benchmark

from ailf.communication.a2a_client import A2AClient
from ailf.communication.a2a_orchestration import (
    A2AOrchestrator,
    AgentRoute,
    OrchestrationConfig,
    RouteType,
)
from ailf.communication.a2a_registry import A2ARegistryManager
from ailf.communication.a2a_server import AILFASA2AServer, A2AAgentExecutor, A2ARequestContext
from ailf.schemas.a2a import (
    Message,
    MessagePart,
    Task,
    TaskState,
)


class BenchmarkAgentExecutor(A2AAgentExecutor):
    """Simple agent executor for benchmarking."""
    
    def __init__(self, latency_ms=0):
        """Initialize with optional artificial latency."""
        self.latency_ms = latency_ms
    
    async def execute(self, context: A2ARequestContext) -> Task:
        """Execute the agent logic with optional artificial latency."""
        # Simulate processing time if specified
        if self.latency_ms > 0:
            await asyncio.sleep(self.latency_ms / 1000)
        
        # Get the latest message
        message = context.messages[-1] if context.messages else None
        if not message or message.role != "user":
            # We only process user messages
            return context.task
        
        # Process the message
        content = message.parts[0].content if message.parts else ""
        
        # Create a simple response
        response = Message(
            role="assistant",
            parts=[MessagePart(type="text", content=f"Processed: {content[:50]}...")]
        )
        
        # Update task
        context.task.messages.append(response)
        return context.task


@pytest.mark.benchmark
class TestA2APerformanceBenchmarks:
    """Performance benchmark tests for A2A components."""
    
    @pytest.mark.asyncio
    async def test_client_message_throughput(self, benchmark):
        """Benchmark A2A client message throughput."""
        # Mock client response for consistent testing
        mock_client = A2AClient(base_url="http://non-existent-url")
        
        # Replace _make_request with a mock implementation
        async def mock_make_request(method, path, json_data=None):
            # Simulate a successful response with minimal processing
            if path.endswith("/tasks"):
                return {"id": "benchmark-task-1", "state": "ready", "messages": []}
            elif "/messages" in path:
                return {
                    "id": "benchmark-task-1",
                    "state": "ready",
                    "messages": [
                        {
                            "role": "user",
                            "parts": [{"type": "text", "content": "test message"}]
                        },
                        {
                            "role": "assistant",
                            "parts": [{"type": "text", "content": "test response"}]
                        }
                    ]
                }
            return {}
        
        mock_client._make_request = mock_make_request
        
        # Define the benchmark function
        async def run_client_message():
            task = await mock_client.create_task()
            message = Message(
                role="user",
                parts=[MessagePart(type="text", content="benchmark message")]
            )
            response = await mock_client.send_message(task.id, message)
            return response
        
        # Run the benchmark (use a wrapper to run async function)
        def run_benchmark():
            return asyncio.run(run_client_message())
        
        result = benchmark(run_benchmark)
        print(f"\nA2A Client Message Throughput - Mean time: {result.stats['mean']:.6f}s")
    
    @pytest.mark.asyncio
    async def test_orchestration_routing_performance(self, benchmark):
        """Benchmark A2A orchestration routing performance."""
        # Create a mock orchestrator
        config = OrchestrationConfig(
            routes=[
                AgentRoute(
                    source_agent="agent1",
                    type=RouteType.CONDITIONAL,
                    conditions=[]
                ),
                AgentRoute(
                    source_agent="agent2",
                    type=RouteType.SEQUENTIAL,
                    destination_agents=["agent3"]
                ),
            ],
            entry_points=["agent1"]
        )
        
        registry = A2ARegistryManager()
        orchestrator = A2AOrchestrator(
            config=config,
            registry_manager=registry,
            agent_url_map={
                "agent1": "http://localhost:1",
                "agent2": "http://localhost:2",
                "agent3": "http://localhost:3",
            }
        )
        
        # Mock the get_route method to avoid actual lookups
        def mock_get_route(agent_id, task_data):
            if agent_id == "agent1":
                return "agent2"
            elif agent_id == "agent2":
                return "agent3"
            return None
        
        orchestrator._get_route = mock_get_route
        
        # Define benchmark function
        async def run_routing():
            task_data = {
                "id": "benchmark-task",
                "state": "ready",
                "messages": [
                    {
                        "role": "user",
                        "parts": [{"type": "text", "content": "test message"}]
                    }
                ]
            }
            
            # Test route determination performance
            start_time = time.time()
            route = orchestrator._get_route("agent1", task_data)
            end_time = time.time()
            
            return end_time - start_time
        
        # Run the benchmark
        def run_benchmark():
            return asyncio.run(run_routing())
        
        result = benchmark(run_benchmark)
        print(f"\nA2A Orchestration Routing - Mean time: {result.stats['mean']:.6f}s")
    
    @pytest.mark.asyncio
    async def test_agent_executor_latency(self):
        """Test the impact of agent executor latency on performance."""
        # Create executors with varying latency
        latencies = [0, 50, 100, 200, 500]  # milliseconds
        results = {}
        
        for latency in latencies:
            executor = BenchmarkAgentExecutor(latency_ms=latency)
            
            # Create a test context
            context = A2ARequestContext(
                task=Task(
                    id="benchmark-task",
                    state=TaskState.READY,
                    messages=[
                        Message(
                            role="user",
                            parts=[MessagePart(type="text", content="benchmark message")]
                        )
                    ]
                ),
                messages=[
                    Message(
                        role="user",
                        parts=[MessagePart(type="text", content="benchmark message")]
                    )
                ]
            )
            
            # Run multiple iterations for more stable measurements
            iterations = 5
            execution_times = []
            
            for _ in range(iterations):
                start_time = time.time()
                await executor.execute(context)
                execution_time = (time.time() - start_time) * 1000  # convert to ms
                execution_times.append(execution_time)
            
            # Calculate stats
            results[latency] = {
                "mean": statistics.mean(execution_times),
                "min": min(execution_times),
                "max": max(execution_times),
                "stdev": statistics.stdev(execution_times) if len(execution_times) > 1 else 0
            }
        
        # Print results
        print("\nAgent Executor Performance with Varying Latency:")
        print(f"{'Latency (ms)': <15} {'Mean (ms)': <15} {'Min (ms)': <15} {'Max (ms)': <15} {'StdDev (ms)': <15}")
        print("-" * 75)
        
        for latency, stats in results.items():
            print(
                f"{latency: <15.1f} {stats['mean']: <15.2f} {stats['min']: <15.2f} "
                f"{stats['max']: <15.2f} {stats['stdev']: <15.2f}"
            )
    
    @pytest.mark.asyncio
    async def test_connection_pooling_impact(self, benchmark):
        """Benchmark the impact of connection pooling on A2A client performance."""
        # This would require an actual HTTP server, so we'll just simulate it
        # In a real test, we'd set up an actual server and test with different
        # connection pool configurations
        
        # Define benchmark function that simulates connection pooling effect
        async def run_with_pooling(pool_size):
            # Simulate multiple concurrent requests with a pool
            start_time = time.time()
            tasks = []
            
            # Create a number of tasks to simulate concurrent requests
            concurrency = 10
            
            # Create a semaphore to limit concurrency based on pool size
            semaphore = asyncio.Semaphore(pool_size)
            
            async def make_request():
                async with semaphore:
                    # Simulate network latency
                    await asyncio.sleep(0.05)
                    return {"success": True}
            
            # Create and gather tasks
            for _ in range(concurrency):
                tasks.append(asyncio.create_task(make_request()))
            
            await asyncio.gather(*tasks)
            end_time = time.time()
            
            return end_time - start_time
        
        # Test with different pool sizes
        pool_sizes = [1, 2, 5, 10]
        results = {}
        
        for pool_size in pool_sizes:
            # Define benchmark wrapper for specific pool size
            def run_benchmark():
                return asyncio.run(run_with_pooling(pool_size))
            
            result = benchmark.pedantic(
                run_benchmark,
                rounds=5,
                iterations=1,
                name=f"connection_pool_size_{pool_size}"
            )
            
            results[pool_size] = result.stats["mean"]
        
        # Print results
        print("\nConnection Pooling Performance Impact:")
        print(f"{'Pool Size': <10} {'Mean Time (s)': <15}")
        print("-" * 25)
        
        for pool_size, mean_time in results.items():
            print(f"{pool_size: <10} {mean_time: <15.6f}")


if __name__ == "__main__":
    pytest.main(["-xvs", __file__])
