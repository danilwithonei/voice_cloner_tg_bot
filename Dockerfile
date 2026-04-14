# Use a base image with CUDA 12.8 support and Ubuntu 24.04 (includes Python 3.12)
FROM nvidia/cuda:12.8.0-cudnn-runtime-ubuntu24.04

# Avoid interactive prompts during build
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    ffmpeg \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set python3 as default python
RUN ln -sf /usr/bin/python3 /usr/bin/python

# Set working directory
WORKDIR /app

# Upgrade pip and install setuptools
RUN pip install --upgrade pip setuptools --break-system-packages

# Copy requirements first for better caching
COPY requirements.txt .

# Install PyTorch with CUDA 12.8 support
RUN pip install torch==2.8.0 torchaudio==2.8.0 --index-url https://download.pytorch.org/whl/cu128 --break-system-packages

# Install remaining dependencies
RUN pip install -r requirements.txt --break-system-packages

# Copy the rest of the application
COPY . .

# Create directory for temporary files
RUN mkdir -p temp_audio

# Expose the API port
EXPOSE 8000

# Default command (can be overridden in docker-compose)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
