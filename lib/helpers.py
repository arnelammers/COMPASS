from pathlib import Path


def get_mzmine_params(config, wildcards):
    """Returns the mzmine parameters for the given dataset."""
    return config["datasets"][wildcards.dataset]["mzmine"]


def get_samples(dataset):
    """Dynamically collects sample names ."""
    raw_samples = {p.stem for p in Path(f"data/{dataset}/raw").glob("*.raw")}

    mzml_samples = {p.stem for p in Path(f"data/{dataset}/mzml_raw").glob("*.mzML.gz")}

    return sorted(raw_samples | mzml_samples)



