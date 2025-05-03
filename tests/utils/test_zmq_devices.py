"""Tests for ZMQ device functionality."""

import logging
import threading
import time
from typing import Any, Generator

import pytest
import zmq

from utils.schemas.zmq_devices import AuthConfig
from utils.zmq_devices import (DEFAULT_POLL_TIMEOUT, BaseDevice, DeviceConfig,
                               DeviceError, DeviceManager, DeviceType,
                               ThreadDevice)

logger = logging.getLogger(__name__)


@pytest.fixture
def zmq_context(request) -> Generator[zmq.Context, None, None]:
    """Fixture providing a ZMQ context."""
    ctx = zmq.Context()
    yield ctx
    ctx.term()


@pytest.fixture
def random_ports():
    """Get random available ports."""
    context = zmq.Context()
    ports = []
    for _ in range(3):  # We need 3 ports
        socket = context.socket(zmq.PAIR)
        port = socket.bind_to_random_port("tcp://127.0.0.1")
        ports.append(port)
        socket.close()
    context.term()
    return ports


@pytest.fixture
def device_config() -> DeviceConfig:
    """Fixture providing basic device configuration."""
    return DeviceConfig(
        device_type=DeviceType.QUEUE,
        frontend_addr="tcp://127.0.0.1:5559",
        backend_addr="tcp://127.0.0.1:5560",
        ignore_errors=False
    )


def test_queue_device_basic_operation(zmq_context: zmq.Context, device_config: DeviceConfig) -> None:
    """Test basic operation of a queue device."""
    # Initialize device
    device = BaseDevice(device_config)
    device.start()

    frontend_client = None
    backend_client = None
    thread = None

    try:
        # Create client sockets
        frontend_client = zmq_context.socket(zmq.REQ)
        backend_client = zmq_context.socket(zmq.REP)

        frontend_client.connect(device_config.frontend_addr)
        backend_client.connect(device_config.backend_addr)

        # Test message forwarding
        test_message = b"test"
        event = threading.Event()
        stop_thread = threading.Event()

        def backend_handler() -> None:
            try:
                while not stop_thread.is_set():
                    if backend_client.poll(timeout=100) == zmq.POLLIN:
                        msg = backend_client.recv()
                        assert msg == test_message
                        backend_client.send(b"received")
                        event.set()
                        break
            except Exception as e:
                logger.error(f"Backend handler error: {e}")
                event.set()  # Set event to prevent test hanging

        # Start backend handler thread
        thread = threading.Thread(target=backend_handler)
        thread.start()

        # Send message through frontend
        frontend_client.send(test_message)

        # Wait for response
        assert event.wait(
            timeout=2.0), "Timeout waiting for message forwarding"

        # Only try to receive if we haven't hit a timeout
        if not stop_thread.is_set():
            response = frontend_client.recv()
            assert response == b"received"

    finally:
        # Signal thread to stop
        if thread is not None:
            stop_thread.set()
            thread.join(timeout=1.0)

        # Clean up sockets
        if frontend_client:
            frontend_client.close()
        if backend_client:
            backend_client.close()

        # Clean up device
        device.stop()
        if not device.join(timeout=1.0):
            logger.warning("Device thread didn't exit cleanly")
            # Force context cleanup in case device is stuck


def test_device_auth(zmq_context: zmq.Context, tmp_path: Any) -> None:
    """Test device with CURVE authentication."""
    # Generate test certificates
    public_key = b'rq:rM>}U?@Lns47E1%kR.o@n%FcmmsL/@{H8]yf7'
    secret_key = b'JTKVSB%%)wK0E.X)V>+}o?pNmC{O&4W4b!Ni{Lh6'

    auth_config = AuthConfig(
        server_public_key=public_key,
        server_secret_key=secret_key,
        certificates_dir=str(tmp_path)
    )

    config = DeviceConfig(
        device_type=DeviceType.QUEUE,
        frontend_addr="tcp://127.0.0.1:5561",
        backend_addr="tcp://127.0.0.1:5562",
        auth_config=auth_config
    )

    device = ThreadDevice(config)
    device.start()

    try:
        # Create authenticated client sockets
        frontend_client = zmq_context.socket(zmq.REQ)
        frontend_client.curve_secretkey = secret_key
        frontend_client.curve_publickey = public_key
        frontend_client.curve_serverkey = public_key

        backend_client = zmq_context.socket(zmq.REP)
        backend_client.curve_secretkey = secret_key
        backend_client.curve_publickey = public_key
        backend_client.curve_serverkey = public_key

        frontend_client.connect(config.frontend_addr)
        backend_client.connect(config.backend_addr)

        # Test authenticated communication
        test_message = b"secure test"
        event = threading.Event()

        def secure_backend_handler() -> None:
            msg = backend_client.recv()
            assert msg == test_message
            backend_client.send(b"secure received")
            event.set()

        thread = threading.Thread(target=secure_backend_handler)
        thread.start()

        frontend_client.send(test_message)
        assert event.wait(timeout=2.0), "Timeout waiting for secure message"
        response = frontend_client.recv()
        assert response == b"secure received"

        thread.join()

    finally:
        device.stop()
        device.join(timeout=2.0)


def test_device_cleanup(zmq_context: zmq.Context, device_config: DeviceConfig) -> None:
        """Test proper cleanup of device resources."""
        device = ThreadDevice(device_config)
        device.start()

    # Let the device initialize
    time.sleep(0.1)

    # Stop and wait for cleanup
    device.stop()
    device.join(timeout=2.0)

    assert not device.is_alive(), "Device thread should not be alive"

    # Try to bind to the same ports - should succeed if cleanup was proper
    test_socket1 = zmq_context.socket(zmq.REP)
    test_socket2 = zmq_context.socket(zmq.REQ)

    try:
        test_socket1.bind(device_config.frontend_addr)
        test_socket2.bind(device_config.backend_addr)
    except zmq.ZMQError as e:
        pytest.fail(f"Failed to bind to device ports after cleanup: {e}")
    finally:
        test_socket1.close()
        test_socket2.close()


class TestDeviceManager:
    """Test suite for ZMQ device management."""

    def test_queue_device(self, random_ports):
        """Test basic queue device functionality."""
        frontend_port, backend_port, monitor_port = random_ports
        poller = None

        with DeviceManager() as devices:
            # Create and start queue device
            device = devices.create_queue(
                frontend=f"tcp://*:{frontend_port}",
                backend=f"tcp://*:{backend_port}",
                monitor=f"tcp://*:{monitor_port}"
            )
            device.start()

            # Create client sockets
            context = zmq.Context.instance()
            sender = context.socket(zmq.DEALER)
            receiver = context.socket(zmq.ROUTER)
            monitor = context.socket(zmq.SUB)

            # Set timeouts to avoid hanging
            sender.setsockopt(zmq.SNDTIMEO, 1000)  # 1 second send timeout
            receiver.setsockopt(zmq.RCVTIMEO, 1000)  # 1 second receive timeout
            monitor.setsockopt(zmq.RCVTIMEO, 1000)  # 1 second receive timeout

            try:
                sender.connect(f"tcp://localhost:{frontend_port}")
                receiver.connect(f"tcp://localhost:{backend_port}")
                monitor.connect(f"tcp://localhost:{monitor_port}")
                monitor.setsockopt_string(zmq.SUBSCRIBE, "")

                # Use poller to check if sockets are ready
                poller = zmq.Poller()
                poller.register(receiver, zmq.POLLIN)
                poller.register(monitor, zmq.POLLIN)

                # Allow time for connections to establish
                time.sleep(0.1)  # 100ms should be enough

                # Allow time for connections
                time.sleep(0.1)

                # Test message forwarding
                sender.send_string("test")

                # ROUTER socket receives [identity, empty delimiter, message]
                identity = receiver.recv()
                empty = receiver.recv()
                message = receiver.recv_string()
                assert message == "test"

                # Monitor receives the complete message parts
                mon_identity = monitor.recv()
                mon_empty = monitor.recv()
                mon_message = monitor.recv_string()
                assert mon_message == "test"

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

    def test_process_device(zmq_context: zmq.Context, device_config: DeviceConfig) -> None:
        """Test ProcessDevice implementation."""
        from utils.zmq_devices import ProcessDevice

        device = ProcessDevice(device_config)
        device.start()

        try:
            # Verify process is running
            assert device.is_alive(), "Device process should be running"

            # Create client sockets
            frontend_client = zmq_context.socket(zmq.REQ)
            backend_client = zmq_context.socket(zmq.REP)

            frontend_client.connect(device_config.frontend_addr)
            backend_client.connect(device_config.backend_addr)

            # Test inter-process communication
            test_message = b"process test"
            event = threading.Event()

            def process_backend_handler() -> None:
                msg = backend_client.recv()
                assert msg == test_message
                backend_client.send(b"process received")
                event.set()

            thread = threading.Thread(target=process_backend_handler)
            thread.start()

            # Send message through frontend
            frontend_client.send(test_message)
            assert event.wait(
                timeout=2.0), "Timeout waiting for process device"
            response = frontend_client.recv()
            assert response == b"process received"

            thread.join()

        finally:
            device.stop()
            device.join(timeout=2.0)
            assert not device.is_alive(), "Device process should be terminated"

    def test_device_manager() -> None:
        """Test DeviceManager functionality."""
        manager = DeviceManager()

        # Create multiple devices
        configs = [
            DeviceConfig(
                device_type=DeviceType.QUEUE,
                frontend_addr=f"tcp://127.0.0.1:{5570 + i}",
                backend_addr=f"tcp://127.0.0.1:{5571 + i}"
            )
            for i in range(3)
        ]

        # Start devices through manager
        for config in configs:
            manager.start_device(config)

        try:
            assert len(
                manager.active_devices) == 3, "Should have 3 active devices"

            # Verify all devices are running
            for device in manager.active_devices:
                assert device.is_alive(), "All devices should be running"

        finally:
            # Stop all devices
            manager.stop_all()

            # Verify cleanup
            assert len(
                manager.active_devices) == 0, "All devices should be stopped"
            for device in manager._devices:
                assert not device.is_alive(), "All devices should be terminated"
