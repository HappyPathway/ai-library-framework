"""ZMQ Device Schema Definitions.

This module defines the data models and configuration schemas for ZMQ devices
and authentication mechanisms.

Key Components:
    DeviceType: Enum for ZMQ device types
    DeviceConfig: Base configuration for ZMQ devices
    AuthConfig: Configuration for ZMQ authentication
"""

from enum import Enum, auto
from typing import Optional, Dict, List
from pydantic import BaseModel, Field

class DeviceType(str, Enum):
    """ZMQ device types."""
    QUEUE = "QUEUE"
    FORWARDER = "FORWARDER"
    STREAMER = "STREAMER"

class DeviceConfig(BaseModel):
    """Base configuration for ZMQ devices."""
    device_type: DeviceType
    frontend_type: str
    backend_type: str
    monitor_type: Optional[str] = None
    frontend_addr: str
    backend_addr: str
    monitor_addr: Optional[str] = None
    bind_frontend: bool = True
    bind_backend: bool = True
    bind_monitor: bool = True

class AuthConfig(BaseModel):
    """Authentication configuration."""
    require_auth: bool = False
    allow_ips: List[str] = Field(default_factory=list)
    deny_ips: List[str] = Field(default_factory=list)
    certificates_dir: Optional[str] = None
    passwords: Dict[str, str] = Field(default_factory=dict)
