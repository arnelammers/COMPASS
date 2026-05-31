from pathlib import Path

snakemake = snakemake  # type: ignore

# Get snakemake parameters
output_mzbatch = Path(snakemake.output["mzbatch"])

# Get template
template_file = Path("resources/templates/" + snakemake.params.settings["template"] + ".mzbatch")

# Read template
xml = template_file.read_text()

# 1. Put input files in batch file
input_files = "\n\t\t\t".join(
    [f"<file>{str(Path(f).resolve())}</file>" for f in snakemake.input.input_files]
)
xml = xml.replace("{input_files}", input_files)

# 2. Put metadata file in batch file
xml = xml.replace("{metadata_file}", str(Path(snakemake.input["metadata_file"]).resolve()))

# 3. Put output files in batch file
output_dir = output_mzbatch.resolve().parent 
xml = xml.replace("{output_feature_table}", str(output_dir / "feature_table.csv"))
xml = xml.replace("{output_feature_table_before_subtraction}", str(output_dir / "feature_table_before_subtraction.csv"))
xml = xml.replace("{output_annotations}", str(output_dir / "annotations.csv"))
xml = xml.replace("{output_export_sirius}", str(output_dir / "export_sirius.mgf"))

# 4. Put other parameters in batch file
xml = xml.replace("{rt_range_min}", str(snakemake.params.settings["retention_time_range"][0]))
xml = xml.replace("{rt_range_max}", str(snakemake.params.settings["retention_time_range"][1]))
xml = xml.replace("{minimum_feature_height}", str(int(float(snakemake.params.settings["minimum_feature_height"]))))
xml = xml.replace("{approximate_feature_fwhm}", str(snakemake.params.settings["approximate_feature_fwhm"]))
xml = xml.replace("{blank_subtraction_min_blank_presence}", str(snakemake.params.settings["blank_subtraction"]["min_blank_presence"]))
xml = xml.replace("{blank_subtraction_fold_change_threshold}", str(snakemake.params.settings["blank_subtraction"]["fold_change_threshold"]))

# 5. Put spectral library files in batch file
spectral_library_files = "\n\t\t\t".join(
    [f"<file>{str(Path('resources/spectral_libraries/' + f).resolve())}</file>" for f in snakemake.params.settings["spectral_library_files"]]
)
xml = xml.replace("{spectral_library_files}", spectral_library_files)

# Write batch file
with open(output_mzbatch, "w") as f:
    f.write(xml)
