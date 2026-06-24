#!/usr/bin/env bash

# directory of this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# project root (two levels up from bin/linux)
ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

docker run -it --rm \
  --memory=14g --shm-size=8g \
  --dns=1.1.1.1 \
  --dns=8.8.8.8 \
  -e JAVA_TOOL_OPTIONS="-Xmx10g" \
  -u "$(id -u):$(id -g)" \
  -v "$ROOT_DIR":/home/bio/workflow \
  -v "$ROOT_DIR/.sirius-6.3":/home/bio/.sirius-6.3 \
  -v "$ROOT_DIR/.mzmine":/home/bio/.mzmine \
  compass-app bash