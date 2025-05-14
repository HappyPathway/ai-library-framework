"""Protocol Buffer utility script for generating Python code from proto files.

This script handles the generation of Python code from Protocol Buffer (.proto) definitions.
It's designed to be run directly or imported by other scripts.

Usage:
    python -m schemas.messaging.protobuf.generate

Dependencies:
    - protobuf
    - grpcio
    - grpcio-tools
"""

import os
import sys
import subprocess
from pathlib import Path

def ensure_dependencies():
    """Ensure all required dependencies are installed."""
    try:
        import grpc
        from google.protobuf.compiler import plugin_pb2 as _
    except ImportError:
        print("Installing dependencies for Protocol Buffers...")
        subprocess.check_call([
            sys.executable, "-m", "pip", "install",
            "grpcio", "grpcio-tools", "protobuf"
        ])
        print("Dependencies installed successfully.")

def get_proto_dir():
    """Get the directory containing the .proto files."""
    # Get the directory containing this script
    current_dir = Path(__file__).parent.absolute()
    return current_dir

def generate_python_code():
    """Generate Python code from .proto files."""
    proto_dir = get_proto_dir()
    output_dir = proto_dir
    
    # Find all .proto files in the proto_dir
    proto_files = list(proto_dir.glob("*.proto"))
    
    if not proto_files:
        print(f"No .proto files found in {proto_dir}")
        return
    
    # Ensure the proto_dir is in the Python path
    sys.path.insert(0, str(proto_dir.parent.parent.parent))  # Add root project dir
    
    # Generate Python code using protoc
    for proto_file in proto_files:
        proto_path = proto_file.relative_to(proto_dir.parent.parent.parent)
        print(f"Generating Python code for {proto_path}...")
        
        # The command to run protoc
        cmd = [
            sys.executable, "-m", "grpc_tools.protoc",
            f"--proto_path={proto_dir.parent.parent.parent}",  # Root dir
            f"--python_out={proto_dir.parent.parent.parent}",  # Output to the same root
            f"--grpc_python_out={proto_dir.parent.parent.parent}",  # GRPC output
            str(proto_path)
        ]
        
        try:
            subprocess.check_call(cmd)
            print(f"Successfully generated Python code for {proto_path}")
        except subprocess.CalledProcessError as e:
            print(f"Failed to generate Python code for {proto_path}: {e}")

if __name__ == "__main__":
    ensure_dependencies()
    generate_python_code()
