from typing import TYPE_CHECKING

import numpy as np
import pandas as pd
from scipy.stats import ttest_ind

if TYPE_CHECKING:
    from snakemake.iocontainers import snakemake

config = snakemake.params["config"]

# Get dataframes from annotations
feature_table_df = pd.read_csv(snakemake.input["feature_table"], low_memory=False)
structure_annotations_combined_df = pd.read_csv(
    snakemake.input["structure_annotations_combined"], low_memory=False
)
formula_annotations_df = pd.read_csv(
    snakemake.input["formula_annotations"], low_memory=False
)
query_neighbors_df = pd.read_csv(snakemake.input["query_neighbors"], low_memory=False)

metadata_df = pd.read_csv(snakemake.input["metadata"], low_memory=False)

condition_columns = config["condition_columns"]

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


def get_area_columns(condition_column, condition):
    # Get all filenames with condition
    files = metadata_df.loc[
        (metadata_df[condition_column] == condition)
        & (metadata_df["type"] == "sample"),
        "filename",
    ].tolist()
    # map filennames to get area columns
    mapped_files = [f"datafile:{x}:area" for x in files]
    return mapped_files


def get_foldchanges_df():
    # Filter features that have annotations
    df_filtered = feature_table_df[
        feature_table_df["id"].isin(formula_annotations_df["id"])
        | feature_table_df["id"].isin(structure_annotations_combined_df["id"])
    ].copy()

    # Do comparison for each column
    for condition_column in condition_columns:
        # Get different condition values
        conditions = metadata_df[condition_column].dropna().unique()
        # Do for each condition
        for condition in conditions:
            # get area columns
            area_columns = get_area_columns(condition_column, condition)
            # fillna 0
            df_filtered[area_columns] = df_filtered[area_columns].fillna(0)
            # add mean values column
            df_filtered["da:" + ":" + condition + ":mean_area"] = df_filtered[
                area_columns
            ].mean(axis=1)
        # combine conditions in name
        conditions_combined = (
            condition_column + ":" + conditions[0] + "_vs_" + conditions[1]
        )
        # set log2folchange
        df_filtered["da:" + conditions_combined + ":log2FC"] = np.log2(
            df_filtered["da:" + ":" + conditions[0] + ":mean_area"]
            / df_filtered["da:" + ":" + conditions[1] + ":mean_area"]
        )
        # Get p-value
        areas_condition1 = df_filtered[
            get_area_columns(condition_column, conditions[0])
        ]
        areas_condition2 = df_filtered[
            get_area_columns(condition_column, conditions[1])
        ]

        df_filtered["da:" + conditions_combined + ":welch_p"] = [
            ttest_ind(a, b, equal_var=False, nan_policy="omit").pvalue
            for a, b in zip(areas_condition1.values, areas_condition2.values)
        ]
    cols = [c for c in df_filtered.columns if c == "id" or c.startswith("da:")]
    fc_df = df_filtered.loc[:, cols]

    # include formula annotations
    fc_df = fc_df.merge(
        formula_annotations_df[["id", "molecularFormula"]], on="id", how="left"
    )
    # include structure annotations
    fc_df = fc_df.merge(
        structure_annotations_combined_df[["id", "compound_name", "smiles"]],
        on="id",
        how="left",
    )
    fc_df["query_neighbors"] = fc_df["id"].isin(query_neighbors_df["id"])

    # reorder columns
    front_cols = [
        "id",
        "compound_name",
        "smiles",
        "molecularFormula",
        "query_neighbors",
    ]

    fc_df = fc_df[front_cols + [c for c in fc_df.columns if c not in front_cols]]

    # order df
    fc_df = fc_df.sort_values(by=["query_neighbors", "id"], ascending=[False, True])

    return fc_df


fc_df = get_foldchanges_df()
fc_df.to_csv(snakemake.output["da"], index=False)
