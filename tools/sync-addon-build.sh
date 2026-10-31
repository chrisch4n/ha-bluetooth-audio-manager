#!/bin/sh
# Copy the shared sources into the add-on folder.
#
# This branch is installed as a store repository and built locally by the
# Supervisor (config.yaml has no "image:").  The Supervisor uses the add-on
# folder as the Docker build context, so the Dockerfile cannot reach ../src
# or ../docker - they have to live inside the folder.  Edit src/ and docker/
# as usual, then run this script before committing.
# tests/test_addon_build_context.py fails if the copies drift.
set -eu
cd "$(dirname "$0")/.."
dst=bluetooth_audio_manager
rm -rf "$dst/src" "$dst/rootfs"
cp -R src "$dst/src"
cp -R docker/rootfs "$dst/rootfs"
cp docker/requirements.txt docker/build.yaml "$dst/"
sed -e 's#^COPY docker/requirements.txt #COPY requirements.txt #' \
    -e 's#^COPY docker/rootfs /#COPY rootfs /#' \
    docker/Dockerfile > "$dst/Dockerfile"
find "$dst/src" -name __pycache__ -type d -prune -exec rm -rf {} +
echo "synced into $dst/"
