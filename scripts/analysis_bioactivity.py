from typing import TYPE_CHECKING

import h5py
import hdbscan
import matplotlib as mpl
import networkx as nx
import numpy as np
import pandas as pd
import umap
from adjustText import adjust_text
from matplotlib import pyplot as plt
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE

if TYPE_CHECKING:
    from snakemake.iocontainers import snakemake

config = snakemake.params["config"]

# Get dataframes from annotations and query
structure_annotations_combined_df = pd.read_csv(
    snakemake.input["structure_annotations_combined"], low_memory=False
)
formula_annotations_df = pd.read_csv(
    snakemake.input["formula_annotations"], low_memory=False
)
query_df = pd.read_csv(
    f"resources/bioactivity_queries/{config['query']}.csv", low_memory=False
)

smiles_dataset = structure_annotations_combined_df["smiles"].to_numpy()
smiles_query = query_df["smiles"].to_numpy()
all_smiles = np.concatenate([smiles_dataset, smiles_query])

query_mask = np.isin(all_smiles, smiles_query)


def read_signatures():
    with h5py.File(snakemake.input["signatures"], "r") as fh:
        return fh["signature"][:]


def get_tsne_figure(X) -> plt.Figure:
    # Retain 85% of the total variance in the data
    pca = PCA(n_components=0.85)
    transformed = pca.fit_transform(X)
    n_components = pca.n_components_

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
        f"t-SNE visualization of PCA-reduced data (PCA 85% variance retained: {n_components} components)"
    )
    ax.set_xlabel("Component 1")
    ax.set_ylabel("Component 2")
    return fig


def get_hdbscan_clustering(X):
    clusterable_embedding = umap.UMAP(
        n_neighbors=15,
        min_dist=0.0,
        n_components=5,
        random_state=42,
    ).fit_transform(X)

    clustering = hdbscan.HDBSCAN(
        min_samples=5,
        min_cluster_size=10,
    ).fit(clusterable_embedding)

    return clustering


def get_query_neighbors_df(clustering):
    labels = clustering.labels_
    # Get labels of query compounds
    query_labels = labels[query_mask]

    # Get labels of clusters, without noise cluster
    query_clusters = set(query_labels) - {-1}

    # Get mask for clusters equal to query clusters
    cluster_mask = np.isin(labels, list(query_clusters))

    # Get mask from elements not in query
    result_mask = cluster_mask & ~query_mask

    neighbors_df = pd.DataFrame(
        {
            "smiles": all_smiles[result_mask],
            "cluster_label": labels[result_mask],
            "cluster_membership_probability": clustering.probabilities_[result_mask],
            "cluster_outlier_score": clustering.outlier_scores_[result_mask],
        }
    )

    query_label_df = query_df.copy()
    query_label_df["cluster_label"] = labels[query_mask]

    label_to_query_names = (
        query_label_df.groupby("cluster_label")["compound_name"]
        .apply(lambda x: ";".join(list(x.dropna().unique())))
        .to_dict()
    )
    neighbors_df["query_compounds"] = neighbors_df["cluster_label"].map(
        label_to_query_names
    )

    merged_df = structure_annotations_combined_df.merge(
        neighbors_df, on="smiles", how="inner"
    )

    merged_df.sort_values(
        by="cluster_membership_probability", ascending=False, inplace=True
    )

    return merged_df


def get_umap_figure(X, clustering):
    labels = clustering.labels_
    standard_embedding = umap.UMAP(random_state=42).fit_transform(X)

    clustered = labels >= 0

    fig, ax = plt.subplots(figsize=(6, 6), constrained_layout=True)

    cmap = mpl.colormaps["tab10"]

    # background points
    ax.scatter(
        standard_embedding[~clustered, 0],
        standard_embedding[~clustered, 1],
        color=(0.5, 0.5, 0.5),
        s=5,
        alpha=0.5,
    )

    # clustered points
    colors_mapped = [cmap(lbl % cmap.N) for lbl in labels[clustered]]
    ax.scatter(
        standard_embedding[clustered, 0],
        standard_embedding[clustered, 1],
        c=colors_mapped,
        s=5,
        alpha=0.5,
    )

    # reference points
    ax.scatter(
        standard_embedding[:, 0][query_mask],
        standard_embedding[:, 1][query_mask],
        c="red",
        marker="x",
        s=20,
        linewidths=1,
        alpha=0.25,
    )

    unique_labels = np.unique(labels[clustered])

    handles = [
        plt.Line2D(
            [0],
            [0],
            marker="o",
            linestyle="",
            markerfacecolor=cmap(lbl % cmap.N),
            markeredgecolor="none",
            markersize=6,
            label=str(lbl),
        )
        for lbl in unique_labels
    ]

    ax.legend(
        bbox_to_anchor=(1.05, 1),
        loc="upper left",
        fontsize=8,
        handles=handles,
        title="Labels",
    )

    ax.set_title("UMAP")
    return fig


def get_molecular_network_figure_query_neighbors(
    graphml, query_neighbors: pd.DataFrame
):
    G = nx.read_graphml(graphml)

    # Get list of ids that are clustered with query compounds
    valid_ids = query_neighbors["sirius_id"].tolist()

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

    # Color clustered compounds red
    node_colors = [
        "red" if int(n) in valid_ids else "lightgray"
        for n, attrs in G_filtered.nodes(data=True)
    ]
    return get_molecular_network_figure(G_filtered, node_colors)


def get_molecular_network_figure(G, node_colors):
    fig, ax = plt.subplots(figsize=(12, 12), constrained_layout=True)

    # Make nodes more seperate
    pos = nx.spring_layout(
        G,
        seed=42,
        k=1.5 / np.sqrt(len(G.nodes())),
    )

    # Draw nodes and edges
    nx.draw(
        G,
        pos,
        ax=ax,
        node_color=node_colors,
        node_size=50,
        edge_color="gray",
        width=0.5,
        with_labels=False,
    )

    # Get dict that map id to smiles/mol formula
    structure_id_to_name = (
        structure_annotations_combined_df.set_index("sirius_id")
        .apply(
            lambda r: (
                f"{r['compound_name']} [{r['molecularFormula']}] ({r['annotation_type']})"
            ),
            axis=1,
        )
        .to_dict()
    )

    formula_id_to_formula = (
        formula_annotations_df.set_index("sirius_id")
        .apply(lambda r: f"{r['molecularFormula']} (formula)", axis=1)
        .to_dict()
    )

    # Determine labels of nodes
    labels = {
        n: structure_id_to_name.get(int(n)) or formula_id_to_formula.get(int(n)) or "?"
        for n in G.nodes()
    }

    # Get texts
    texts = [ax.text(x, y, labels[n], fontsize=6) for n, (x, y) in pos.items()]

    # Use adjust text to prevent nodes colliding
    adjust_text(
        texts,
        ax=ax,
        expand_points=(1.2, 1.4),
        arrowprops=dict(
            arrowstyle="-",
            lw=0.3,
            color="gray",
            shrinkA=10,
            shrinkB=5,
            linestyle=(0, (2, 2)),
        ),
    )

    return fig


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
    clustering_df = structure_annotations_combined_df.merge(
        clustering_df, on="smiles", how="inner"
    )
    clustering_df.sort_values(
        by=["cluster_label", "cluster_membership_probability"],
        ascending=[True, False],
        inplace=True,
    )
    return clustering_df


def get_clusters_df(clustering):
    clusters_df = pd.DataFrame(
        {
            "cluster_label": range(len(clustering.cluster_persistence_)),
            "cluster_persistence": clustering.cluster_persistence_,
        }
    )

    return clusters_df


# Compute signatures
signatures = read_signatures()

# Save tsne
tsne = get_tsne_figure(signatures)
tsne.savefig(snakemake.output["tsne"], dpi=300)

# Get label of HDBSCAN clustering
clustering = get_hdbscan_clustering(signatures)

# Get clusters
clusters_df = get_clusters_df(clustering)
clusters_df.to_csv(snakemake.output["clusters"], index=False)


# Get annoytations with cluster label
annot_cluster_df = get_structure_annotations_clustered_df(clustering)
annot_cluster_df.to_csv(
    snakemake.output["structure_annotations_clustered"], index=False
)

# Get compounds clustered with query
query_neighbors_df = get_query_neighbors_df(clustering)
query_neighbors_df.to_csv(snakemake.output["query_neighbors"], index=False)

# Create UMAP and save
umapfig = get_umap_figure(signatures, clustering)
umapfig.savefig(snakemake.output["umap"], dpi=300)

similarity_methods = ["cosine", "modcosine", "spec2vec", "ms2deepscore"]
for similarity_method in similarity_methods:
    molnet_query = get_molecular_network_figure_query_neighbors(
        snakemake.input["graphml_" + similarity_method], query_neighbors_df
    )
    molnet_query.savefig(
        snakemake.output["molnet_query_neighbors_" + similarity_method], dpi=300
    )
