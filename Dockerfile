# ------------------------
# Base image
# ------------------------
FROM mambaorg/micromamba:1.5.0

# ------------------------
# Environment variables
# ------------------------
ENV DEBIAN_FRONTEND=noninteractive
ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
ENV PATH="$JAVA_HOME/bin:$PATH"

# ------------------------
# Install system dependencies
# ------------------------
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

# ------------------------
# Switch back to micromamba user
# ------------------------
USER $MAMBA_USER
WORKDIR /home/mambauser/workflow

# ------------------------
# Install Python packages + Snakemake
# ------------------------
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

# ------------------------
# Install MZmine
# ------------------------
RUN wget https://github.com/mzmine/mzmine3/releases/download/3.1.0/MZmine-3.1.0.zip && \
    unzip MZmine-3.1.0.zip -d /home/mambauser/tools/ && \
    rm MZmine-3.1.0.zip
ENV PATH="/home/mambauser/tools/MZmine-3.1.0/bin:$PATH"

# ------------------------
# Install SIRIUS + CANOPUS
# ------------------------
RUN wget https://bio.informatik.uni-jena.de/downloads/Sirius-5.7.3_linux64.tar.gz && \
    tar -xvzf Sirius-5.7.3_linux64.tar.gz -C /home/mambauser/tools/ && \
    rm Sirius-5.7.3_linux64.tar.gz
ENV PATH="/home/mambauser/tools/SIRIUS-5.7.3:$PATH"

# ------------------------
# Install Fermo
# ------------------------
RUN git clone https://github.com/sdrogers/fermo.git /home/mambauser/tools/fermo && \
    pip install --no-cache-dir /home/mambauser/tools/fermo

# ------------------------
# Install MS2LDA dependencies
# ------------------------
RUN pip install pyms2lda

# ------------------------
# Set working directory
# ------------------------
WORKDIR /home/mambauser/workflow

# ------------------------
# Default command
# ------------------------
CMD ["/bin/bash"]