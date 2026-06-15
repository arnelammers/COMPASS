$SCRIPT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path
$ROOT_DIR = Resolve-Path "$SCRIPT_DIR\..\.."

$DATA_DIR = Join-Path $ROOT_DIR "data"

# Only initialize if data folder does NOT exist
if (!(Test-Path $DATA_DIR)) {

    Write-Host "Creating data structure..."

    New-Item -ItemType Directory -Force -Path "$DATA_DIR\test\raw" | Out-Null

    @"
filename,type,group,fraction,replicate
sample1.mzML,sample,A,POC,1
"@ | Set-Content "$DATA_DIR\test\metadata.csv"

    Write-Host "Created data/ with metadata.csv"
}
else {
    Write-Host "data/ already exists, skipping initialization"
}


# Ensure config exists
$configDir = "$ROOT_DIR\config"
$configFile = "$configDir\config.yaml"
$exampleFile = "$configDir\config_example.yaml"

New-Item -ItemType Directory -Force -Path $configDir | Out-Null

if (!(Test-Path $configFile)) {
    if (Test-Path $exampleFile) {
        Copy-Item $exampleFile $configFile
        Write-Host "Copied config_example.yaml → config.yaml"
    } else {
        Write-Host "Warning: config_example.yaml not found"
    }
} else {
    Write-Host "config.yaml already exists, skipping copy"
}

Write-Host "Project initialized at $ROOT_DIR"