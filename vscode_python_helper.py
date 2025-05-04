#!/usr/bin/env python3
"""
VS Code Python Path Helper

This script prints out Python environment information to help configure VS Code.
It shows:
1. Python interpreter path
2. Python version
3. Site-packages directories
4. Installed packages and their locations

Usage:
    python3 vscode_python_helper.py
"""

import importlib
import os
import site
import subprocess
import sys


def main():
    """Print Python environment information."""
    print(f"Python interpreter: {sys.executable}")
    print(f"Python version: {sys.version}")

    print("\nSite-packages directories:")
    for path in site.getsitepackages():
        print(f"  - {path}")

    print("\nUser site-packages directory:")
    print(f"  - {site.getusersitepackages()}")

    print("\nSYSPATH entries:")
    for path in sys.path:
        print(f"  - {path}")

    print("\nInstalled packages:")
    required_packages = [
        "pydantic", "anthropic", "openai", "google-generativeai",
        "google-cloud-secretmanager", "mcp"
    ]

    for package in required_packages:
        try:
            module_name = package.replace("-", "_")
            module = importlib.import_module(module_name)
            location = os.path.dirname(module.__file__)

            # Try to get version using importlib metadata
            try:
                version = module.__version__
            except AttributeError:
                # Fall back to pip show
                try:
                    pip_output = subprocess.check_output(
                        [sys.executable, "-m", "pip", "show", package],
                        stderr=subprocess.STDOUT,
                        universal_newlines=True
                    )
                    for line in pip_output.split('\n'):
                        if line.startswith('Version:'):
                            version = line.split('Version:')[1].strip()
                            break
                    else:
                        version = "unknown"
                except subprocess.CalledProcessError:
                    version = "unknown"

            print(f"  - {package} v{version}")
            print(f"    Location: {location}")
        except ImportError:
            print(f"  - {package}: NOT FOUND")

    print("\nTo configure VS Code, add this to .vscode/settings.json:")
    print("""
{
    "python.defaultInterpreterPath": "%s",
    "python.analysis.extraPaths": [
%s
    ],
    "python.languageServer": "Pylance",
    "python.analysis.typeCheckingMode": "basic"
}
""" % (
        sys.executable,
        "\n".join(f'        "{path}",' for path in site.getsitepackages())
    ))


if __name__ == "__main__":
    main()
