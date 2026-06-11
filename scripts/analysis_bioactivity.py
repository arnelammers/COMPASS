from typing import TYPE_CHECKING

import h5py
import hdbscan
import networkx as nx
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


def get_hdbscan_clustering(signature):
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

    query_label_df = query_df.copy()
    query_label_df["label"] = labels[query_mask]

    label_to_query_names = (
        query_label_df.groupby("label")["compound_name"]
        .apply(lambda x: ";".join(list(x.dropna().unique())))
        .to_dict()
    )
    neighbors_df["query_compounds"] = neighbors_df["label"].map(label_to_query_names)

    merged_df = annotations_combined_df.merge(neighbors_df, on="smiles", how="inner")

    return merged_df


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


def get_molecular_network(graphml, clustered: pd.DataFrame):
    G = nx.read_graphml(graphml)

    valid_ids = clustered["sirius_id"].tolist()

    hit_clusters = {
        attrs.get("component") for n, attrs in G.nodes(data=True) if int(n) in valid_ids
    }

    nodes_to_keep = [
        n for n, attrs in G.nodes(data=True) if attrs.get("component") in hit_clusters
    ]

    G_filtered = G.subgraph(nodes_to_keep).copy()

    node_colors = [
        "red" if int(n) in valid_ids else "lightgray"
        for n, attrs in G_filtered.nodes(data=True)
    ]

    fig, ax = plt.subplots(figsize=(12, 12))

    id_to_name = annotations_combined_df.set_index("sirius_id")[
        "compound_name"
    ].to_dict()

    pos = nx.spring_layout(
        G_filtered,
        seed=42,
        k=1.5 / np.sqrt(len(G_filtered.nodes())),
    )

    labels = {n: id_to_name.get(int(n)) or str(n) for n in G_filtered.nodes()}

    nx.draw(
        G_filtered,
        pos,
        ax=ax,
        node_color=node_colors,
        node_size=50,
        edge_color="gray",
        width=0.5,
        with_labels=True,
        labels=labels,
        font_size=6,
    )

    return fig


# Compute fingerprints
fingerprints = read_fingerprints()

# Save tsne
tsne = create_tsne(fingerprints)
tsne.savefig(snakemake.output["tsne"], dpi=300)

# Get label of HDBSCAN clustering
labels = get_hdbscan_clustering(fingerprints)

# Get compounds clustered with query
clustered_df = get_clustered_with_query(labels)
clustered_df.to_csv(snakemake.output["clustered"], index=False)

# Create UMAP and save
umapfig = create_umap(fingerprints, labels)
umapfig.savefig(snakemake.output["umap"], dpi=300)

# Create molecular network
molnet_cosine = get_molecular_network(snakemake.input["graphml_cosine"], clustered_df)
molnet_cosine.savefig(snakemake.output["molnet_cosine"], dpi=300)

molnet_modcosine = get_molecular_network(
    snakemake.input["graphml_modcosine"], clustered_df
)
molnet_modcosine.savefig(snakemake.output["molnet_modcosine"], dpi=300)

molnet_spec2vec = get_molecular_network(
    snakemake.input["graphml_spec2vec"], clustered_df
)
molnet_spec2vec.savefig(snakemake.output["molnet_spec2vec"], dpi=300)

molnet_ms2deepscore = get_molecular_network(
    snakemake.input["graphml_ms2deepscore"], clustered_df
)
molnet_ms2deepscore.savefig(snakemake.output["molnet_ms2deepscore"], dpi=300)
