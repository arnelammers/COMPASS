# Load config file 
configfile: "config.yaml"

# List of datasets from config.yaml
DATASETS = list(config["datasets"].keys())

rule all:
    input:
        expand("results/{dataset}/mzmine/output.mgf", dataset=DATASETS),
        expand("results/{dataset}/mzmine/output.csv", dataset=DATASETS),
        expand("results/{dataset}/mzmine/mzmine_config.mzbatch", dataset=DATASETS)

rule convert_to_mzml:
    input:
        dataset_dir="data/{dataset}"
    output:
        mzml_dir="data/{dataset}/mzml"
    script:
        "workflow/scripts/convert_to_mzml.py"
rule mzmine:
    input:
        dataset_dir="data/{dataset}"
        metadata_file="data/{dataset}/metadata.csv"
    output:
        mgf="results/{dataset}/mzmine/output.mgf",
        csv="results/{dataset}/mzmine/output.csv",
        mzbatch="results/{dataset}/mzmine/mzmine_config.mzbatch"
    script:
        "workflow/scripts/run_mzmine.py"