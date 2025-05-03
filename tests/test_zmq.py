"""ZMQ Module Tests"""

import pytest
import zmq

from utils.schemas.zmq import SocketType
from utils.zmq import ZMQError, ZMQManager


class TestZMQManager:
    @pytest.fixture
    def random_port(self):
        """Get a random available port."""
        context = zmq.Context()
        socket = context.socket(zmq.PAIR)
        port = socket.bind_to_random_port("tcp://127.0.0.1")
        socket.close()
        context.term()
        return port

    def test_pub_sub_pattern(self, random_port):
        """Test publisher/subscriber pattern."""
        with ZMQManager() as zmq:
            # Setup publisher
            pub_addr = f"tcp://*:{random_port}"
            sub_addr = f"tcp://localhost:{random_port}"

            with zmq.socket(SocketType.PUB, pub_addr, bind=True) as pub:
                with zmq.socket(SocketType.SUB, sub_addr, topics=["test"]) as sub:
                    # Wait for connection with poll
                    for _ in range(50):  # 5 second timeout
                        if sub.poll(timeout_ms=100):
                            break
                    else:
                        pytest.fail("Connection timeout")

                    # Send message
                    assert pub.send_message("Hello", topic="test")

                    # Receive message
                    message = sub.receive()
                    assert message is not None
                    assert message.topic == "test"
                    assert message.payload.decode() == "Hello"

    def test_invalid_address(self):
        """Test error handling for invalid address."""
        with ZMQManager() as zmq:
            with pytest.raises(ZMQError):
                with zmq.socket(SocketType.PUB, "invalid://address"):
                    pass
