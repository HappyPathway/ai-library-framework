#!/bin/bash

# Script to build and push the dev container as a Docker image
# Usage: ./build-and-push.sh [registry_path]
# Example: ./build-and-push.sh myregistry/python-agent-template:latest

set -e

# Get image tag from argument or use default
IMAGE_TAG=${1:-"python-agent-template:latest"}

echo "Building Docker image: $IMAGE_TAG"
docker build -t "$IMAGE_TAG" -f Dockerfile ..

# Check if the user wants to push the image
read -p "Do you want to push this image to a registry? (y/N): " PUSH_IMAGE
if [[ $PUSH_IMAGE =~ ^[Yy]$ ]]; then
    echo "Pushing image to registry..."
    docker push "$IMAGE_TAG"
    echo "Image pushed successfully!"
else
    echo "Image built successfully. To push later, run:"
    echo "docker push $IMAGE_TAG"
fi

echo "To use this image in a devcontainer.json, set:"
echo '  "image": "'"$IMAGE_TAG"'"'
echo "instead of the build section."
