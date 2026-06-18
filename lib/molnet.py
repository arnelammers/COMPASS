import networkx as nx
import pandas as pd


def get_annotated_molecular_network(
    G: nx.Graph, structure_df: pd.DataFrame, formula_df: pd.DataFrame
):
    # Filter formula annotation to not contain rows that have strcuture annotation
    formula_filtered_df = formula_df[
        ~formula_df["sirius_id"].isin(structure_df["sirius_id"])
    ]

    # Merge annotations
    combined_df = pd.concat([structure_df, formula_filtered_df], ignore_index=True)

    # Fill NA
    combined_df = combined_df.fillna("")

    # Match types
    combined_df["sirius_id"] = combined_df["sirius_id"].astype(str)

    # Get dict per sirius id
    node_attributes = combined_df.set_index("sirius_id").to_dict("index")

    # Annotate the graph's nodes
    nx.set_node_attributes(G, node_attributes)

    return G
