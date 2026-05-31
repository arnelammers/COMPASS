# Load config file 
configfile: "config/config.yaml"

# List of datasets from config.yaml
DATASETS = list(config["datasets"].keys())

rule all:
    input:
        expand("results/{dataset}/mzmine/mzmine_config.mzbatch", dataset=DATASETS)

rule convert_to_mzml:
    input:
        raw_files = lambda wildcards: [
            str(f) for f in Path(f"data/{wildcards.dataset}/raw").glob("*.raw")
        ]
    output:
        mzml_dir=directory("data/{dataset}/mzml")
    script:
        "scripts/convert_to_mzml.py"
rule generate_mzmine_config:
    input:
        dataset_dir="data/{dataset}/mzml",
        metadata_file="data/{dataset}/metadata.csv"
    output:
        mzbatch="results/{dataset}/mzmine/mzmine_config.mzbatch"
    script:
        "scripts/generate_mzmine_config.py"