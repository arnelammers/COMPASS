import sys
import subprocess

from pathlib import Path
from glob import glob

snakemake = snakemake  # type: ignore

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
template_file = Path("resources/templates/" + dataset_config.mzmine.template + ".mzbatch")

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

# 4. Put other parameters in batch file
xml = xml.replace("{rt_range_min}", str(dataset_config.mzmine.retention_time_range[0]))
xml = xml.replace("{rt_range_max}", str(dataset_config.mzmine.retention_time_range[1]))
xml = xml.replace("{minimum_feature_height}", str(dataset_config.mzmine.minimum_feature_height))
xml = xml.replace("{approximate_feature_fwhm}", str(dataset_config.mzmine.approximate_feature_fwhm))
xml = xml.replace("{blank_subtraction_min_blank_presence}", str(dataset_config.mzmine.blank_subtraction.min_blank_presence))
xml = xml.replace("{blank_subtraction_fold_change_threshold}", str(dataset_config.mzmine.blank_subtraction.fold_change_threshold))

# Write batch file
with open(output_mzbatch, "w") as f:
    f.write(xml)
