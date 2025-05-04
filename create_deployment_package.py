#!/usr/bin/env python3
"""
Deployment Package Creator

This script creates a minimal deployment package with only the dependencies
needed for a specific use case.

Usage:
    python create_deployment_package.py --features ai mcp --output ./deployment

This will create a deployment package with only the AI and MCP dependencies.
"""

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Create a minimal deployment package")
    parser.add_argument("--features", nargs="+", choices=["ai", "mcp", "cloud", "zmq"],
                        default=[], help="Features to include")
    parser.add_argument("--output", type=str, required=True,
                        help="Output directory for the deployment package")
    return parser.parse_args()


def create_deployment_package(features, output_dir):
    """Create a deployment package with the specified features."""
    # Create a temporary directory for the virtual environment
    with tempfile.TemporaryDirectory() as temp_dir:
        venv_dir = Path(temp_dir) / "venv"

        # Create a virtual environment
        subprocess.run([sys.executable, "-m", "venv",
                       str(venv_dir)], check=True)

        # Get the pip path
        if os.name == "nt":  # Windows
            pip_path = venv_dir / "Scripts" / "pip"
        else:  # Unix/Linux/Mac
            pip_path = venv_dir / "bin" / "pip"

        # Install the base requirements
        subprocess.run([str(pip_path), "install", "-r",
                       "requirements/base.txt"], check=True)

        # Install the feature-specific requirements
        for feature in features:
            subprocess.run([str(pip_path), "install", "-r",
                           f"requirements/{feature}.txt"], check=True)

        # Install the production requirements
        subprocess.run([str(pip_path), "install", "-r",
                       "requirements/prod.txt"], check=True)

        # Create the output directory
        os.makedirs(output_dir, exist_ok=True)

        # Copy the project files
        shutil.copytree("utils", os.path.join(output_dir, "utils"),
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))

        # Copy the site-packages
        if os.name == "nt":  # Windows
            site_packages = venv_dir / "Lib" / "site-packages"
        else:  # Unix/Linux/Mac
            # Find the site-packages directory
            python_version = subprocess.check_output(
                [str(venv_dir / "bin" / "python"), "-c",
                 "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"],
                universal_newlines=True).strip()
            site_packages = venv_dir / "lib" / \
                f"python{python_version}" / "site-packages"

        shutil.copytree(site_packages, os.path.join(output_dir, "site-packages"),
                        ignore=shutil.ignore_patterns("pip", "setuptools", "wheel", "pkg_resources", "*.pyc"))

        # Create a run script
        with open(os.path.join(output_dir, "run.py"), "w") as f:
            f.write("""#!/usr/bin/env python3
import sys
import os

# Add the site-packages directory to the Python path
site_packages = os.path.join(os.path.dirname(os.path.abspath(__file__)), "site-packages")
sys.path.insert(0, site_packages)

# Add the main directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import your application entry point
# from your_app import main
# main()

# For testing purposes, just print out the available modules
print("Available modules:")
for module_name in sorted(sys.modules.keys()):
    print(f"  - {module_name}")
""")

        # Make the run script executable
        os.chmod(os.path.join(output_dir, "run.py"), 0o755)

        print(f"\nDeployment package created at: {output_dir}")
        print(f"Features included: base, {', '.join(features)}, prod")
        print("\nTo run the application:")
        print(f"  python {output_dir}/run.py")


if __name__ == "__main__":
    args = parse_arguments()
    create_deployment_package(args.features, args.output)
