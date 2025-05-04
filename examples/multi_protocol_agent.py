"""Multi-Protocol Agent Communication Example.

This example demonstrates how to build agents that can communicate through
multiple messaging protocols (Redis and ZMQ) depending on the use case.

This pattern is useful for:
1. Hybrid environments where some components only support certain protocols
2. Gradual migration from one messaging system to another
3. Optimizing for different communication patterns (pub/sub vs. req/rep)

Example:
    $ python -m examples.multi_protocol_agent

Requirements:
    - Redis server running locally
    - Python packages: pyzmq, redis
"""

import argparse
import asyncio
import json
import logging
import signal
import sys
import threading
import time
from typing import Any, Dict, List, Optional

from utils.messaging.redis import RedisClient, RedisPubSub, RedisStream
from utils.zmq import ZMQClient
from utils.zmq_devices import DeviceType, ZMQDevice

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("multi_protocol_agent")


class HybridMessagingAgent:
    """Agent that can communicate via both Redis and ZMQ."""

    def __init__(self, agent_id: str):
        """Initialize the agent.

        Args:
            agent_id: Unique identifier for this agent
        """
        self.agent_id = agent_id
        self.running = False

        # Initialize Redis clients
        self.redis_client = RedisClient()
        self.redis_pubsub = RedisPubSub(self.redis_client)
        self.redis_stream = RedisStream(
            "hybrid_agent_tasks", self.redis_client)

        # Initialize ZMQ client
        self.zmq_client = ZMQClient()

        # Set up signal handlers for clean shutdown
        signal.signal(signal.SIGINT, self._handle_exit)
        signal.signal(signal.SIGTERM, self._handle_exit)

    def _handle_exit(self, signum, frame):
        """Handle termination signals."""
        logger.info(f"Received signal {signum}, shutting down...")
        self.running = False
        # Give background threads time to complete
        time.sleep(0.5)
        sys.exit(0)

    def start(self):
        """Start the agent."""
        self.running = True
        logger.info(f"Agent {self.agent_id} started")

        # Subscribe to Redis channels
        self.redis_pubsub.subscribe("broadcast", self._handle_redis_broadcast)
        self.redis_pubsub.run_in_thread()

        # Setup Redis Stream consumer group
        try:
            self.redis_stream.create_consumer_group("agents", self.agent_id)
        except Exception as e:
            logger.warning(f"Error creating consumer group: {str(e)}")

        # Start ZMQ sockets
        self.zmq_client.add_subscriber("tcp://localhost:5555", "updates")
        self.zmq_client.subscriber_callback = self._handle_zmq_message

        # Set up request socket
        self.zmq_client.setup_request("tcp://localhost:5556")

        return self

    def run(self):
        """Run the agent's main loop."""
        try:
            while self.running:
                # Process ZMQ messages
                self.zmq_client.receive(timeout=100)  # Non-blocking

                # Process Redis stream messages
                messages = self.redis_stream.read_group(count=5, block=500)
                for message in messages:
                    try:
                        self._process_task(message["data"])
                        self.redis_stream.acknowledge(message["id"])
                    except Exception as e:
                        logger.error(f"Error processing message: {str(e)}")

                time.sleep(0.1)  # Small sleep to prevent CPU spinning
        finally:
            self.stop()

    def stop(self):
        """Stop the agent."""
        if not self.running:
            return

        self.running = False
        logger.info(f"Stopping agent {self.agent_id}")

        # Clean up Redis connections
        self.redis_pubsub.stop()

        # Clean up ZMQ connections
        self.zmq_client.close()

    def _handle_redis_broadcast(self, message):
        """Handle broadcast messages from Redis pub/sub.

        Args:
            message: The received message data
        """
        logger.info(f"Redis broadcast received: {message}")

        # Process the message based on its type
        if isinstance(message, dict) and "type" in message:
            if message["type"] == "command":
                self._execute_command(message["command"], source="redis")

    def _handle_zmq_message(self, topic, message):
        """Handle messages from ZMQ subscription.

        Args:
            topic: The topic the message was published on
            message: The received message data
        """
        logger.info(f"ZMQ message received on topic {topic}")

        # Try to parse JSON if it's a string
        if isinstance(message, str):
            try:
                message = json.loads(message)
            except json.JSONDecodeError:
                pass

        # Process the message based on its type
        if isinstance(message, dict) and "type" in message:
            if message["type"] == "command":
                self._execute_command(message["command"], source="zmq")

    def _execute_command(self, command: str, source: str):
        """Execute a command received from any messaging system.

        Args:
            command: The command to execute
            source: The source of the command (redis or zmq)
        """
        logger.info(f"Executing command from {source}: {command}")

        # Implement command execution logic
        if command == "ping":
            # Respond with pong over the same protocol
            if source == "redis":
                self.redis_pubsub.publish("responses", {
                    "from": self.agent_id,
                    "type": "response",
                    "response": "pong"
                })
            elif source == "zmq":
                response = json.dumps({
                    "from": self.agent_id,
                    "type": "response",
                    "response": "pong"
                })
                self.zmq_client.publish("responses", response)

    def _process_task(self, task):
        """Process a task from the Redis stream.

        Args:
            task: Task data from Redis stream
        """
        logger.info(f"Processing task: {task}")

        # Example of sending a ZMQ request based on Redis task
        if "action" in task and task["action"] == "query":
            response = self.zmq_client.request(task["query"])

            # Store the result back in Redis
            self.redis_client.set_json(
                f"result:{task['id']}",
                {"query": task["query"], "response": response}
            )

            logger.info(f"Task {task['id']} completed")


def send_test_messages():
    """Send some test messages through both protocols."""
    # Send Redis pub/sub message
    pubsub = RedisPubSub()
    pubsub.publish("broadcast", {
        "type": "command",
        "command": "ping",
        "timestamp": time.time()
    })

    # Send Redis stream message
    stream = RedisStream("hybrid_agent_tasks")
    stream.add({
        "id": f"task-{int(time.time())}",
        "action": "query",
        "query": "test_query",
        "timestamp": str(time.time())
    })

    # Send ZMQ pub/sub message
    zmq_client = ZMQClient()
    zmq_client.setup_publisher("tcp://*:5555")
    zmq_client.publish("updates", json.dumps({
        "type": "command",
        "command": "ping",
        "timestamp": time.time()
    }))

    # Clean up
    zmq_client.close()


def setup_zmq_responder():
    """Set up a ZMQ responder for testing."""
    def responder_thread():
        zmq_client = ZMQClient()
        zmq_client.setup_reply("tcp://*:5556")

        while True:
            try:
                request = zmq_client.receive_request()
                if request:
                    # Echo the request as a response
                    zmq_client.send_reply(f"Response to: {request}")
            except KeyboardInterrupt:
                break

        zmq_client.close()

    threading.Thread(target=responder_thread, daemon=True).start()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Multi-protocol agent example")
    parser.add_argument(
        "--id",
        default=f"agent-{int(time.time())}",
        help="Agent ID"
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Send test messages"
    )

    args = parser.parse_args()

    if args.test:
        send_test_messages()
        return

    # Set up ZMQ responder in background thread
    setup_zmq_responder()

    # Start the agent
    agent = HybridMessagingAgent(args.id).start()

    try:
        # Send some test messages after a short delay
        def delayed_test():
            time.sleep(2)  # Give the agent time to set up
            send_test_messages()

        threading.Thread(target=delayed_test, daemon=True).start()

        # Run the agent
        agent.run()
    except KeyboardInterrupt:
        agent.stop()


if __name__ == "__main__":
    main()
