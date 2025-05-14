# ruff: noqa: F401
# pylint: disable=broad-except,no-member,too-many-instance-attributes
"""ZMQ Device Management Module.

DEPRECATED: This module has been moved to ailf.messaging.zmq_devices.
Please update your imports to: from ailf.messaging.zmq_devices import DeviceManager, ThreadDevice

This module provides high-level abstractions for ZMQ devices with proper resource
management, monitoring, and error handling.

Key Components:
    DeviceManager: Factory for creating and managing ZMQ devices
    ThreadDevice: Device implementation running in a background thread
    ProcessDevice: Device implementation running in a separate process
"""
import warnings

# Add deprecation warning
warnings.warn(
    "The utils.messaging.devices module is deprecated. Use ailf.messaging.zmq_devices instead.",
    DeprecationWarning,
    stacklevel=2
)

# Re-export all symbols from the new module location
from ailf.messaging.zmq_devices import *
