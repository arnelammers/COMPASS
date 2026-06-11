from typing import TYPE_CHECKING

import h5py
import hdbscan
import numpy as np
import pandas as pd
import umap
from matplotlib import pyplot as plt
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE

if TYPE_CHECKING:
    from snakemake.iocontainers import snakemake

config = snakemake.config["datasets"][snakemake.wildcards.dataset]["report"][
    "bioactivity"
]

# Get dataframes from annotations and query
annotations_combined_df = pd.read_csv(
    snakemake.input["annotations_combined"], low_memory=False
)
query_df = pd.read_csv(
    f"resources/bioactivity_queries/{config['query']}.csv", low_memory=False
)

smiles_dataset = annotations_combined_df["smiles"].to_numpy()
smiles_query = query_df["smiles"].to_numpy()
all_smiles = np.concatenate([smiles_dataset, smiles_query])

query_mask = np.isin(all_smiles, smiles_query)

smiles_to_name = dict(
    zip(annotations_combined_df["smiles"], annotations_combined_df["compound_name"])
) | dict(zip(query_df["smiles"], query_df["compound_name"]))


def read_fingerprints():
    with h5py.File(snakemake.input["h5"], "r") as fh:
        return fh["signature"][:]


def create_tsne(signature) -> plt.Figure:
    # Retain 85% of the total variance in the data
    pca = PCA(n_components=0.85)
    n_components = pca.n_components
    transformed = pca.fit_transform(signature)

    projection = TSNE(n_components=2).fit_transform(transformed)

    fig, ax = plt.subplots(figsize=(8, 6), constrained_layout=True)

    ax.scatter(projection[:, 0], projection[:, 1], color="lightgrey", alpha=0.5)
    ax.scatter(
        projection[:, 0][query_mask],
        projection[:, 1][query_mask],
        color="red",
        alpha=0.25,
    )

    ax.set_title(
        f"t-SNE visualization of PCA-reduced data (PCA: {n_components} components)"
    )
    ax.set_xlabel("Component 1")
    ax.set_ylabel("Component 2")
    return fig


def get_clustering(signature):
    clusterable_embedding = umap.UMAP(
        n_neighbors=30,
        min_dist=0.0,
        n_components=2,
        random_state=42,
    ).fit_transform(fingerprints)

    labels = hdbscan.HDBSCAN(
        min_samples=2,
        min_cluster_size=5,
    ).fit_predict(clusterable_embedding)

    return labels


def get_clustered_with_query(labels):
    # Get labels of query compounds
    query_labels = labels[query_mask]

    # Get labels of clusters, without noise cluster
    query_clusters = set(query_labels) - {-1}

    # Get mask for clusters equal to query clusters
    cluster_mask = np.isin(labels, list(query_clusters))

    # Get mask from elements not in query
    result_mask = cluster_mask & ~query_mask

    neighbors_df = pd.DataFrame(
        {"smiles": all_smiles[result_mask], "label": labels[result_mask]}
    )
    neighbors_df["compound_name"] = neighbors_df["smiles"].map(smiles_to_name)

    query_df = pd.DataFrame(
        {"smiles": all_smiles[query_mask], "label": labels[query_mask]}
    )
    query_df["compound_name"] = query_df["smiles"].map(smiles_to_name)

    label_to_query_names = (
        query_df.groupby("label")["compound_name"]
        .apply(lambda x: list(x.dropna().unique()))
        .to_dict()
    )
    neighbors_df["query_compounds"] = neighbors_df["label"].map(label_to_query_names)

    return neighbors_df[["compound_name", "smiles", "label", "query_compounds"]]


def create_umap(signature, labels):
    standard_embedding = umap.UMAP(random_state=42).fit_transform(fingerprints)

    clustered = labels >= 0

    fig, ax = plt.subplots(figsize=(6, 6))

    # background points
    ax.scatter(
        standard_embedding[~clustered, 0],
        standard_embedding[~clustered, 1],
        color=(0.5, 0.5, 0.5),
        s=1,
        alpha=0.5,
    )

    # clustered points
    ax.scatter(
        standard_embedding[clustered, 0],
        standard_embedding[clustered, 1],
        c=labels[clustered],
        s=1,
        cmap="Spectral",
        alpha=0.5,
    )

    # reference points
    ax.scatter(
        standard_embedding[:, 0][query_mask],
        standard_embedding[:, 1][query_mask],
        c="red",
        marker="x",
        s=10,
        linewidths=1,
        alpha=0.25,
    )

    ax.set_title("UMAP")
    return fig


# Compute fingerprints
fingerprints = read_fingerprints()

# Save figure
tsne = create_tsne(fingerprints)
tsne.savefig(snakemake.output["tsne"], dpi=300)

labels = get_clustering(fingerprints)
clustered_df = get_clustered_with_query(labels)
clustered_df.to_csv(snakemake.output["clustered"], index=False)

umapfig = create_umap(fingerprints, labels)
umapfig.savefig(snakemake.output["umap"], dpi=300)
