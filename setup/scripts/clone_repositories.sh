#!/bin/bash
# Repository clone script for development environment
# This script automatically clones required repositories when the container is built

echo "Setting up development environment repositories..."
WORKSPACE_DIR="$(pwd)"
REPO_DIR="${WORKSPACE_DIR}/repositories"

# Create repositories directory if it doesn't exist
mkdir -p "${REPO_DIR}"
echo "Repository directory: ${REPO_DIR}"

# Function to clone or update a repository
clone_or_update_repo() {
    local repo_url="$1"
    local repo_name="$2"
    local repo_path="${REPO_DIR}/${repo_name}"

    echo "Checking ${repo_name} repository..."

    if [ -d "${repo_path}" ]; then
        echo "Repository ${repo_name} already exists, updating..."
        cd "${repo_path}" || exit
        git pull
        cd "${WORKSPACE_DIR}" || exit
    else
        echo "Cloning ${repo_name} repository..."
        git clone "${repo_url}" "${repo_path}"
    fi
}

# Clone or update kagent repository
clone_or_update_repo "https://github.com/kagent/kagent.git" "kagent"

# Clone or update A2A repository
clone_or_update_repo "https://github.com/a2a-dev/a2a.git" "a2a"

echo "Repository setup complete!"
