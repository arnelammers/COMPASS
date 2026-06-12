from typing import TYPE_CHECKING

import pandas as pd
from signaturizer import Signaturizer

if TYPE_CHECKING:
    from snakemake.iocontainers import snakemake

config = snakemake.params["config"]

structure_annotations_combined_df = pd.read_csv(
    snakemake.input["structure_annotations_combined"], low_memory=False
)
smiles_query_df = pd.read_csv(
    f"resources/bioactivity_queries/{config['query']}.csv", low_memory=False
)


def compute_signatures(smiles_list: list[str]):
    signaturizer = Signaturizer(config["cc_spaces"])
    results = signaturizer.predict(all_smiles, snakemake.output["signatures"])
    return results


# Get unique smiles from dataframes
smiles_dataset = structure_annotations_combined_df["smiles"].tolist()
smiles_query = smiles_query_df["smiles"].tolist()
all_smiles = smiles_dataset + smiles_query

# Compute signatures
signatures = compute_signatures(all_smiles)
