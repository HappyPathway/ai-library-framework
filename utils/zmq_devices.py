"""ZMQ Device Management Module.

This module provides high-level abstractions for ZMQ devices with proper resource
management, monitoring, and error handling.

Key Components:
    DeviceManager: Factory for creating and managing ZMQ devices
    ThreadDevice: Device implementation running in a background thread
    ProcessDevice: Device implementation running in a separate process
    
Example:
    >>> from utils.zmq_devices import DeviceManager
    >>> from utils.schemas.zmq_devices import DeviceType
    >>> 
    >>> # Create a queue device
    >>> with DeviceManager() as devices:
    ...     device = devices.create_queue(
    ...         frontend="tcp://*:5555",
    ...         backend="tcp://*:5556",
    ...         monitor="tcp://*:5557"
    ...     )
    ...     device.start()
"""

import zmq
from contextlib import contextmanager
from threading import Thread
from multiprocessing import Process
from typing import Optional, Union, Any

from .schemas.zmq_devices import DeviceConfig, DeviceType, AuthConfig
from .logging import setup_logging
from .monitoring import Metrics

logger = setup_logging(__name__)
metrics = Metrics(__name__)

class DeviceError(Exception):
    """Base exception for device operations."""
    pass

class BaseDevice:
    """Base class for ZMQ devices."""
    
    def __init__(
        self,
        config: DeviceConfig,
        auth_config: Optional[AuthConfig] = None,
        context: Optional[zmq.Context] = None,
        metrics: Optional[Metrics] = None
    ):
        """Initialize device.
        
        :param config: Device configuration
        :type config: DeviceConfig
        :param auth_config: Optional authentication configuration
        :type auth_config: Optional[AuthConfig]
        :param context: Optional ZMQ context
        :type context: Optional[zmq.Context]
        :param metrics: Optional metrics collector
        :type metrics: Optional[Metrics]
        """
        self.config = config
        self.auth_config = auth_config
        self.context = context or zmq.Context.instance()
        self.metrics = metrics or Metrics(__name__)
        self._running = False
        self._initialize_sockets()
        
    def _initialize_sockets(self):
        """Initialize device sockets."""
        try:
            # Create sockets
            self.frontend = self.context.socket(getattr(zmq, self.config.frontend_type))
            self.backend = self.context.socket(getattr(zmq, self.config.backend_type))
            
            if self.config.monitor_type:
                self.monitor = self.context.socket(getattr(zmq, self.config.monitor_type))
            else:
                self.monitor = None
                
            # Configure bindings
            if self.config.bind_frontend:
                self.frontend.bind(self.config.frontend_addr)
            else:
                self.frontend.connect(self.config.frontend_addr)
                
            if self.config.bind_backend:
                self.backend.bind(self.config.backend_addr)
            else:
                self.backend.connect(self.config.backend_addr)
                
            if self.monitor and self.config.monitor_addr:
                if self.config.bind_monitor:
                    self.monitor.bind(self.config.monitor_addr)
                else:
                    self.monitor.connect(self.config.monitor_addr)
                    
            # Configure authentication if needed
            if self.auth_config and self.auth_config.require_auth:
                self._setup_auth()
                
        except Exception as e:
            logger.error(f"Failed to initialize device sockets: {str(e)}")
            self.metrics.increment("device.init.error")
            raise DeviceError(f"Device initialization failed: {str(e)}") from e
            
    def _setup_auth(self):
        """Configure authentication."""
        try:
            auth = zmq.auth.Authenticator(self.context)
            
            # Configure IP allow/deny lists
            for ip in self.auth_config.allow_ips:
                auth.allow(ip)
            for ip in self.auth_config.deny_ips:
                auth.deny(ip)
                
            # Configure CURVE if certificates directory is provided
            if self.auth_config.certificates_dir:
                auth.configure_curve(domain="*", location=self.auth_config.certificates_dir)
                
            # Configure PLAIN if passwords are provided
            if self.auth_config.passwords:
                auth.configure_plain(domain="*", passwords=self.auth_config.passwords)
                
            auth.start()
            self._auth = auth
            
        except Exception as e:
            logger.error(f"Failed to setup authentication: {str(e)}")
            self.metrics.increment("auth.setup.error")
            raise DeviceError(f"Authentication setup failed: {str(e)}") from e
            
    def start(self):
        """Start the device."""
        raise NotImplementedError("Subclasses must implement start()")
        
    def stop(self):
        """Stop the device."""
        self._running = False
        
    def close(self):
        """Clean up resources."""
        try:
            self.frontend.close()
            self.backend.close()
            if self.monitor:
                self.monitor.close()
        except Exception as e:
            logger.error(f"Error closing device: {str(e)}")
            self.metrics.increment("device.close.error")

class ThreadDevice(BaseDevice):
    """Device implementation running in a background thread."""
    
    def start(self):
        """Start device in a background thread."""
        self._running = True
        self._thread = Thread(target=self._run, daemon=True)
        self._thread.start()
        
    def _run(self):
        """Device main loop."""
        try:
            zmq.proxy_steerable(
                self.frontend,
                self.backend,
                self.monitor
            )
        except Exception as e:
            if self._running:
                logger.error(f"Device error: {str(e)}")
                self.metrics.increment("device.run.error")

class ProcessDevice(BaseDevice):
    """Device implementation running in a separate process."""
    
    def start(self):
        """Start device in a separate process."""
        self._running = True
        self._process = Process(target=self._run, daemon=True)
        self._process.start()
        
    def _run(self):
        """Device main loop."""
        try:
            # Create new context in subprocess
            self.context = zmq.Context()
            self._initialize_sockets()
            
            zmq.proxy_steerable(
                self.frontend,
                self.backend,
                self.monitor
            )
        except Exception as e:
            if self._running:
                logger.error(f"Device error: {str(e)}")
                self.metrics.increment("device.run.error")

class DeviceManager:
    """Factory for creating and managing ZMQ devices."""
    
    def __init__(self, metrics: Optional[Metrics] = None):
        """Initialize device manager."""
        self.context = zmq.Context.instance()
        self.metrics = metrics or Metrics(__name__)
        self.devices = []
        
    def create_queue(
        self,
        frontend: str,
        backend: str,
        monitor: Optional[str] = None,
        use_process: bool = False,
        auth_config: Optional[AuthConfig] = None
    ) -> Union[ThreadDevice, ProcessDevice]:
        """Create a queue device.
        
        :param frontend: Frontend socket address
        :type frontend: str
        :param backend: Backend socket address
        :type backend: str
        :param monitor: Optional monitor socket address
        :type monitor: Optional[str]
        :param use_process: Whether to run in a separate process
        :type use_process: bool
        :param auth_config: Optional authentication configuration
        :type auth_config: Optional[AuthConfig]
        :return: Configured device
        :rtype: Union[ThreadDevice, ProcessDevice]
        """
        config = DeviceConfig(
            device_type=DeviceType.QUEUE,
            frontend_type="ROUTER",
            backend_type="DEALER",
            monitor_type="PUB" if monitor else None,
            frontend_addr=frontend,
            backend_addr=backend,
            monitor_addr=monitor
        )
        
        device_class = ProcessDevice if use_process else ThreadDevice
        device = device_class(config, auth_config, self.context, self.metrics)
        self.devices.append(device)
        return device
        
    def close(self):
        """Clean up all devices."""
        for device in self.devices:
            try:
                device.stop()
                device.close()
            except Exception as e:
                logger.error(f"Error closing device: {str(e)}")
                self.metrics.increment("device.close.error")
