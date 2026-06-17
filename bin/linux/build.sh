#!/usr/bin/env bash

# directory of this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# project root (two levels up from bin/linux)
ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

docker build -t compass-app "$ROOT_DIR"