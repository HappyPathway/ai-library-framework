"""ZMQ Module Tests"""

import time

import pytest
import zmq

from utils.schemas.zmq import SocketType
from utils.zmq import ZMQError, ZMQManager


class TestZMQManager:
    """Test suite for ZMQ utilities."""

    @pytest.fixture
    def random_port(self):
        """Get a random available port."""
        context = zmq.Context()
        socket = None
        try:
            socket = context.socket(zmq.PAIR)
            socket.setsockopt(zmq.LINGER, 0)
            socket.setsockopt(zmq.RCVTIMEO, 1000)
            socket.setsockopt(zmq.SNDTIMEO, 1000)
            port = socket.bind_to_random_port("tcp://127.0.0.1")
            return port
        finally:
            try:
                if socket:
                    socket.close(linger=0)
            finally:
                context.term()

    def test_pub_sub_pattern(self, random_port):
        """Test publisher/subscriber pattern."""
        with ZMQManager() as zmq:
            address = f"tcp://*:{random_port}"
            connect_addr = f"tcp://localhost:{random_port}"

            # Setup publisher
            with zmq.socket(SocketType.PUB, address, bind=True) as pub:
                # Setup subscriber
                with zmq.socket(SocketType.SUB, connect_addr, topics=["test"]) as sub:
                    # Allow time for subscription to be established
                    time.sleep(0.1)

                    # Test multiple messages to ensure stability
                    for i in range(3):
                        test_msg = f"Hello {i}"
                        assert pub.send_message(test_msg, topic="test")

                        # Receive with timeout
                        message = sub.receive(timeout=1000)
                        assert message is not None, f"No message received for iteration {i}"
                        assert message.topic == "test", f"Wrong topic for iteration {i}"
                        assert message.payload.decode(
                        ) == test_msg, f"Wrong payload for iteration {i}"

    def test_invalid_address(self):
        """Test error handling for invalid address."""
        with ZMQManager() as zmq:
            with pytest.raises(ZMQError):
                with zmq.socket(SocketType.PUB, "invalid://address"):
                    pass
