from typing import TypedDict

import pandas as pd


class AnnotationsSectionInput(TypedDict):
    feature_table: str
    mzmine_annotations: str
    sirius_structure_identifications: str
    sirius_denovo_structure_identifications: str


class AnnotationsSectionOutput(TypedDict):
    table: str
    stats: str


class AnnotationsSectionConfig(TypedDict):
    spectral_library_match_score_cutoff: float
    structure_database_confidence_cutoff: float
    msnovelist_score_cutoff: float


class AnnotationsSection:
    def __init__(
        self,
        input: AnnotationsSectionInput,
        output: AnnotationsSectionOutput,
        config: AnnotationsSectionConfig,
    ):
        """
        Initializes the annotatiomns section"""
        self.input = input
        self.output = output
        self.config = config

        self.feature_table_df = pd.read_csv(input["feature_table"])
        self.mzmine_annotations_df = pd.read_csv(input["mzmine_annotations"])
        self.sirius_structure_identifications_df = pd.read_csv(
            input["sirius_structure_identifications"],
            delimiter="\t",
            dtype={"compoundId": "Int64"},
        )
        self.sirius_denovo_structure_identifications_df = pd.read_csv(
            input["sirius_denovo_structure_identifications"],
            delimiter="\t",
            dtype={"compoundId": "Int64"},
        )
