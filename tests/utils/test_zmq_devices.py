"""Tests for ZMQ device functionality."""

import pytest
import zmq
import time
from utils.zmq_devices import DeviceManager, DeviceError
from utils.schemas.zmq_devices import AuthConfig

class TestDeviceManager:
    """Test suite for ZMQ device management."""
    
    def test_queue_device(self):
        """Test basic queue device functionality."""
        with DeviceManager() as devices:
            # Create and start queue device
            device = devices.create_queue(
                frontend="tcp://*:5555",
                backend="tcp://*:5556",
                monitor="tcp://*:5557"
            )
            device.start()
            
            # Allow time for device startup
            time.sleep(0.1)
            
            # Create client sockets
            context = zmq.Context.instance()
            sender = context.socket(zmq.DEALER)
            receiver = context.socket(zmq.ROUTER)
            monitor = context.socket(zmq.SUB)
            
            try:
                sender.connect("tcp://localhost:5555")
                receiver.connect("tcp://localhost:5556")
                monitor.connect("tcp://localhost:5557")
                monitor.setsockopt_string(zmq.SUBSCRIBE, "")
                
                # Allow time for connections
                time.sleep(0.1)
                
                # Test message forwarding
                sender.send_string("test")
                assert receiver.recv_string() == "test"
                assert monitor.recv_string() == "test"
                
            finally:
                sender.close()
                receiver.close()
                monitor.close()
                
    def test_authenticated_device(self):
        """Test device with authentication."""
        auth_config = AuthConfig(
            require_auth=True,
            allow_ips=["127.0.0.1"],
            passwords={"user": "password"}
        )
        
        with DeviceManager() as devices:
            device = devices.create_queue(
                frontend="tcp://*:5555",
                backend="tcp://*:5556",
                auth_config=auth_config
            )
            device.start()
            
            # Test authentication here...
            # (Full authentication testing would require more setup)
