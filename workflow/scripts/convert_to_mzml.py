import os
import subprocess
import argparse
from glob import glob

THERMO_PARSER_DLL = "/home/mambauser/tools/ThermoRawFileParser-v.2.0.0-dev-linux/ThermoRawFileParser.dll"

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-dir", required=True, help="Path to dataset folder")
    args = parser.parse_args()

    mzml_dir = os.path.join(args.dataset_dir, "mzml")
    raw_dir = os.path.join(args.dataset_dir, "raw")

    # If mzml folder exists, skip conversion
    if os.path.exists(mzml_dir):
        print(f"mzML folder already exists in {args.dataset_dir}, skipping conversion")
        return

    # Otherwise, convert all raw files
    raw_files = glob(os.path.join(raw_dir, "*.raw"))
    
    # Create mzml directory
    os.makedirs(mzml_dir, exist_ok=True)

    for raw_file in raw_files:
        print(f"Converting {raw_file} → {mzml_dir}")
        subprocess.run([
            "dotnet", THERMO_PARSER_DLL,
            "-i", raw_file,
            "-o", mzml_dir,
            "-f", "1", "-p", "-g"
        ], check=True)

if __name__ == "__main__":
    main()