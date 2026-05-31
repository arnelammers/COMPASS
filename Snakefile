# Load config file 
configfile: "config/config.yaml"

# List of datasets from config.yaml
DATASETS = list(config["datasets"].keys())

def get_mzmine_params(wildcards):
    """Returns the mzmine parameters for the given dataset."""
    return config["datasets"][wildcards.dataset]["mzmine"]

def get_samples(dataset):
    """Dynamically collects sample names ."""
    raw_samples = {
        p.stem
        for p in Path(f"data/{dataset}/raw").glob("*.raw")
    }

    mzml_samples = {
        p.stem
        for p in Path(f"data/{dataset}/mzml_raw").glob("*.mzML.gz")
    }

    return sorted(raw_samples | mzml_samples)

rule all:
    input:
        expand("results/{dataset}/mzmine/mzmine_config.mzbatch", dataset=DATASETS)

rule convert_raw_to_mzml:
    input:
        raw="data/{dataset}/raw/{sample}.raw"
    output:
        mzml="data/{dataset}/mzml/{sample}.mzML.gz"
    log:
        "logs/thermo_parser/{dataset}/{sample}.log"
    shell:
        """
        out_dir=$(dirname "{output.mzml}")
        mkdir -p "$out_dir"

        dotnet /home/mambauser/tools/ThermoRawFileParser/ThermoRawFileParser.dll \
            -i {input.raw} \
            -o "$out_dir" \
            -f 1 -p -g 2>&1 | tee {log}
        """

rule generate_mzmine_config:
    input:
        mzmls=lambda wildcards: expand(
            "data/{dataset}/mzml/{sample}.mzML.gz",
            dataset=wildcards.dataset,
            sample=get_samples(wildcards.dataset)
        ),
        metadata_file="data/{dataset}/metadata.csv"
    output:
        mzbatch="results/{dataset}/mzmine/mzmine_config.mzbatch"
    params:
        settings=get_mzmine_params
    script:
        "scripts/generate_mzmine_config.py"