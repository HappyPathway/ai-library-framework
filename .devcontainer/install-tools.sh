#!/bin/bash
# Script to install additional tools defined in tools.json

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TOOLS_JSON="$SCRIPT_DIR/tools.json"

# Function to install apt packages
install_apt_packages() {
    echo "Installing apt packages..."
    packages=$(jq -r '.apt_packages | join(" ")' "$TOOLS_JSON")
    
    if [ -n "$packages" ]; then
        apt-get update
        apt-get install -y --no-install-recommends $packages
        rm -rf /var/lib/apt/lists/*
        echo "✓ Apt packages installed"
    else
        echo "× No apt packages specified"
    fi
}

# Function to install pip packages
install_pip_packages() {
    echo "Installing pip packages..."
    packages=$(jq -r '.pip_packages | join(" ")' "$TOOLS_JSON")
    
    if [ -n "$packages" ]; then
        pip install --no-cache-dir $packages
        echo "✓ Pip packages installed"
    else
        echo "× No pip packages specified"
    fi
}

# Function to install npm packages
install_npm_packages() {
    echo "Installing npm packages..."
    if ! command -v npm &> /dev/null; then
        echo "× npm not installed. Skipping npm packages."
        return
    fi
    
    packages=$(jq -r '.npm_packages | join(" ")' "$TOOLS_JSON")
    
    if [ -n "$packages" ]; then
        npm install -g $packages
        echo "✓ npm packages installed"
    else
        echo "× No npm packages specified"
    fi
}

# Function to install custom tools
install_custom_tools() {
    echo "Installing custom tools..."
    custom_tools=$(jq -c '.custom_tools[]' "$TOOLS_JSON" 2>/dev/null)
    
    if [ -z "$custom_tools" ]; then
        echo "× No custom tools specified"
        return
    fi
    
    while IFS= read -r tool; do
        tool_name=$(echo "$tool" | jq -r '.name')
        version=$(echo "$tool" | jq -r '.version')
        install_command=$(echo "$tool" | jq -r '.install_command')
        
        echo "Installing $tool_name v$version..."
        
        # Replace ${version} with the actual version in the command
        install_command=${install_command/\${version}/$version}
        
        # Execute the command
        eval "$install_command"
        echo "✓ $tool_name installed"
    done <<< "$custom_tools"
}

# Main execution
echo "Starting tools installation..."

if [ ! -f "$TOOLS_JSON" ]; then
    echo "Error: tools.json not found at $TOOLS_JSON"
    exit 1
fi

install_apt_packages
install_pip_packages
install_npm_packages
install_custom_tools

echo "All tools installation completed!"
