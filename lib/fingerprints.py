import numpy as np
from rdkit import Chem
from rdkit.Chem import Crippen, Descriptors, Lipinski


def _get_op_fingerprint(smiles):
    """Creates OP fingerprints with statistics relevant to OP"""
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None

    return np.array(
        [
            Descriptors.MolWt(mol),
            Crippen.MolLogP(mol),
            Descriptors.TPSA(mol),
            Lipinski.NumHDonors(mol),
            Lipinski.NumHAcceptors(mol),
            Descriptors.NumAromaticRings(mol),
            Lipinski.NumRotatableBonds(mol),
            Descriptors.FractionCSP3(mol),
        ]
    )


get_op_fingerprint = np.vectorize(_get_op_fingerprint, signature="()->(n)")


def find_max_cosines(A, B):
    """Function to find maximum cosine (closest vectors) between two matrices, return cosines and indices of best match"""
    # normalize rows of matrix A and B to unit vectors (also prevent division by 0)
    A_norm = A / np.linalg.norm(A, axis=1, keepdims=True).clip(min=1e-9)
    B_norm = B / np.linalg.norm(B, axis=1, keepdims=True).clip(min=1e-9)

    # compute all pairwise cosine similarities (dot product equals cosine similarity with unit vectors)
    similarity_matrix = np.dot(A_norm, B_norm.T)

    # clip values to [-1.0, 1.0]
    similarity_matrix = np.clip(similarity_matrix, -1.0, 1.0)

    # find the best match in B for each row in A
    best_match_indices = np.argmax(similarity_matrix, axis=1)
    max_cosines = np.max(similarity_matrix, axis=1)

    return max_cosines, best_match_indices
