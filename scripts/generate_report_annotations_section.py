from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from snakemake.iocontainers import snakemake

from lib.report.annotations.section import AnnotationsSection
from lib.report.annotations.smiles_combined import AnnotationsSmilesCombined
from lib.report.annotations.stats import AnnotationsStats

annotations_section = AnnotationsSection(
    input=snakemake.input,
    output=snakemake.output,
    config=snakemake.config["datasets"][snakemake.wildcards.dataset]["report"][
        "annotations"
    ],
)

combined = AnnotationsSmilesCombined(annotations_section)
combined.save_to_file()

stats = AnnotationsStats(annotations_section)
stats.save_to_file()
