from typing import TYPE_CHECKING

import pandas as pd

if TYPE_CHECKING:
    from .section import MzmineSection


class AnnotationsSmilesCombined:
    def __init__(
        self,
        section: "MzmineSection",
    ):
        self.feature_table_df = section.feature_table_df
        self.mzmine_annotations_df = section.mzmine_annotations_df
        self.sirius_structure_identifications_df = (
            section.sirius_structure_identifications_df
        )
        self.sirius_denovo_structure_identifications_df = (
            section.sirius_denovo_structure_identifications_df
        )
        self.output = section.output["smiles_combined"]
        self.config = section.config

        self._merge_annotations()
        self._filter_annotations()

    def _merge_annotations(self):
        spectral = self.mzmine_annotations_df.rename(
            columns={
                "compound_name": "compound_name",
                "smiles": "smiles",
                "score": "score",
            }
        ).assign(annotation_type="spectral_match")[
            ["id", "annotation_type", "compound_name", "smiles", "score"]
        ]
        db = self.sirius_structure_identifications_df.rename(
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
        denovo = self.sirius_denovo_structure_identifications_df.rename(
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
        sirius_lookup = pd.concat([db, denovo])[["id", "sirius_id"]].drop_duplicates(
            "id"
        )
        spectral = spectral.merge(sirius_lookup, on="id", how="left")

        # Combine dataframes
        self.combined = pd.concat(
            [spectral, sirius_all],
            ignore_index=True,
        )[["id", "sirius_id", "annotation_type", "compound_name", "smiles", "score"]]

    def _filter_annotations(self):
        # Remove below cutoff
        self.combined = self.combined[
            ~(
                (self.combined["annotation_type"] == "spectral_library")
                & (
                    self.combined["score"]
                    < self.config["spectral_library_match_score_cutoff"]
                )
            )
        ]
        self.combined = self.combined[
            ~(
                (self.combined["annotation_type"] == "structure_database")
                & (
                    self.combined["score"]
                    < self.config["structure_database_confidence_cutoff"]
                )
            )
        ]
        self.combined = self.combined[
            ~(
                (self.combined["annotation_type"] == "denovo")
                & (self.combined["score"] < self.config["msnovelist_score_cutoff"])
            )
        ]

        priority = {"spectral_match": 1, "structure_database": 2, "denovo": 3}
        self.combined["priority"] = self.combined["annotation_type"].map(priority)

        # Remove duplicates
        self.combined = self.combined.sort_values(
            by=["smiles", "priority", "score"],
            ascending=[True, True, False],
        )
        self.combined = self.combined.drop_duplicates(subset=["smiles"], keep="first")
        self.combined = self.combined.drop(columns=["priority"])
        self.combined = self.combined.sort_values(
            by=["id"],
        )

    def save_to_file(self):
        self.combined.to_csv(self.output, index=False)
