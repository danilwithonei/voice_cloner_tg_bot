# Use a base image with CUDA 12.4 support and Ubuntu 22.04 (more stable for drivers)
FROM nvcr.io/nvidia/cuda:12.4.1-cudnn-runtime-ubuntu22.04

# Avoid interactive prompts during build
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3.10 \
    python3-pip \
    ffmpeg \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set python3.10 as default python
RUN ln -sf /usr/bin/python3.10 /usr/bin/python

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install PyTorch with CUDA 12.4 support
RUN pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu124 --break-system-packages

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
