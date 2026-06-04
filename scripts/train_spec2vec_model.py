import argparse

from matchms import SpectrumProcessor
from matchms.filtering.default_pipelines import DEFAULT_FILTERS
from matchms.importing import load_from_mgf
from spec2vec import SpectrumDocument
from spec2vec.model_building import train_new_word2vec_model

parser = argparse.ArgumentParser(description="Train Spec2Vec Model")
parser.add_argument("--input", required=True, help="Path to input MGF file")
parser.add_argument("--output", required=True, help="Path to output model file")

args = parser.parse_args()

# Load spectra from MGF
spectra = list(load_from_mgf(args.input))

# Add some default filters. You can add more filters functions like require min. number of peaks
processor = SpectrumProcessor(DEFAULT_FILTERS)

# Apply filter pipeline
spectra_cleaned, _ = processor.process_spectra(spectra)
spectra_cleaned = [s for s in spectra_cleaned if s is not None]

# Create spectrum documents
reference_documents = [SpectrumDocument(s, n_decimals=2) for s in spectra_cleaned]

# Train your reference model
model_file = args.output
model = train_new_word2vec_model(
    reference_documents,
    iterations=[10, 20, 30],
    filename=model_file,
    workers=2,
    progress_logger=True,
)
