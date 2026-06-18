import json
from typing import TYPE_CHECKING

import networkx as nx
import pandas as pd

from lib.molnet import get_annotated_molecular_network

if TYPE_CHECKING:
    from snakemake.iocontainers import snakemake

config = snakemake.params["config"]

feature_table_df = pd.read_csv(snakemake.input["feature_table"], low_memory=False)
mzmine_annotations_df = pd.read_csv(
    snakemake.input["mzmine_annotations"], low_memory=False
)
sirius_formula_identifications_df = pd.read_csv(
    snakemake.input["sirius_formula_identifications"],
    delimiter="\t",
    dtype={"alignedFeatureId": "Int64"},
    low_memory=False,
)
sirius_structure_identifications_df = pd.read_csv(
    snakemake.input["sirius_structure_identifications"],
    delimiter="\t",
    dtype={"alignedFeatureId": "Int64"},
    low_memory=False,
)
sirius_denovo_structure_identifications_df = pd.read_csv(
    snakemake.input["sirius_denovo_structure_identifications"],
    delimiter="\t",
    dtype={"alignedFeatureId": "Int64"},
    low_memory=False,
)


def merge_structure_annotations():
    spectral = mzmine_annotations_df.rename(
        columns={
            "compound_name": "compound_name",
            "smiles": "smiles",
            "mol_formula": "molecularFormula",
            "score": "score",
        }
    ).assign(annotation_type="spectral_match")[
        [
            "id",
            "annotation_type",
            "compound_name",
            "smiles",
            "molecularFormula",
            "score",
        ]
    ]
    db = sirius_structure_identifications_df.rename(
        columns={
            "mappingFeatureId": "id",
            "alignedFeatureId": "sirius_id",
            "name": "compound_name",
            "smiles": "smiles",
            "molecularFormula": "molecularFormula",
            "ConfidenceScoreExact": "score",
        }
    ).assign(annotation_type="structure_database")[
        [
            "id",
            "sirius_id",
            "annotation_type",
            "compound_name",
            "smiles",
            "molecularFormula",
            "score",
        ]
    ]
    denovo = sirius_denovo_structure_identifications_df.rename(
        columns={
            "mappingFeatureId": "id",
            "alignedFeatureId": "sirius_id",
            "name": "compound_name",
            "smiles": "smiles",
            "molecularFormula": "molecularFormula",
            "ModelScore": "score",
        }
    ).assign(annotation_type="denovo")[
        [
            "id",
            "sirius_id",
            "annotation_type",
            "compound_name",
            "smiles",
            "molecularFormula",
            "score",
        ]
    ]

    # Merge sirius annotations
    sirius_all = pd.concat([db, denovo])

    # Add sirius_id to spectral annotations by creating lookup
    sirius_lookup = pd.concat([db, denovo])[["id", "sirius_id"]].drop_duplicates("id")
    spectral = spectral.merge(sirius_lookup, on="id", how="left")

    # Combine dataframes
    combined = pd.concat(
        [spectral, sirius_all],
        ignore_index=True,
    )[
        [
            "id",
            "sirius_id",
            "annotation_type",
            "compound_name",
            "smiles",
            "molecularFormula",
            "score",
        ]
    ]

    return combined


def filter_structure_annotations(annotations_df: pd.DataFrame):
    # Remove below cutoff
    spectral_mask = ~(
        (annotations_df["annotation_type"] == "spectral_match")
        & (
            annotations_df["score"]
            < config.get("spectral_library_match_score_cutoff", 0.8)
        )
    )

    structure_mask = ~(
        (annotations_df["annotation_type"] == "structure_database")
        & (
            annotations_df["score"]
            < config.get("structure_database_confidence_cutoff", 0.8)
        )
    )

    denovo_mask = ~(
        (annotations_df["annotation_type"] == "denovo")
        & (annotations_df["score"] < config.get("msnovelist_score_cutoff", -3))
    )

    annotations_df = annotations_df.loc[
        spectral_mask & structure_mask & denovo_mask
    ].copy()

    priority = {"spectral_match": 1, "structure_database": 2, "denovo": 3}
    annotations_df["priority"] = annotations_df["annotation_type"].map(priority)

    # Remove duplicates
    annotations_df = annotations_df.sort_values(
        by=["id", "priority", "score"],
        ascending=[True, True, False],
    )
    annotations_df = annotations_df.drop_duplicates(subset=["id"], keep="first")
    annotations_df = annotations_df.drop(columns=["priority"])
    annotations_df = annotations_df.sort_values(
        by=["id"],
    )

    return annotations_df


def get_formula_annotations():
    formula = sirius_structure_identifications_df.rename(
        columns={
            "mappingFeatureId": "id",
            "alignedFeatureId": "sirius_id",
            "molecularFormula": "molecularFormula",
            "SiriusScoreNormalized": "score",
        }
    ).assign(annotation_type="structure_database")[
        [
            "id",
            "sirius_id",
            "molecularFormula",
            "score",
        ]
    ]
    return formula


def filter_formula_annotations(annotations_df: pd.DataFrame):
    # Remove below cutoff
    formula_mask = ~(
        annotations_df["score"] < config.get("formula_identification_score_cutoff", 0.8)
    )

    annotations_df = annotations_df.loc[formula_mask].copy()

    return annotations_df


def get_number_of_spectral_matches(annotations_df: pd.DataFrame):
    return len(annotations_df[annotations_df["annotation_type"] == "spectral_match"])


def get_number_of_structure_database_matches(annotations_df: pd.DataFrame):
    return len(
        annotations_df[annotations_df["annotation_type"] == "structure_database"]
    )


def get_number_of_denovo_predictions(annotations_df: pd.DataFrame):
    return len(annotations_df[annotations_df["annotation_type"] == "denovo"])


def get_number_of_formula_predictions(annotations_df: pd.DataFrame):
    return len(annotations_df)


# Merge and filter structure annotations
structure_df = merge_structure_annotations()
structure_df = filter_structure_annotations(structure_df)

# Save combined structure annotations
structure_df.to_csv(snakemake.output["structure_annotations"], index=False)

# Get formula annotations
formula_df = get_formula_annotations()
formula_df = filter_formula_annotations(formula_df)

# Save combined structure annotations
formula_df.to_csv(snakemake.output["formula_annotations"], index=False)

# Save annotated molecular network
similarity_measures = ["cosine", "modcosine", "spec2vec", "ms2deepscore"]
for similarity_measure in similarity_measures:
    # Load graphml file
    molnet = nx.read_graphml(snakemake.input["graphml_" + similarity_measure])
    # Annotate network
    molnet_annotated = get_annotated_molecular_network(
        molnet,
        structure_df,
        formula_df,
    )
    nx.write_graphml(
        molnet_annotated, snakemake.output["molnet_annotated_" + similarity_measure]
    )

## Stats

stats = {
    "# Formula predictions": get_number_of_formula_predictions(formula_df),
    "# Spectral library matches": get_number_of_spectral_matches(structure_df),
    "# Structure database matches": get_number_of_structure_database_matches(
        structure_df
    ),
    "# De novo predictions": get_number_of_denovo_predictions(structure_df),
}

with open(snakemake.output["stats"], "w") as f:
    json.dump(stats, f, indent=2)
