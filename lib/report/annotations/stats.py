from typing import TYPE_CHECKING

import pandas as pd

if TYPE_CHECKING:
    from .section import MzmineSection


class AnnotationsStats:
    def __init__(
        self,
        section: "MzmineSection",
    ):
        self.output = section.output["stats"]
        self.smiles_combined_df = pd.read_csv(section.output["smiles_combined"])

        self._get_stats()

    def _get_stats(self):
        self.stats_df = pd.DataFrame(
            {
                "Statistic": [
                    "# Spectral library matches",
                    "# Structure database matches",
                    "# De novo predictions",
                ],
                "Value": [
                    self.get_number_of_spectral_matches(),
                    self.get_number_of_structure_database_matches(),
                    self.get_number_of_denovo_predictions(),
                ],
            }
        )

    def get_number_of_spectral_matches(self):
        return len(
            self.smiles_combined_df[
                self.smiles_combined_df["annotation_type"] == "spectral_match"
            ]
        )

    def get_number_of_structure_database_matches(self):
        return len(
            self.smiles_combined_df[
                self.smiles_combined_df["annotation_type"] == "structure_database"
            ]
        )

    def get_number_of_denovo_predictions(self):
        return len(
            self.smiles_combined_df[
                self.smiles_combined_df["annotation_type"] == "denovo"
            ]
        )

    def save_to_file(self):
        self.stats_df.style.hide(axis="index").to_html(self.output)
