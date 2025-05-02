"""ZMQ Module Tests"""

import pytest
import zmq
from utils.zmq import ZMQManager, ZMQError
from utils.schemas.zmq import SocketType

class TestZMQManager:
    """Test suite for ZMQ utilities."""
    
    def test_pub_sub_pattern(self):
        """Test publisher/subscriber pattern."""
        with ZMQManager() as zmq:
            # Setup publisher
            with zmq.socket(SocketType.PUB, "tcp://*:5555", bind=True) as pub:
                # Setup subscriber
                with zmq.socket(SocketType.SUB, "tcp://localhost:5555", topics=["test"]) as sub:
                    # Allow time for connection
                    import time
                    time.sleep(0.1)
                    
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
