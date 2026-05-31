import sys
import subprocess

from pathlib import Path
from glob import glob

# Get current dataset
current_dataset = snakemake.wildcards.dataset

# Access config for this specific dataset
dataset_config = snakemake.config["datasets"][current_dataset]

# Get snakemake parameters
dataset_dir = Path(snakemake.input["dataset_dir"])
metadata_file = Path(snakemake.input["metadata_file"])
output_mzbatch = Path(snakemake.output["mzbatch"])

# Get input files and template
input_files = glob(dataset_dir / "*")
template_file = Path("resources/templates/dda_orbitrap.mzbatch")

# Read template
xml = template_file.read_text()

# 1. Put input files in batch file

# Build file list
file_entries = "\n".join(
    [f"<file>{str(Path(f).resolve())}</file>" for f in input_files]
)
xml = xml.replace("{input_files}", file_entries)

# 2. Put metadata file in batch file
xml = xml.replace("{metadata_file}", str(metadata_file.resolve()))

# 3. Put output files in batch file
output_dir = Path("results") / current_dataset / "mzmine"
xml = xml.replace("{output_feature_table}", str(output_dir / "feature_table.csv"))
xml = xml.replace("{output_feature_table_before_subtraction}", str(output_dir / "feature_table_before_subtraction.csv"))
xml = xml.replace("{output_annotations}", str(output_dir / "annotations.csv"))
xml = xml.replace("{output_export_sirius}", str(output_dir / "export_sirius.mgf"))

# Write batch file
with open(output_mzbatch, "w") as f:
    f.write(xml)

# Run MZmine
cmd = ["mzmine", "--batch", str(output_mzbatch.resolve())]
subprocess.run(cmd, check=True)