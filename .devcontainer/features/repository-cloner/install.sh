#!/bin/bash
set -e

# Get parameters
REPOSITORIES=${REPOSITORIES:-"kagent/kagent,a2a-dev/a2a"}
TARGET_DIR=${TARGETDIR:-"/workspaces/repositories"}

echo "Repository Cloner Feature activated!"
echo "Will clone repositories: $REPOSITORIES"
echo "Target directory: $TARGET_DIR"

# Create repositories directory if it doesn't exist
mkdir -p "${TARGET_DIR}"

# Function to clone a repository
clone_repository() {
    local repo="$1"
    local repo_url="https://github.com/${repo}.git"
    local repo_name=$(echo "$repo" | cut -d '/' -f 2)
    local repo_path="${TARGET_DIR}/${repo_name}"

    echo "Checking ${repo_name} repository..."

    if [ -d "${repo_path}" ]; then
        echo "Repository ${repo_name} already exists, updating..."
        cd "${repo_path}" || exit
        git pull
        cd - > /dev/null || exit
    else
        echo "Cloning ${repo_name} repository..."
        git clone "${repo_url}" "${repo_path}"
    fi
}

# Clone all repositories
IFS=',' read -ra REPO_ARRAY <<< "$REPOSITORIES"
for repo in "${REPO_ARRAY[@]}"; do
    clone_repository "$repo"
done

echo "Repository setup complete!"
