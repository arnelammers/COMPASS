import json
from typing import TYPE_CHECKING

import pandas as pd

if TYPE_CHECKING:
    from snakemake.iocontainers import snakemake

config = snakemake.config["datasets"][snakemake.wildcards.dataset]["report"][
    "annotations"
]

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
        & (annotations_df["score"] < config["spectral_library_match_score_cutoff"])
    )

    structure_mask = ~(
        (annotations_df["annotation_type"] == "structure_database")
        & (annotations_df["score"] < config["structure_database_confidence_cutoff"])
    )

    denovo_mask = ~(
        (annotations_df["annotation_type"] == "denovo")
        & (annotations_df["score"] < config["msnovelist_score_cutoff"])
    )

    annotations_df = annotations_df.loc[
        spectral_mask & structure_mask & denovo_mask
    ].copy()

    priority = {"spectral_match": 1, "structure_database": 2, "denovo": 3}
    annotations_df["priority"] = annotations_df["annotation_type"].map(priority)

    # Remove duplicates
    annotations_df = annotations_df.sort_values(
        by=["smiles", "priority", "score"],
        ascending=[True, True, False],
    )
    annotations_df = annotations_df.drop_duplicates(subset=["smiles"], keep="first")
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
        annotations_df["score"] < config["formula_identification_score_cutoff"]
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
structure_combined_df = merge_structure_annotations()
structure_combined_df = filter_structure_annotations(structure_combined_df)

# Save combined structure annotations
structure_combined_df.to_csv(
    snakemake.output["structure_annotations_combined"], index=False
)

# Get formula annotations
formula_df = get_formula_annotations()
formula_df = filter_formula_annotations(formula_df)

# Save combined structure annotations
formula_df.to_csv(snakemake.output["formula_annotations"], index=False)

## Stats

stats = {
    "# Formula predictions": get_number_of_formula_predictions(formula_df),
    "# Spectral library matches": get_number_of_spectral_matches(structure_combined_df),
    "# Structure database matches": get_number_of_structure_database_matches(
        structure_combined_df
    ),
    "# De novo predictions": get_number_of_denovo_predictions(structure_combined_df),
}

with open(snakemake.output["stats"], "w") as f:
    json.dump(stats, f, indent=2)
