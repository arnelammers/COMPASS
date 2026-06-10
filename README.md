
# COMPASS

COMPASS (COmpound Mapping and Prioritization through Activity and Spectral Similarity analysis) is a Snakemake/Python metabolomics workflow for prioritizing unknown compounds based on spectral similarity and predicted bioactivity. Compounds of interest are identified by targeting specific bioactivity profiles, toxicological endpoints, or structural similarity to a user-defined query, and visualized through molecular networking and bioactivity descriptor comparison.

COMPASS builds on several tools and resources: [MZmine](https://mzio.io/mzmine-news/) (data pre-processing and feature alignment), [SIRIUS](https://bio.informatik.uni-jena.de/software/sirius/) (feature annotation), [SpecReboot](https://github.com/ECharria/SpecReBoot) (molecular networking), and the bioactivity descriptors from [Bertoni et al.](https://doi.org/10.1038/s41467-023-43793-x) Thanks to the developers and authors for making their work available.

COMPASS was created as a MSc thesis project at the [Van der Hooft Computational Metabolomics Group](https://vdhooftcompmet.github.io/) at the [Bioinformatics department](https://www.wur.nl/en/chair-groups/bioinformatics-group) of [Wageningen University & Research](https://www.wur.nl/en).

## Requirements

COMPASS requires [Docker](https://docs.docker.com/get-docker/) to build and run. No additional dependencies need to be installed manually. COMPASS has been tested on Linux; however, as it runs entirely within Docker, it should work on any operating system that supports Docker.

## Input

Create a subfolder for your dataset under `data/{dataset}/` and provide your mass spectrometry files in one of two ways:

- **`data/{dataset}/mzml/`** — place `.mzML` or `.mzML.gz` files directly here
- **`data/{dataset}/raw/`** — place Thermo `.raw` files here; the workflow will convert them to `.mzML.gz` files automatically

Also create a `metadata.csv` file in the dataset folder. It must contain a column `filename` with the filenames as they appear (or will appear) in the `mzml/` folder after conversion.

Then update the configuration file to your preferences according to the [configuration docs](docs/config.md).

## Quickstart

Clone the repository and build the Docker image:

```bash
docker build -t compass-app .
```

Then enter the container using the following command:

```bash
docker run -it --rm \
  --memory=14g --shm-size=8g \
  -e JAVA_TOOL_OPTIONS="-Xmx12g" \
  -u "$(id -u):$(id -g)" \
  -v "$(pwd)":/home/mambauser/workflow \
  -v "$(pwd)/.sirius-6.3":/home/mambauser/.sirius-6.3 \
  -v "$(pwd)/.mzmine":/home/mambauser/.mzmine \
  compass-app bash
```

Before running the pipeline for the first time, log in to MZmine and SIRIUS in the container by the following commands respectively. Their configurations will be stored on your local machine via the mounted volumes:

```bash
mzmine -login-console
sirius login -u  -p 
```

Then run the pipeline in the container:

```bash
snakemake --cores 8
```

The results for each substep will appear in the `results/` folder for each dataset that was specified in the configuration. Logs for each tool are written to the `logs/` folder.

## References

* Schmid, R., Heuckeroth, S., Korf, A. et al. Integrative analysis of multimodal mass spectrometry data in MZmine 3. Nat Biotechnol 41, 447–449 (2023). https://doi.org/10.1038/s41587-023-01690-2
* Dührkop, K., Fleischauer, M., Ludwig, M. et al. SIRIUS 4: a rapid tool for turning tandem mass spectra into metabolite structure information. Nat Methods 16, 299–302 (2019). https://doi.org/10.1038/s41592-019-0344-8
* Charria Girón, E., Torres Ortega, L. R., Mergola Greef, J., Marin Felix, Y., Caicedo Ortega, N. H., Surup, F., Medema, M. H., & van der Hooft, J. J. J. (2026). Bootstrap resampling of mass spectral pairs with SpecReBoot reveals hidden molecular relationships. bioRxiv. doi: https://doi.org/10.64898/2026.02.03.703446
* Bertoni, M., Duran-Frigola, M., Badia-i-Mompel, P. et al. Bioactivity descriptors for uncharacterized chemical compounds. Nat Commun 12, 3932 (2021). https://doi.org/10.1038/s41467-021-24150-4