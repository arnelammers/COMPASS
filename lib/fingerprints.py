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
