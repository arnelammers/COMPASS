from typing import TYPE_CHECKING

import pandas as pd

if TYPE_CHECKING:
    from .section import MzmineSection


class MzmineStats:
    def __init__(
        self,
        section: "MzmineSection",
    ):
        self.output = section.output["stats"]
        self.feature_table_df = section.feature_table_df
        self.feature_table_before_subtraction_df = (
            section.feature_table_before_subtraction_df
        )

        self._get_stats()

    def _get_stats(self):
        self.stats_df = pd.DataFrame(
            {
                "Statistic": [
                    "# Features before subtraction",
                    "# Features after subtraction",
                ],
                "Value": [
                    self.get_number_of_features_before_subtraction(),
                    self.get_number_of_features(),
                ],
            }
        )

    def get_number_of_features(self):
        return len(self.feature_table_df)

    def get_number_of_features_before_subtraction(self):
        return len(self.feature_table_before_subtraction_df)

    def save_to_file(self):
        self.stats_df.style.hide(axis="index").to_html(self.output)
