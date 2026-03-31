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
RUN micromamba install -y -n base -c conda-forge \
    snakemake \
    python=3.10 \
    matchms \
    numpy \
    scipy \
    networkx \
    pandas \
    ms2lda \
    rdkit \
    scikit-learn \
    matplotlib \
    seaborn \
    jupyter \
    && micromamba clean --all --yes

# Download ThermoRawFileParser
RUN wget https://github.com/CompOmics/ThermoRawFileParser/releases/download/v2.0.0-dev/ThermoRawFileParser-v.2.0.0-dev-linux.zip \
    -O /home/mambauser/tools/ThermoRawFileParser.zip && \
    unzip /home/mambauser/tools/ThermoRawFileParser.zip -d /home/mambauser/tools/ && \
    rm /home/mambauser/tools/ThermoRawFileParser.zip

# Install MZmine
RUN wget https://github.com/mzmine/mzmine3/releases/download/3.1.0/MZmine-3.1.0.zip && \
    unzip MZmine-3.1.0.zip -d /home/mambauser/tools/ && \
    rm MZmine-3.1.0.zip
ENV PATH="/home/mambauser/tools/MZmine-3.1.0/bin:$PATH"

# Install SIRIUS
RUN wget https://bio.informatik.uni-jena.de/downloads/Sirius-5.7.3_linux64.tar.gz && \
    tar -xvzf Sirius-5.7.3_linux64.tar.gz -C /home/mambauser/tools/ && \
    rm Sirius-5.7.3_linux64.tar.gz
ENV PATH="/home/mambauser/tools/SIRIUS-5.7.3:$PATH"

# Install MS2LDA dependencies
RUN pip install pyms2lda

# Set working directory
WORKDIR /home/mambauser/workflow

# Default command
CMD ["/bin/bash"]