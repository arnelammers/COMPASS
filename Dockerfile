# Base image
FROM condaforge/miniforge3:latest

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
    openssh-client \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install .NET runtime for ThermoRawFileParser
RUN wget https://dot.net/v1/dotnet-install.sh -O /tmp/dotnet-install.sh && \
    chmod +x /tmp/dotnet-install.sh && \
    /tmp/dotnet-install.sh --runtime dotnet --install-dir /opt/dotnet && \
    rm /tmp/dotnet-install.sh
ENV PATH="/opt/dotnet:$PATH"

# Create user
RUN usermod -l bio -d /home/bio -m ubuntu && \
    groupmod -n bio ubuntu && \
    mkdir -p /home/bio/workflow && \
    chown -R bio:bio /home/bio && \
    chown -R bio:bio /opt/conda

# Switch back to bio user
USER bio
WORKDIR /home/bio/workflow

# Create directory for tools
RUN mkdir -p /home/bio/tools

# Download ThermoRawFileParser
RUN mkdir -p /home/bio/tools/ThermoRawFileParser && \
    wget https://github.com/CompOmics/ThermoRawFileParser/releases/download/v.2.0.0-dev/ThermoRawFileParser-v.2.0.0-dev-linux.zip \
    -O /home/bio/tools/ThermoRawFileParser.zip && \
    unzip /home/bio/tools/ThermoRawFileParser.zip -d /home/bio/tools/ThermoRawFileParser/ && \
    rm /home/bio/tools/ThermoRawFileParser.zip

# Install MZmine
RUN mkdir -p /home/bio/tools/mzmine && \
    wget https://github.com/mzmine/mzmine/releases/download/v4.9.14/mzmine_Linux_portable-4.9.14.zip && \
    unzip mzmine_Linux_portable-4.9.14.zip -d /home/bio/tools/mzmine && \
    rm mzmine_Linux_portable-4.9.14.zip && \
    chmod -R a+rx /home/bio/tools/mzmine
ENV PATH="/home/bio/tools/mzmine/bin:$PATH"

# Install SIRIUS
RUN wget https://github.com/sirius-ms/sirius/releases/download/v6.3.7/sirius-6.3.7-linux-x64.zip && \
    unzip sirius-6.3.7-linux-x64.zip -d /home/bio/tools/ && \
    rm sirius-6.3.7-linux-x64.zip
ENV PATH="/home/bio/tools/sirius/bin:$PATH"

# Install SpecReboot
RUN git clone https://github.com/ECharria/SpecReBoot.git /home/bio/tools/specreboot 

RUN --mount=type=cache,target=/opt/conda/pkgs \
    conda env create -f /home/bio/tools/specreboot/environment.yml && \
    conda clean -a -y

RUN --mount=type=cache,target=/root/.cache/pip \
    conda run -n specreboot \
    pip install -e /home/bio/tools/specreboot/

# Install Python packages + Snakemake

# Create signaturizer env
COPY signaturizer_env.yml /tmp/
RUN --mount=type=cache,target=/opt/conda/pkgs \
    conda env create -f /tmp/signaturizer_env.yml && \
    conda clean -afy

# Create base
COPY analysis_env.yml /tmp/
RUN --mount=type=cache,target=/opt/conda/pkgs \
    conda env update -n base -f /tmp/analysis_env.yml && \
    conda clean -afy

# Set working directory
WORKDIR /home/bio/workflow

# Default command
CMD ["/bin/bash"]