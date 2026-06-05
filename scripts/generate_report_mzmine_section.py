from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from snakemake.iocontainers import snakemake

from lib.report.mzmine.pca import MzminePCA
from lib.report.mzmine.section import MzmineSection

mzmine_section = MzmineSection(
    input=snakemake.input,
    output=snakemake.output,
    config=snakemake.config["datasets"][snakemake.wildcards.dataset]["report"][
        "mzmine"
    ],
)

pca = MzminePCA(mzmine_section)
pca.save_figure()
