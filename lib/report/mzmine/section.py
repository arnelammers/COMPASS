from typing import TypedDict

import pandas as pd


class MzmineSectionInput(TypedDict):
    feature_table: str
    feature_table_before_subtraction: str
    annotations: str
    export_sirius: str
    metadata: str


class MzmineSectionOutput(TypedDict):
    pca: str
    stats: str


class PcaConfig(TypedDict):
    samples_groupby: list[str]
    procedural_blanks_groupby: list[str]


class MzmineSectionConfig(TypedDict):
    pca: PcaConfig


class MzmineSection:
    def __init__(
        self,
        input: MzmineSectionInput,
        output: MzmineSectionOutput,
        config: MzmineSectionConfig,
    ):
        """
        Initializes the MZmine section"""
        self.input = input
        self.output = output
        self.config = config

        self.feature_table_df = pd.read_csv(input["feature_table"])

        self.feature_table_before_subtraction_df = pd.read_csv(
            input["feature_table_before_subtraction"]
        )

        self.metadata_df = pd.read_csv(input["metadata"])
