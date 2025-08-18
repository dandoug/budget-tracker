#!/usr/bin/env bash

if docker buildx ls | grep -q '^multiarch'; then
  docker buildx use multiarch
else
  docker buildx create --name multiarch --use
fi
docker buildx inspect --bootstrap

# Optional: install binfmt emulators for cross-building on Linux hosts.
# - Safe to run multiple times; it re-registers emulators.
# - Usually unnecessary on macOS/Windows Docker Desktop (emulation is built-in).
# Enable by exporting INSTALL_BINFMT=1
if [ "${INSTALL_BINFMT:-0}" = "1" ]; then
  if [ "$(uname -s)" = "Linux" ]; then
    echo "Installing binfmt emulators (requires privileged Docker)..."
    docker run --privileged --rm tonistiigi/binfmt --install all
  else
    echo "Skipping binfmt install on non-Linux host (Docker Desktop includes emulation)."
  fi
fi

# Authenticate to a registry (if pushing)
# docker login <registry>

# Run the build from the project root (parent of this script's directory) in a subshell
# so the caller's current directory is not changed.
(
  cd "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/.." || exit 1
  docker buildx build --platform linux/amd64,linux/arm64 -t dandoug/budget-tracker:latest --push .
)

# -----------------------------------------------------------------------------
# Examples:

# Local testing: build and load single-arch images into local Docker
# docker buildx build --platform linux/arm64 -t <image>:arm64 --load .
# docker buildx build --platform linux/amd64 -t <image>:amd64 --load .
#
# Use a specific Dockerfile and context while building multi-arch
# docker buildx build --platform linux/amd64,linux/arm64 -f path/to/Dockerfile -t <registry>/<image>:<tag> --push path/to/context


