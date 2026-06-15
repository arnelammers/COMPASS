# Get directory of this script
$SCRIPT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path

# Project root (two levels up from bin/windows)
$ROOT_DIR = Resolve-Path "$SCRIPT_DIR\..\.."

docker build -t compass-app $ROOT_DIR