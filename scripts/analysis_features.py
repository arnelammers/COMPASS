import json
from typing import TYPE_CHECKING

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap
from scipy.stats import ttest_ind
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

if TYPE_CHECKING:
    from snakemake.iocontainers import snakemake

config = snakemake.params["config"]

feature_table_df = pd.read_csv(snakemake.input["feature_table"], low_memory=False)
feature_table_before_subtraction_df = pd.read_csv(
    snakemake.input["feature_table_before_subtraction"], low_memory=False
)
metadata_df = pd.read_csv(snakemake.input["metadata"], low_memory=False)

# Keep a list of expected filenames from metadata
valid_filenames = set(metadata_df["filename"].tolist())


def extract_area_df() -> pd.DataFrame:
    """Filters, cleans, and aligns the area columns with metadata."""

    # Identify all area columns
    area_cols = [
        col
        for col in feature_table_before_subtraction_df.columns
        if col.startswith("datafile:") and col.endswith(":area")
    ]

    # Slice the dataframe and immediately copy
    area_df = feature_table_before_subtraction_df[area_cols].copy()

    # Clean the column names cleanly using .rename()
    # Example: 'datafile:Sample_A.mzML:area' -> 'Sample_A.mzML'
    area_df = area_df.rename(
        columns=lambda x: x.replace("datafile:", "").replace(":area", "")
    )

    # Filter columns to only keep those present in metadata
    matched_cols = [col for col in area_df.columns if col in valid_filenames]

    return area_df[matched_cols]


def extract_pca(area_df: pd.DataFrame) -> tuple[PCA, pd.DataFrame]:
    X = area_df.T

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
    pca_df = pca_df.merge(metadata_df, left_index=True, right_on="filename").set_index(
        "filename"
    )

    return pca, pca_df


def generate_pca(pca: PCA, pca_df: pd.DataFrame):
    samples_groupby = config["pca"]["samples_groupby"]
    procedural_blanks_groupby = config["pca"]["procedural_blanks_groupby"]

    # Map type to marker shapes
    type_markers = {
        "sample": "o",
        "instrumental_blank": "s",
        "procedural_blank": "^",
    }

    # Set figure size
    fig, ax = plt.subplots(figsize=(7, 5), constrained_layout=True)

    # --- Samples ---
    samples = pca_df[pca_df["type"] == "sample"].copy()

    # Set group by column and et unique combinations
    samples["groupby"] = samples[samples_groupby].astype(str).agg("_".join, axis=1)
    samples_unique_groupby = sorted(
        samples["groupby"].unique(), key=lambda s: tuple(s.split("_"))
    )

    # Assign colors using palette
    cmap = mpl.colormaps["tab20"]

    samples_palette = [cmap(i) for i in np.linspace(0, 1, len(samples_unique_groupby))]

    samples_color_mapping = dict(zip(samples_unique_groupby, samples_palette))

    # Plot samples
    for sample_groupby in samples_unique_groupby:
        subset = samples[samples["groupby"] == sample_groupby]
        ax.scatter(
            subset["PC1"],
            subset["PC2"],
            color=samples_color_mapping[sample_groupby],
            marker=type_markers["sample"],
            label=f"Sample: {sample_groupby}",
        )

    # --- Procedural blanks ---
    procedural_blanks = pca_df[pca_df["type"] == "procedural_blank"].copy()

    # Set group by column and et unique combinations
    procedural_blanks["groupby"] = (
        procedural_blanks[procedural_blanks_groupby].astype(str).agg("_".join, axis=1)
    )
    procedural_blanks_unique_groupby = sorted(
        procedural_blanks["groupby"].unique(), key=lambda s: tuple(s.split("_"))
    )

    # Assign colors
    procedural_blanks_cmap = LinearSegmentedColormap.from_list(
        "grey_blend", ["darkgrey", "lightgrey"]
    )

    procedural_blanks_palette = [
        procedural_blanks_cmap(x)
        for x in np.linspace(0, 1, len(procedural_blanks_unique_groupby))
    ]
    procedural_blanks_color_mapping = dict(
        zip(procedural_blanks_unique_groupby, procedural_blanks_palette)
    )

    for procedural_blank_groupby in procedural_blanks_unique_groupby:
        subset = procedural_blanks[
            procedural_blanks["groupby"] == procedural_blank_groupby
        ]
        ax.scatter(
            subset["PC1"],
            subset["PC2"],
            color=procedural_blanks_color_mapping[procedural_blank_groupby],
            marker=type_markers["procedural_blank"],
            label=f"Procedural blank: {procedural_blank_groupby}",
        )

    # --- Instrumental blanks ---
    instrumental_blanks = pca_df[pca_df["type"] == "instrumental_blank"]
    ax.scatter(
        instrumental_blanks["PC1"],
        instrumental_blanks["PC2"],
        color="black",
        marker=type_markers["instrumental_blank"],
        label="Instrumental blank",
    )

    ax.set_xlabel(f"PC1 ({pca.explained_variance_ratio_[0] * 100:.2f}%)")
    ax.set_ylabel(f"PC2 ({pca.explained_variance_ratio_[1] * 100:.2f}%)")
    ax.set_title(f"PCA: Colored by {'+'.join(samples_groupby)}, shape by type")
    ax.legend(bbox_to_anchor=(1.05, 1), loc="upper left", fontsize=8)
    ax.grid(True)

    return fig


def get_feature_state_columns_samples():
    # Get all filenames
    files = metadata_df.loc[
        (metadata_df["type"] == "sample"),
        "filename",
    ].tolist()
    # map filennames to get feature state columns
    mapped_files = [f"datafile:{x}:feature_state" for x in files]
    return mapped_files


def get_feature_state_columns_samples_condition(condition_column, condition):
    # Get all filenames with condition
    files = metadata_df.loc[
        (metadata_df[condition_column] == condition)
        & (metadata_df["type"] == "sample"),
        "filename",
    ].tolist()
    # map filennames to get area columns
    mapped_files = [f"datafile:{x}:feature_state" for x in files]
    return mapped_files


def get_area_columns_samples_condition(condition_column, condition):
    # Get all filenames with condition
    files = metadata_df.loc[
        (metadata_df[condition_column] == condition)
        & (metadata_df["type"] == "sample"),
        "filename",
    ].tolist()
    # map filennames to get area columns
    mapped_files = [f"datafile:{x}:area" for x in files]
    return mapped_files


def get_da_df():
    condition_columns = config["da_condition_columns"]

    # Check whether all columns only have two different values
    bad_cols = {
        col: metadata_df[col].nunique(dropna=True)
        for col in condition_columns
        if metadata_df[col].nunique(dropna=True) != 2
    }

    if bad_cols:
        raise ValueError(
            "The following condition columns do NOT have exactly two unique values:\n"
            + "\n".join([f"{col}: {n} unique values" for col, n in bad_cols.items()])
        )

    # Filter features that have annotations
    da_df = feature_table_df.copy()
    da_df["detected_rate"] = (
        da_df[get_feature_state_columns_samples()] == "DETECTED"
    ).mean(axis=1)

    # Do comparison for each column
    for condition_column in condition_columns:
        # Get different condition values
        conditions = metadata_df[condition_column].dropna().unique()
        # Do for each condition
        for condition in conditions:
            # get area columns
            area_columns = get_area_columns_samples_condition(
                condition_column, condition
            )
            # fillna 0
            da_df[area_columns] = da_df[area_columns].fillna(0)
            # add mean values column
            da_df["mean_area" + ":" + condition] = da_df[area_columns].mean(axis=1)
        # combine conditions in name
        conditions_combined = (
            condition_column + ":" + conditions[0] + "_vs_" + conditions[1]
        )
        # set log2folchange
        da_df["log2FC:" + conditions_combined] = np.log2(
            da_df["mean_area:" + conditions[0]] / da_df["mean_area:" + conditions[1]]
        )
        # Get p-value
        areas_condition1 = da_df[
            get_area_columns_samples_condition(condition_column, conditions[0])
        ]
        areas_condition2 = da_df[
            get_area_columns_samples_condition(condition_column, conditions[1])
        ]

        da_df["welch_p:" + conditions_combined] = [
            ttest_ind(a, b, equal_var=False, nan_policy="omit").pvalue
            for a, b in zip(areas_condition1.values, areas_condition2.values)
        ]
    cols = [
        c
        for c in da_df.columns
        if c in ["id", "rt", "mz", "area", "height"]
        or c == "detected_rate"
        or c.startswith("log2FC:")
        or c.startswith("mean_area:")
        or c.startswith("welch_p:")
    ]
    da_df = da_df.loc[:, cols]

    # order df
    da_df = da_df.sort_values(by="id", ascending=True)

    return da_df


def get_number_of_features():
    return len(feature_table_df)


def get_number_of_features_before_subtraction():
    return len(feature_table_before_subtraction_df)


def get_number_of_ms2_features():
    return int((feature_table_df["fragment_scans"] != 0).sum())


def get_number_of_features_per_condition():
    numbers_per_condition = {}
    # Do comparison for each column
    for condition_column in config["pca"]["samples_groupby"]:
        # Get different condition values
        conditions = metadata_df[condition_column].dropna().unique()
        # Do for each condition
        for condition in conditions:
            # get feature state columns
            feature_state_columns = get_feature_state_columns_samples_condition(
                condition_column, condition
            )
            numbers_per_condition[
                f"# Features after subtraction ({condition_column},{condition})"
            ] = int(
                (feature_table_df[feature_state_columns] == "DETECTED")
                .any(axis=1)
                .sum()
            )
            numbers_per_condition[
                f"# Features after subtraction with MS2 ({condition_column},{condition})"
            ] = int(
                (
                    (feature_table_df[feature_state_columns] == "DETECTED").any(axis=1)
                    & (feature_table_df["fragment_scans"] != 0)
                ).sum()
            )
    return numbers_per_condition


## PCA

# Extract the area dataframe during initialization
area_df = extract_area_df()

# Extract PCA dataframe
pca, pca_df = extract_pca(area_df)

# Generate PCA
fig = generate_pca(pca, pca_df)
fig.savefig(snakemake.output["pca"], dpi=300)

# Differential analysis
da_df = get_da_df()
da_df.to_csv(snakemake.output["da"], index=False)

## Stats

stats = {
    "# Features before subtraction": get_number_of_features_before_subtraction(),
    "# Features after subtraction": get_number_of_features(),
    "# Features after subtraction with MS2": get_number_of_ms2_features(),
    **get_number_of_features_per_condition(),
}

with open(snakemake.output["stats"], "w") as f:
    json.dump(stats, f, indent=2)
