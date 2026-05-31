
# Setup

To build the docker image execute:

```sh
docker build -t thesis-app .
```

To run the pipeline execute:

```sh
docker run --rm -u "$(id -u):$(id -g)" -v "$(pwd)":/home/mambauser/workflow thesis-app snakemake --cores 4
```