# Load config file 
configfile: "config/config.yaml"

wildcard_constraints:
    collection="[^/.]+",
    dataset="[^/]+",
    sample="[^/]+"

# List of datasets from config.yaml
DATASETS = list(config["datasets"].keys())

import lib.helpers as helpers

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
        input_files=lambda wildcards: expand(
            "data/{dataset}/mzml/{sample}.mzML.gz",
            dataset=wildcards.dataset,
            sample=helpers.get_samples(wildcards.dataset)
        ),
        metadata_file="data/{dataset}/metadata.csv",
        spectral_library_files=lambda wc:
            helpers.get_spectral_library_files(config, wc.dataset)
    output:
        mzbatch="results/{dataset}/mzmine/mzmine_config.mzbatch"
    params:
        settings=lambda wildcards: helpers.get_mzmine_params(config, wildcards)
    script:
        "scripts/generate_mzmine_config.py"

rule download_spectral_library_file:
    output:
        "resources/spectral_libraries/{collection}/{filename}"
    params:
        zenodo_id=lambda wc: config["spectral_libraries"][wc.collection]["zenodo_id"],
        url=lambda wc: (
            f"https://zenodo.org/records/"
            f"{config['spectral_libraries'][wc.collection]['zenodo_id']}"
            f"/files/{wc.filename}?download=1"
        )
    shell:
        """
        mkdir -p resources/spectral_libraries/{wildcards.collection}

        if [ ! -f {output} ]; then
            curl -L "{params.url}" -o {output}
        fi
        """