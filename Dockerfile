# Base image
FROM mambaorg/micromamba:1.5.0

# Environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
ENV PATH="$JAVA_HOME/bin:$PATH"

# Install system dependencies
USER root
RUN apt-get update && apt-get install -y \
    openjdk-17-jdk \
    wget \
    unzip \
    curl \
    git \
    python3-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install .NET runtime for ThermoRawFileParser
RUN wget https://dot.net/v1/dotnet-install.sh -O /tmp/dotnet-install.sh && \
    chmod +x /tmp/dotnet-install.sh && \
    /tmp/dotnet-install.sh --runtime dotnet --install-dir /opt/dotnet && \
    rm /tmp/dotnet-install.sh
ENV PATH="/opt/dotnet:$PATH"

# Switch back to micromamba user
USER $MAMBA_USER
WORKDIR /home/mambauser/workflow

# Install Python packages + Snakemake
RUN micromamba install -y -n base -c conda-forge -c bioconda -c defaults \
    snakemake \
    python=3.11 \
    matchms \
    numpy \
    scipy \
    networkx \
    pandas \
    rdkit \
    scikit-learn \
    matplotlib \
    seaborn \
    jupyter \
    && micromamba clean --all --yes

# Create directory for tools
RUN mkdir -p /home/mambauser/tools

# Download ThermoRawFileParser
RUN mkdir -p /home/mambauser/tools/ThermoRawFileParser && \
    wget https://github.com/CompOmics/ThermoRawFileParser/releases/download/v.2.0.0-dev/ThermoRawFileParser-v.2.0.0-dev-linux.zip \
    -O /home/mambauser/tools/ThermoRawFileParser.zip && \
    unzip /home/mambauser/tools/ThermoRawFileParser.zip -d /home/mambauser/tools/ThermoRawFileParser/ && \
    rm /home/mambauser/tools/ThermoRawFileParser.zip

# Install MZmine
RUN mkdir -p /home/mambauser/tools/mzmine && \
    wget https://github.com/mzmine/mzmine/releases/download/v4.9.14/mzmine_Linux_portable-4.9.14.zip && \
    unzip mzmine_Linux_portable-4.9.14.zip -d /home/mambauser/tools/mzmine && \
    rm mzmine_Linux_portable-4.9.14.zip
ENV PATH="/home/mambauser/tools/mzmine/bin:$PATH"

# Install SIRIUS
RUN wget https://github.com/sirius-ms/sirius/releases/download/v6.3.4/sirius-6.3.4-linux-x64.zip && \
    unzip sirius-6.3.4-linux-x64.zip -d /home/mambauser/tools/ && \
    rm sirius-6.3.4-linux-x64.zip
ENV PATH="/home/mambauser/tools/sirius/bin:$PATH"

# Set working directory
WORKDIR /home/mambauser/workflow

# Default command
CMD ["/bin/bash"]