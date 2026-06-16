# Get directory of this script
$SCRIPT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path

# Project root (two levels up from bin/windows)
$ROOT_DIR = Resolve-Path "$SCRIPT_DIR\..\.."

docker run -it --rm `
  --memory=14g --shm-size=8g `
  -e "JAVA_TOOL_OPTIONS=-Xmx10g" `
  -v "$ROOT_DIR:/home/bio/workflow" `
  -v "$ROOT_DIR\.sirius-6.3:/home/bio/.sirius-6.3" `
  -v "$ROOT_DIR\.mzmine:/home/bio/.mzmine" `
  compass-app bash