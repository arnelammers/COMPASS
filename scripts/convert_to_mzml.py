import subprocess
import argparse
from glob import glob
from pathlib import Path

# Location of ThermoRawFileParser DLL
THERMO_PARSER_DLL = "/home/mambauser/tools/ThermoRawFileParser-v.2.0.0-dev-linux/ThermoRawFileParser.dll"

# Get snakemake parameters
dataset_dir = Path(snakemake.input["dataset_dir"])

mzml_dir = dataset_dir / "mzml"
raw_dir = dataset_dir / "raw"

# If mzml folder exists, skip conversion
if mzml_dir.exists():
    print(f"mzML folder already exists in {args.dataset_dir}, skipping conversion")
else:
    # Otherwise, convert all raw files
    raw_files = glob(raw_dir / "*.raw")

    # Create mzml directory if not existing
    mzml_dir.mkdir(exist_ok=True)

    for raw_file in raw_files:
        print(f"Converting {raw_file} → {mzml_dir}")
        subprocess.run([
            "dotnet", THERMO_PARSER_DLL,
            "-i", raw_file,
            "-o", mzml_dir,
            "-f", "1", "-p", "-g"
        ], check=True)