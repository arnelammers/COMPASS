import lib.helpers as helpers
from snakemake.utils import validate


# Load config file
configfile: "config/config.yaml"


validate(config, "config/schema.json")

# List of datasets from config.yaml
DATASETS = list(config["datasets"].keys())
SIRIUS_FILES = [
    "canopus_formula_summary.tsv",
    "canopus_structure_summary.tsv",
    "denovo_structure_identifications.tsv",
    "formula_identifications.tsv",
    "spectral_matches.tsv",
    "spectral_matches_analog.tsv",
    "structure_identifications.tsv",
]


wildcard_constraints:
    collection="[^/.]+",
    dataset="[^/]+",
    sample="[^/]+",


rule all:
    input:
        expand("results/{dataset}/sirius/fbmn/spectra.mgf", dataset=DATASETS),


rule convert_raw_to_mzml:
    input:
        raw="data/{dataset}/raw/{sample}.raw",
    output:
        mzml="data/{dataset}/mzml/{sample}.mzML.gz",
    log:
        "logs/thermo_parser/{dataset}/{sample}.log",
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
            sample=helpers.get_samples(wildcards.dataset),
        ),
        metadata_file="data/{dataset}/metadata.csv",
        spectral_library_files=lambda wc: helpers.get_spectral_library_files(
            config, wc.dataset
        ),
    output:
        mzbatch="results/{dataset}/mzmine/mzmine_config.mzbatch",
    params:
        settings=lambda wildcards: helpers.get_mzmine_params(config, wildcards),
    script:
        "scripts/generate_mzmine_config.py"


rule download_spectral_library_file:
    output:
        "resources/spectral_libraries/{collection}/{filename}",
    params:
        zenodo_id=lambda wc: config["spectral_libraries"][wc.collection]["zenodo_id"],
        url=lambda wc: (
            f"https://zenodo.org/records/"
            f"{config['spectral_libraries'][wc.collection]['zenodo_id']}"
            f"/files/{wc.filename}?download=1"
        ),
    shell:
        """
        mkdir -p resources/spectral_libraries/{wildcards.collection}

        if [ ! -f {output} ]; then
            curl -L "{params.url}" -o {output}
        fi
        """


rule run_mzmine:
    input:
        dataset_dir="data/{dataset}/mzml",
        mzbatch="results/{dataset}/mzmine/mzmine_config.mzbatch",
    output:
        feature_table="results/{dataset}/mzmine/feature_table.csv",
        feature_table_before_subtraction="results/{dataset}/mzmine/feature_table_before_subtraction.csv",
        annotations="results/{dataset}/mzmine/annotations.csv",
        export_sirius="results/{dataset}/mzmine/export_sirius.mgf",
    log:
        "logs/mzmine/{dataset}.log",
    resources:
        mem_mb=12000,
    shell:
        """
        export _JAVA_OPTIONS="-Xmx6g"
        mzmine -b {input.mzbatch} >{log} 2>&1
        """


rule run_sirius:
    input:
        mgf="results/{dataset}/mzmine/export_sirius.mgf",
    output:
        project="results/{dataset}/sirius/project.sirius",
    log:
        "logs/sirius/{dataset}.log",
    shell:
        """
        sirius --input {input.mgf} --project {output.project} --mzmax=800 formulas -p orbitrap fingerprints classes structures denovo-structures >{log} 2>&1
        """


rule sirius_export_summaries:
    input:
        project="results/{dataset}/sirius/project.sirius",
    output:
        expand(
            "results/{{dataset}}/sirius/summaries/{file}",
            file=SIRIUS_FILES,
        ),
    log:
        "logs/sirius/{dataset}.export_summaries.log",
    shell:
        """
        sirius --project {input.project} summaries -o results/{wildcards.dataset}/sirius/summaries >{log} 2>&1
        """


rule sirius_export_fbmn:
    input:
        project="results/{dataset}/sirius/project.sirius",
    output:
        mgf="results/{dataset}/sirius/fbmn/spectra.mgf",
    log:
        "logs/sirius/{dataset}.export_fbmn.log",
    shell:
        """
        sirius --project {input.project} mgf-export --merge-ms2 -o {output.mgf} >{log} 2>&1
        """
