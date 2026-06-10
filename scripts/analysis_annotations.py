import json
from typing import TYPE_CHECKING

import pandas as pd

if TYPE_CHECKING:
    from snakemake.script import snakemake

config = snakemake.config["datasets"][snakemake.wildcards.dataset]["report"][
    "annotations"
]

feature_table_df = pd.read_csv(snakemake.input["feature_table"], low_memory=False)
mzmine_annotations_df = pd.read_csv(
    snakemake.input["mzmine_annotations"], low_memory=False
)
sirius_structure_identifications_df = pd.read_csv(
    snakemake.input["sirius_structure_identifications"],
    delimiter="\t",
    dtype={"compoundId": "Int64"},
    low_memory=False,
)
sirius_denovo_structure_identifications_df = pd.read_csv(
    snakemake.input["sirius_denovo_structure_identifications"],
    delimiter="\t",
    dtype={"compoundId": "Int64"},
    low_memory=False,
)


def merge_annotations():
    spectral = mzmine_annotations_df.rename(
        columns={
            "compound_name": "compound_name",
            "smiles": "smiles",
            "score": "score",
        }
    ).assign(annotation_type="spectral_match")[
        ["id", "annotation_type", "compound_name", "smiles", "score"]
    ]
    db = sirius_structure_identifications_df.rename(
        columns={
            "mappingFeatureId": "id",
            "compoundId": "sirius_id",
            "name": "compound_name",
            "smiles": "smiles",
            "ConfidenceScoreExact": "score",
        }
    ).assign(annotation_type="structure_database")[
        ["id", "sirius_id", "annotation_type", "compound_name", "smiles", "score"]
    ]
    denovo = sirius_denovo_structure_identifications_df.rename(
        columns={
            "mappingFeatureId": "id",
            "compoundId": "sirius_id",
            "name": "compound_name",
            "smiles": "smiles",
            "ModelScore": "score",
        }
    ).assign(annotation_type="denovo")[
        ["id", "sirius_id", "annotation_type", "compound_name", "smiles", "score"]
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
    )[["id", "sirius_id", "annotation_type", "compound_name", "smiles", "score"]]

    return combined


def filter_annotations(annotations_df: pd.DataFrame):
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


def get_number_of_spectral_matches(annotations_df: pd.DataFrame):
    return len(annotations_df[annotations_df["annotation_type"] == "spectral_match"])


def get_number_of_structure_database_matches(annotations_df: pd.DataFrame):
    return len(
        annotations_df[annotations_df["annotation_type"] == "structure_database"]
    )


def get_number_of_denovo_predictions(annotations_df: pd.DataFrame):
    return len(annotations_df[annotations_df["annotation_type"] == "denovo"])


# Merge and filter annotations
combined_df = merge_annotations()
combined_df = filter_annotations(combined_df)

# Save combined annotations
combined_df.to_csv(snakemake.output["smiles_combined"], index=False)

## Stats

stats = {
    "# Spectral library matches": get_number_of_spectral_matches(combined_df),
    "# Structure database matches": get_number_of_structure_database_matches(
        combined_df
    ),
    "# De novo predictions": get_number_of_denovo_predictions(combined_df),
}

with open(snakemake.output["stats"], "w") as f:
    json.dump(stats, f, indent=2)
