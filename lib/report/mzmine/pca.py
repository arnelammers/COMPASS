from typing import TYPE_CHECKING

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

if TYPE_CHECKING:
    from .section import MzmineSection


class MzminePCA:
    def __init__(
        self,
        section: "MzmineSection",
    ):
        self.section = section
        self.df = section.feature_table
        self.metadata_df = section.metadata

        # Keep a list of expected filenames from metadata
        self.valid_filenames = set(self.metadata_df["filename"].tolist())

        # Extract the area dataframe during initialization
        self.area_df = self._extract_area_df()

        # Extract PCA dataframe
        self.pca, self.pca_df = self._extract_pca()

        # Generate PCA
        self._generate_pca()

    def _extract_area_df(self) -> pd.DataFrame:
        """Filters, cleans, and aligns the area columns with metadata."""

        # Identify all area columns
        area_cols = [
            col
            for col in self.df.columns
            if col.startswith("datafile:") and col.endswith(":area")
        ]

        # Slice the dataframe and immediately copy
        area_df = self.df[area_cols].copy()

        # Clean the column names cleanly using .rename()
        # Example: 'datafile:Sample_A.mzML:area' -> 'Sample_A.mzML'
        area_df = area_df.rename(
            columns=lambda x: x.replace("datafile:", "").replace(":area", "")
        )

        # Filter columns to only keep those present in metadata
        matched_cols = [col for col in area_df.columns if col in self.valid_filenames]

        return area_df[matched_cols]

    def _extract_pca(self) -> tuple[PCA, pd.DataFrame]:
        X = self.area_df.T

        # Fill NA
        X_filled = X.fillna(0)

        # Standardize the data
        X_scaled = StandardScaler().fit_transform(X_filled)

        # Run PCA
        pca = PCA(n_components=2)
        X_pca = pca.fit_transform(X_scaled)

        # Create a DataFrame for PCA results
        pca_df = pd.DataFrame(X_pca, columns=["PC1", "PC2"], index=X.index)

        # Merge PCA results with metadata
        pca_df = pca_df.merge(
            self.metadata_df, left_index=True, right_on="filename"
        ).set_index("filename")

        return pca, pca_df

    def _generate_pca(self):
        samples_groupby = self.section.config["pca"]["samples_groupby"]
        procedural_blanks_groupby = self.section.config["pca"][
            "procedural_blanks_groupby"
        ]

        # Map type to marker shapes
        type_markers = {
            "sample": "o",
            "instrumental_blank": "s",
            "procedural_blank": "^",
        }

        # Set figure size
        plt.figure(figsize=(10, 8))

        # --- Samples ---
        samples = self.pca_df[self.pca_df["type"] == "sample"].copy()

        # Set group by column and et unique combinations
        samples["groupby"] = samples[samples_groupby].astype(str).agg("_".join, axis=1)
        samples_unique_groupby = sorted(
            samples["groupby"].unique(), key=lambda s: s.split("_")
        )

        # Assign colors using palette
        samples_palette = sns.color_palette(
            "tab20", n_colors=len(samples_unique_groupby)
        )
        samples_color_mapping = dict(zip(samples_unique_groupby, samples_palette))

        # Plot samples
        for sample_groupby in samples_unique_groupby:
            subset = samples[samples["groupby"] == sample_groupby]
            plt.scatter(
                subset["PC1"],
                subset["PC2"],
                color=samples_color_mapping[sample_groupby],
                marker=type_markers["sample"],
                label=f"Sample: {sample_groupby}",
            )

        # --- Procedural blanks ---
        procedural_blanks = self.pca_df[
            self.pca_df["type"] == "procedural_blank"
        ].copy()

        # Set group by column and et unique combinations
        procedural_blanks["groupby"] = (
            procedural_blanks[procedural_blanks_groupby]
            .astype(str)
            .agg("_".join, axis=1)
        )
        procedural_blanks_unique_groupby = sorted(
            procedural_blanks["groupby"].unique(), key=lambda s: s.split("_")
        )

        # Assign colors
        procedural_blanks_palette = sns.blend_palette(
            ["lightgrey", "darkgrey"], n_colors=len(procedural_blanks_unique_groupby)
        )
        procedural_blanks_color_mapping = dict(
            zip(procedural_blanks_unique_groupby, procedural_blanks_palette)
        )

        for procedural_blank_groupby in procedural_blanks_unique_groupby:
            subset = procedural_blanks[
                procedural_blanks["fraction"] == procedural_blank_groupby
            ]
            plt.scatter(
                subset["PC1"],
                subset["PC2"],
                color=procedural_blanks_color_mapping[procedural_blank_groupby],
                marker=type_markers["procedural_blank"],
                label=f"Procedural blank: {procedural_blank_groupby}",
            )

        # --- Instrumental blanks ---
        instrumental_blanks = self.pca_df[self.pca_df["type"] == "instrumental_blank"]
        plt.scatter(
            instrumental_blanks["PC1"],
            instrumental_blanks["PC2"],
            color="black",
            marker=type_markers["instrumental_blank"],
            label="Instrumental blank",
        )

        plt.xlabel(f"PC1 ({self.pca.explained_variance_ratio_[0] * 100:.2f}%)")
        plt.ylabel(f"PC2 ({self.pca.explained_variance_ratio_[1] * 100:.2f}%)")
        plt.title(f"PCA: Colored by {'+'.join(samples_groupby)}, shape by type")
        plt.legend(bbox_to_anchor=(1.05, 1), loc="upper left", fontsize=8)
        plt.grid(True)

    def save_figure(self):
        plt.savefig(self.section.output["pca"], dpi=300, bbox_inches="tight")
        plt.close()
