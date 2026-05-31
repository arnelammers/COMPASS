import subprocess
import argparse
from glob import glob
from pathlib import Path

# Location of ThermoRawFileParser DLL
THERMO_PARSER_DLL = "/home/mambauser/tools/ThermoRawFileParser/ThermoRawFileParser.dll"

snakemake = snakemake  # type: ignore

# Create mzml directory
mzml_dir = Path(snakemake.output["mzml_dir"])
mzml_dir.mkdir(exist_ok=True, parents=True)

# Loop directly over the files to convert them to mzML using the ThermoRawFileParser
for raw_file in snakemake.input["raw_files"]:
    print(f"Converting {raw_file} → {mzml_dir}")
    subprocess.run([
        "dotnet", THERMO_PARSER_DLL,
        "-i", raw_file,
        "-o", str(mzml_dir),
        "-f", "1", "-p", "-g"
    ], check=True)

