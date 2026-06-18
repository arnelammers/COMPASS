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
        expand("results/{dataset}/analysis/features/pca.png", dataset=DATASETS),
        expand("results/{dataset}/analysis/features/stats.json", dataset=DATASETS),
        expand(
            "results/{dataset}/analysis/features/da.csv",
            dataset=DATASETS,
        ),
        expand(
            "results/{dataset}/analysis/annotations/structure_annotations.csv",
            dataset=DATASETS,
        ),
        expand(
            "results/{dataset}/analysis/annotations/formula_annotations.csv",
            dataset=DATASETS,
        ),
        expand("results/{dataset}/analysis/annotations/stats.json", dataset=DATASETS),
        expand(
            "results/{dataset}/analysis/annotations/molnet_annotated_cosine.graphml",
            dataset=DATASETS,
        ),
        expand(
            "results/{dataset}/analysis/annotations/molnet_annotated_modcosine.graphml",
            dataset=DATASETS,
        ),
        expand(
            "results/{dataset}/analysis/annotations/molnet_annotated_spec2vec.graphml",
            dataset=DATASETS,
        ),
        expand(
            "results/{dataset}/analysis/annotations/molnet_annotated_ms2deepscore.graphml",
            dataset=DATASETS,
        ),
        expand("results/{dataset}/analysis/bioactivity/signatures.h5", dataset=DATASETS),
        expand("results/{dataset}/analysis/bioactivity/tsne.png", dataset=DATASETS),
        expand(
            "results/{dataset}/analysis/bioactivity/query_neighbors.csv",
            dataset=DATASETS,
        ),
        expand(
            "results/{dataset}/analysis/bioactivity/structure_annotations_clustered.csv",
            dataset=DATASETS,
        ),
        expand(
            "results/{dataset}/analysis/bioactivity/clusters.csv",
            dataset=DATASETS,
        ),
        expand(
            "results/{dataset}/analysis/bioactivity/molnet_query_neighbors_cosine.graphml",
            dataset=DATASETS,
        ),
        expand(
            "results/{dataset}/analysis/bioactivity/molnet_query_neighbors_modcosine.graphml",
            dataset=DATASETS,
        ),
        expand(
            "results/{dataset}/analysis/bioactivity/molnet_query_neighbors_spec2vec.graphml",
            dataset=DATASETS,
        ),
        expand(
            "results/{dataset}/analysis/bioactivity/molnet_query_neighbors_ms2deepscore.graphml",
            dataset=DATASETS,
        ),


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

        dotnet /home/bio/tools/ThermoRawFileParser/ThermoRawFileParser.dll \
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
        curl -fL "{params.url}" -o {output}
        """


rule run_mzmine:
    input:
        mzmls=lambda wildcards: expand(
            "data/{dataset}/mzml/{sample}.mzML.gz",
            dataset=wildcards.dataset,
            sample=helpers.get_samples(wildcards.dataset),
        ),
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
        mzmine -b {input.mzbatch} 2>&1 | tee {log}
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
        sirius --input {input.mgf} --project {output.project} --mzmax=800 formulas -p orbitrap fingerprints classes structures denovo-structures 2>&1 | tee {log}
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
        sirius --project {input.project} summaries -o results/{wildcards.dataset}/sirius/summaries 2>&1 | tee {log}
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
        sirius --project {input.project} mgf-export --merge-ms2 -o {output.mgf} 2>&1 | tee {log}
        """


rule download_ms2deepscore_model:
    output:
        "resources/models/ms2deepscore/ms2deepscore_model.pt",
    shell:
        """
        curl -fL "https://zenodo.org/records/17826815/files/ms2deepscore_model.pt?download=1" -o {output}
        """


rule download_spec2vec_model:
    output:
        "resources/models/spec2vec/spec2vec_AllPositive_ratio05_filtered_201101_iter_15.model",
    shell:
        """
        curl -fL "https://zenodo.org/api/records/4173596/files-archive" -o resources/models/spec2vec.zip
        unzip resources/models/spec2vec.zip -d resources/models/spec2vec
        rm resources/models/spec2vec.zip
        """


rule train_spec2vec_model:
    input:
        mgf="results/{dataset}/sirius/fbmn/spectra.mgf",
    output:
        model="results/{dataset}/spec2vec/spec2vec.model",
    shell:
        "/opt/conda/envs/specreboot/bin/python scripts/train_spec2vec_model.py --input {input.mgf} --output {output.model}"


rule run_specreboot:
    input:
        mgf="results/{dataset}/sirius/fbmn/spectra.mgf",
        spec2vec_model="results/{dataset}/spec2vec/spec2vec.model",
        msdeepscore_model="resources/models/ms2deepscore/ms2deepscore_model.pt",
    output:
        graphml_cosine="results/{dataset}/specreboot/Reboot_bootstrap_threshold_Cosine.graphml",
        graphml_modcosine="results/{dataset}/specreboot/Reboot_bootstrap_threshold_ModCosine.graphml",
        graphml_spec2vec="results/{dataset}/specreboot/Reboot_bootstrap_threshold_Spec2Vec.graphml",
        graphml_ms2deepscore="results/{dataset}/specreboot/Reboot_bootstrap_threshold_MS2DeepScore.graphml",
    log:
        "logs/specreboot/{dataset}.log",
    shell:
        """
        /opt/conda/envs/specreboot/bin/specreboot matchms \
            --mgf {input.mgf} \
            --similarities all \
            --ms2dp-model {input.msdeepscore_model} \
            --spec2vec-model {input.spec2vec_model} \
            --outdir "results/{wildcards.dataset}/specreboot" \
            --prefix "Reboot" \
            --B 30 2>&1 | tee {log}
        """


rule analysis_features:
    input:
        feature_table="results/{dataset}/mzmine/feature_table.csv",
        feature_table_before_subtraction="results/{dataset}/mzmine/feature_table_before_subtraction.csv",
        annotations="results/{dataset}/mzmine/annotations.csv",
        export_sirius="results/{dataset}/mzmine/export_sirius.mgf",
        metadata="data/{dataset}/metadata.csv",
    output:
        pca="results/{dataset}/analysis/features/pca.png",
        stats="results/{dataset}/analysis/features/stats.json",
        da="results/{dataset}/analysis/features/da.csv",
    params:
        config=lambda wc: config["datasets"][wc.dataset]["analysis"]["features"],
    script:
        "scripts/analysis_features.py"


rule analysis_annotations:
    input:
        feature_table="results/{dataset}/mzmine/feature_table.csv",
        mzmine_annotations="results/{dataset}/mzmine/annotations.csv",
        sirius_formula_identifications="results/{dataset}/sirius/summaries/formula_identifications.tsv",
        sirius_structure_identifications="results/{dataset}/sirius/summaries/structure_identifications.tsv",
        sirius_denovo_structure_identifications="results/{dataset}/sirius/summaries/denovo_structure_identifications.tsv",
        graphml_cosine="results/{dataset}/specreboot/Reboot_bootstrap_threshold_Cosine.graphml",
        graphml_modcosine="results/{dataset}/specreboot/Reboot_bootstrap_threshold_ModCosine.graphml",
        graphml_spec2vec="results/{dataset}/specreboot/Reboot_bootstrap_threshold_Spec2Vec.graphml",
        graphml_ms2deepscore="results/{dataset}/specreboot/Reboot_bootstrap_threshold_MS2DeepScore.graphml",
    output:
        structure_annotations="results/{dataset}/analysis/annotations/structure_annotations.csv",
        formula_annotations="results/{dataset}/analysis/annotations/formula_annotations.csv",
        stats="results/{dataset}/analysis/annotations/stats.json",
        molnet_annotated_cosine="results/{dataset}/analysis/annotations/molnet_annotated_cosine.graphml",
        molnet_annotated_modcosine="results/{dataset}/analysis/annotations/molnet_annotated_modcosine.graphml",
        molnet_annotated_spec2vec="results/{dataset}/analysis/annotations/molnet_annotated_spec2vec.graphml",
        molnet_annotated_ms2deepscore="results/{dataset}/analysis/annotations/molnet_annotated_ms2deepscore.graphml",
    params:
        config=lambda wc: config["datasets"][wc.dataset]["analysis"]["annotations"],
    script:
        "scripts/analysis_annotations.py"


rule compute_signatures:
    input:
        structure_annotations="results/{dataset}/analysis/annotations/structure_annotations.csv",
    output:
        signatures="results/{dataset}/analysis/bioactivity/signatures.h5",
    conda:
        "signaturizer_env"
    params:
        config=lambda wc: config["datasets"][wc.dataset]["analysis"]["bioactivity"],
    script:
        "scripts/compute_signatures.py"


rule analysis_bioactivity:
    input:
        signatures="results/{dataset}/analysis/bioactivity/signatures.h5",
        structure_annotations="results/{dataset}/analysis/annotations/structure_annotations.csv",
        formula_annotations="results/{dataset}/analysis/annotations/formula_annotations.csv",
        graphml_cosine="results/{dataset}/specreboot/Reboot_bootstrap_threshold_Cosine.graphml",
        graphml_modcosine="results/{dataset}/specreboot/Reboot_bootstrap_threshold_ModCosine.graphml",
        graphml_spec2vec="results/{dataset}/specreboot/Reboot_bootstrap_threshold_Spec2Vec.graphml",
        graphml_ms2deepscore="results/{dataset}/specreboot/Reboot_bootstrap_threshold_MS2DeepScore.graphml",
    output:
        tsne="results/{dataset}/analysis/bioactivity/tsne.png",
        umap="results/{dataset}/analysis/bioactivity/umap.png",
        clusters="results/{dataset}/analysis/bioactivity/clusters.csv",
        query_neighbors="results/{dataset}/analysis/bioactivity/query_neighbors.csv",
        structure_annotations_clustered="results/{dataset}/analysis/bioactivity/structure_annotations_clustered.csv",
        molnet_query_neighbors_cosine="results/{dataset}/analysis/bioactivity/molnet_query_neighbors_cosine.graphml",
        molnet_query_neighbors_modcosine="results/{dataset}/analysis/bioactivity/molnet_query_neighbors_modcosine.graphml",
        molnet_query_neighbors_spec2vec="results/{dataset}/analysis/bioactivity/molnet_query_neighbors_spec2vec.graphml",
        molnet_query_neighbors_ms2deepscore="results/{dataset}/analysis/bioactivity/molnet_query_neighbors_ms2deepscore.graphml",
    params:
        config=lambda wc: config["datasets"][wc.dataset]["analysis"]["bioactivity"],
    script:
        "scripts/analysis_bioactivity.py"
