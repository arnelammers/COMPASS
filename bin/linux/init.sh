#!/usr/bin/env bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

DATA_DIR="$ROOT_DIR/data"

# Only initialize if data folder does NOT exist
if [ ! -d "$DATA_DIR" ]; then
  echo "Creating data structure..."

  mkdir -p "$DATA_DIR/test/raw"

  cat > "$DATA_DIR/test/metadata.csv" << EOF
filename,type,group,fraction,replicate
sample1.mzML,sample,A,POC,1
EOF

  echo "Created data/ with metadata.csv"
else
  echo "data/ already exists, skipping initialization"
fi

# Copy config
if [ ! -f "$ROOT_DIR/config/config.yaml" ]; then
  if [ -f "$ROOT_DIR/config/config_example.yaml" ]; then
    cp "$ROOT_DIR/config/config_example.yaml" "$ROOT_DIR/config/config.yaml"
    echo "Copied config_example.yaml → config.yaml"
  else
    echo "Warning: config_example.yaml not found"
  fi
else
  echo "config.yaml already exists, skipping copy"
fi

echo "Project initialized at $ROOT_DIR"