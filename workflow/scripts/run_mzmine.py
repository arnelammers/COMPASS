import sys
import subprocess

from pathlib import Path
from glob import glob

# Get snakemake parameters
dataset_dir = Path(snakemake.input["dataset_dir"])
metadata_file = Path(snakemake.input["metadata_file"])

output_mgf = Path(snakemake.output["mgf"])
output_csv = Path(snakemake.output["csv"])
output_mzbatch = Path(snakemake.output["mzbatch"])

# Get input files and template
input_files = glob(dataset_dir / "mzml" / "*")
template_file = Path("workflow/scripts/mzmine_batch_template.xml")

# Read template
xml = template_file.read_text()

# Build file list
file_entries = "\n".join(
    [f"<file>{str(Path(f).resolve())}</file>" for f in input_files]
)

# Replace placeholders
xml = xml.replace("{input_files}", file_entries)
xml = xml.replace("{metadata_file}", str(metadata_file.resolve()))
xml = xml.replace("{output_mgf}", str(output_mgf.resolve()))
xml = xml.replace("{output_csv}", str(output_csv.resolve()))

# Write batch file
with open(output_mzbatch, "w") as f:
    f.write(xml)

# Run MZmine
cmd = ["mzmine", "--batch", str(output_mzbatch.resolve())]
subprocess.run(cmd, check=True)