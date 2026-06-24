from typing import TYPE_CHECKING

import h5py
import hdbscan
import matplotlib as mpl
import networkx as nx
import numpy as np
import pandas as pd
import umap
from matplotlib import pyplot as plt
from scipy.spatial.distance import cdist
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE
from sklearn.preprocessing import StandardScaler

from lib.fingerprints import get_op_fingerprint
from lib.molnet import get_annotated_molecular_network

if TYPE_CHECKING:
    from snakemake.iocontainers import snakemake

config = snakemake.params["config"]

# Get dataframes from annotations and query
structure_annotations_df = pd.read_csv(
    snakemake.input["structure_annotations"], low_memory=False
)
formula_annotations_df = pd.read_csv(
    snakemake.input["formula_annotations"], low_memory=False
)
query_df = pd.read_csv(
    f"resources/bioactivity_queries/{config['query']}.csv", low_memory=False
)

# Get all smiles of dataset and query

smiles_dataset = structure_annotations_df["smiles"].to_numpy()
smiles_query = query_df["smiles"].to_numpy()
all_smiles = np.concatenate([smiles_dataset, smiles_query])

# Get mask of all smiles belonging to query

query_mask = np.array([False] * len(smiles_dataset) + [True] * len(smiles_query))

# Get masks of all structure annotation type

spectral_mask_dataset = structure_annotations_df["annotation_type"] == "spectral_match"

spectral_mask = np.concatenate([spectral_mask_dataset, [False] * len(smiles_query)])

db_mask_dataset = structure_annotations_df["annotation_type"] == "structure_database"

db_mask = np.concatenate([db_mask_dataset, [False] * len(smiles_query)])

denovo_mask_dataset = structure_annotations_df["annotation_type"] == "denovo"

denovo_mask = np.concatenate([denovo_mask_dataset, [False] * len(smiles_query)])


def read_signatures():
    with h5py.File(snakemake.input["signatures"], "r") as fh:
        return fh["signature"][:]


def get_tsne_figure(X) -> plt.Figure:
    # Retain 85% of the total variance in the data
    pca = PCA(n_components=0.85)
    transformed = pca.fit_transform(X)
    n_components = pca.n_components_

    projection = TSNE(n_components=2).fit_transform(transformed)

    fig, ax = plt.subplots(figsize=(8, 6))

    ax.scatter(
        projection[spectral_mask, 0],
        projection[spectral_mask, 1],
        color="lightgrey",
        alpha=0.5,
        marker="^",
        label="Spectral match",
    )
    ax.scatter(
        projection[db_mask, 0],
        projection[db_mask, 1],
        color="lightgrey",
        alpha=0.5,
        marker="o",
        label="Structure database",
    )
    ax.scatter(
        projection[denovo_mask, 0],
        projection[denovo_mask, 1],
        color="lightgrey",
        alpha=0.5,
        marker="s",
        label="De novo",
    )
    ax.scatter(
        projection[:, 0][query_mask],
        projection[:, 1][query_mask],
        color="red",
        alpha=0.25,
        marker="*",
        label="Query",
    )

    # Set axis titles
    ax.set_xlabel("Component 1")
    ax.set_ylabel("Component 2")

    # Set title
    ax.set_title(
        f"t-SNE visualization of PCA-reduced data (PCA 85% variance retained: {n_components} components)"
    )

    # Add legend
    ax.legend(title="Type")

    plt.tight_layout()
    return fig


def get_hdbscan_clustering(X):
    clusterable_embedding = umap.UMAP(
        n_neighbors=config.get("clusterable_embedding_umap_n_neighbors", 15),
        min_dist=config.get("clusterable_embedding_umap_min_dist", 0.0),
        n_components=config.get("clusterable_embedding_n_components", 5),
        random_state=42,
    ).fit_transform(X)

    clustering = hdbscan.HDBSCAN(
        min_samples=config.get("hdbscan_min_samples", 5),
        min_cluster_size=config.get("hdbscan_cluster_size", 10),
    ).fit(clusterable_embedding)

    return clustering


def get_clusters_df(clustering):
    clusters_df = pd.DataFrame(
        {
            "cluster_label": range(len(clustering.cluster_persistence_)),
            "cluster_persistence": clustering.cluster_persistence_,
        }
    )

    return clusters_df


def get_structure_annotations_clustered_df(clustering):
    labels = clustering.labels_
    clustering_df = pd.DataFrame(
        {
            "smiles": all_smiles[~query_mask],
            "cluster_label": labels[~query_mask],
            "cluster_membership_probability": clustering.probabilities_[~query_mask],
            "cluster_outlier_score": clustering.outlier_scores_[~query_mask],
        }
    )
    # Sort to place highest probabilities first, then drop duplicate smiles
    clustering_df.sort_values(
        by="cluster_membership_probability", ascending=False, inplace=True
    )
    clustering_df.drop_duplicates(subset=["smiles"], keep="first", inplace=True)

    clustering_df = structure_annotations_df.merge(
        clustering_df, on="smiles", how="inner"
    )
    clustering_df.sort_values(
        by=["cluster_label", "cluster_membership_probability"],
        ascending=[True, False],
        inplace=True,
    )
    return clustering_df


def get_query_neighbors_df(X, clustering, structure_annotations_clustered_df):
    labels = clustering.labels_
    # Get labels of query compounds
    query_labels = labels[query_mask]

    # Get labels of clusters, without noise cluster
    query_clusters = set(query_labels) - {-1}

    # Get mask for clusters equal to query clusters
    cluster_mask = np.isin(labels, list(query_clusters))

    # Get mask from elements not in query
    result_mask = cluster_mask & ~query_mask

    # Get cosine scores
    X_dataset = X[result_mask]
    X_query = X[query_mask]

    distance_matrix = cdist(X_dataset, X_query, metric="euclidean")

    min_distances = np.min(distance_matrix, axis=1)
    closest_indices = np.argmin(distance_matrix, axis=1)

    # Filter clustered structure annotations to just have query clusters
    neighbors_df = structure_annotations_clustered_df[
        structure_annotations_clustered_df["cluster_label"].isin(query_clusters)
    ].copy()
    neighbors_df["query_min_distance"] = min_distances
    neighbors_df["query_closest_compound"] = (
        query_df["compound_name"].iloc[closest_indices].values
    )

    # Sort by membershop probability
    neighbors_df.sort_values(by="query_min_distance", ascending=True, inplace=True)

    return neighbors_df


def get_umap_figure(X, clustering):
    labels = clustering.labels_
    standard_embedding = umap.UMAP(random_state=42).fit_transform(X)

    fig, ax = plt.subplots(figsize=(12, 9))

    # Get helper mask to determine which labels determine clusters
    is_noise = labels == -1
    is_cluster = ~is_noise

    # Get cluster labels
    cluster_labels = labels[is_cluster]

    # Init color array with colors of each label
    colors = np.empty((len(labels), 4))

    # tab10 will be used for cluster labels
    cmap = mpl.colormaps["tab10"]
    colors[is_cluster] = [cmap(l % cmap.N) for l in cluster_labels]
    # Assign light grey to noise
    colors[is_noise] = (0.8, 0.8, 0.8, 1.0)  # lightgrey

    # dataset points (spectral)
    ax.scatter(
        standard_embedding[:, 0][~query_mask & spectral_mask],
        standard_embedding[:, 1][~query_mask & spectral_mask],
        c=colors[~query_mask & spectral_mask],
        alpha=0.3,
        marker="^",
        label="Spectral match",
    )
    # dataset points (structure database)
    ax.scatter(
        standard_embedding[:, 0][~query_mask & db_mask],
        standard_embedding[:, 1][~query_mask & db_mask],
        c=colors[~query_mask & db_mask],
        alpha=0.3,
        marker="o",
        label="Structure database",
    )
    # dataset points (denovo)
    ax.scatter(
        standard_embedding[:, 0][~query_mask & denovo_mask],
        standard_embedding[:, 1][~query_mask & denovo_mask],
        c=colors[~query_mask & denovo_mask],
        alpha=0.3,
        marker="s",
        label="De novo",
    )

    # reference points
    ax.scatter(
        standard_embedding[:, 0][query_mask],
        standard_embedding[:, 1][query_mask],
        c=colors[query_mask],
        marker="*",
        alpha=0.5,
        label="Query",
    )

    # Set title
    ax.set_title("UMAP")

    # Add first legend
    handles_type = [
        plt.Line2D(
            [], [], marker="^", color="gray", linestyle="None", label="Spectral match"
        ),
        plt.Line2D(
            [],
            [],
            marker="o",
            color="gray",
            linestyle="None",
            label="Structure database",
        ),
        plt.Line2D([], [], marker="s", color="gray", linestyle="None", label="De novo"),
        plt.Line2D([], [], marker="*", color="gray", linestyle="None", label="Query"),
    ]
    legend1 = ax.legend(handles=handles_type, title="Type")

    # Set color to black
    for h in legend1.legend_handles:
        h.set_color("grey")
        h.set_markerfacecolor("grey")
        h.set_markeredgecolor("grey")

    ax.add_artist(legend1)

    # Add label legend
    unique_labels = np.unique(labels)

    # Get mapping of label to color
    label_to_color = {lbl: colors[labels == lbl][0] for lbl in unique_labels}

    handles_labels = [
        plt.Line2D(
            [0],
            [0],
            marker="o",
            linestyle="",
            markerfacecolor=label_to_color[lbl],
            markeredgecolor="none",
            markersize=6,
            label=str(lbl),
        )
        for lbl in unique_labels
    ]

    legend2 = ax.legend(
        handles=handles_labels,
        bbox_to_anchor=(1.05, 1),
        loc="upper left",
        fontsize=8,
        title="Clusters",
    )

    ax.add_artist(legend2)

    plt.tight_layout()
    plt.subplots_adjust(right=0.8)

    return fig


def get_query_neighbors_molecular_network(
    graphml,
    query_neighbors_df: pd.DataFrame,
    structure_df: pd.DataFrame,
    formula_df: pd.DataFrame,
):
    G = nx.read_graphml(graphml)

    # Get list of ids that are clustered with query compounds
    valid_ids = query_neighbors_df["sirius_id"].tolist()

    # Get clusters that contain at least one id from query
    hit_clusters = {
        attrs.get("component") for n, attrs in G.nodes(data=True) if int(n) in valid_ids
    }

    # Filter nodes to only have nodes within clusters that have clustered compounds
    nodes_to_keep = [
        n for n, attrs in G.nodes(data=True) if attrs.get("component") in hit_clusters
    ]

    # filter graph
    G_filtered = G.subgraph(nodes_to_keep).copy()

    G_annotated = get_annotated_molecular_network(G_filtered, structure_df, formula_df)

    return G_annotated


# Compute signatures
signatures = read_signatures()
scaler_signatures = StandardScaler()
signatures_scaled = scaler_signatures.fit_transform(signatures)

additional = get_op_fingerprint(all_smiles)
scaler_additional = StandardScaler()
additional_scaled = scaler_additional.fit_transform(additional)

X = np.hstack([signatures_scaled, additional_scaled])


# Save tsne
tsne = get_tsne_figure(X)
tsne.savefig(snakemake.output["tsne"], dpi=300)

# Get label of HDBSCAN clustering
clustering = get_hdbscan_clustering(X)

# Get clusters
clusters_df = get_clusters_df(clustering)
clusters_df.to_csv(snakemake.output["clusters"], index=False)


# Get annoytations with cluster label
annot_cluster_df = get_structure_annotations_clustered_df(clustering)
annot_cluster_df.to_csv(
    snakemake.output["structure_annotations_clustered"], index=False
)

# Get compounds clustered with query
query_neighbors_df = get_query_neighbors_df(X, clustering, annot_cluster_df)
query_neighbors_df.to_csv(snakemake.output["query_neighbors"], index=False)

# Create UMAP and save
umapfig = get_umap_figure(X, clustering)
umapfig.savefig(snakemake.output["umap"], dpi=300)

similarity_measures = ["cosine", "modcosine", "spec2vec", "ms2deepscore"]
for similarity_measure in similarity_measures:
    molnet_query = get_query_neighbors_molecular_network(
        snakemake.input["graphml_" + similarity_measure],
        query_neighbors_df,
        annot_cluster_df,
        formula_annotations_df,
    )
    nx.write_graphml(
        molnet_query, snakemake.output["molnet_query_neighbors_" + similarity_measure]
    )
