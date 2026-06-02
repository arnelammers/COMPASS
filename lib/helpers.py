from pathlib import Path


def get_mzmine_params(config, wildcards):
    """Returns the mzmine parameters for the given dataset."""
    return config["datasets"][wildcards.dataset]["mzmine"]


def get_samples(dataset):
    """Dynamically collects sample names ."""
    raw_samples = {p.stem for p in Path(f"data/{dataset}/raw").glob("*.raw")}

    mzml_samples = {p.stem for p in Path(f"data/{dataset}/mzml_raw").glob("*.mzML.gz")}

    return sorted(raw_samples | mzml_samples)


def get_spectral_library_files(config, dataset):
    """Returns local paths to spectral library files required by a dataset."""
    libs = config["datasets"][dataset]["mzmine"]["spectral_library_files"]

    return [f"resources/spectral_libraries/{lib}" for lib in libs]
