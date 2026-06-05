from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from snakemake.iocontainers import snakemake

from lib.report.mzmine.pca import MzminePCA
from lib.report.mzmine.section import MzmineSection
from lib.report.mzmine.stats import MzmineStats

mzmine_section = MzmineSection(
    input=snakemake.input,
    output=snakemake.output,
    config=snakemake.config["datasets"][snakemake.wildcards.dataset]["report"][
        "mzmine"
    ],
)

pca = MzminePCA(mzmine_section)
pca.save_figure()

stats = MzmineStats(mzmine_section)
stats.save_to_file()
