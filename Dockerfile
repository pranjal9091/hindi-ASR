# Use NVIDIA CUDA 12.4.1 Runtime with cuDNN as base
FROM nvidia/cuda:12.4.1-cudnn-runtime-ubuntu22.04

# Avoid prompt interaction during installation
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Set the working directory
WORKDIR /app

# Install software-properties-common, add deadsnakes PPA, and install Python 3.11, dev packages, and ffmpeg
RUN apt-get update && apt-get install -y --no-install-recommends \
    software-properties-common \
    && add-apt-repository -y ppa:deadsnakes/ppa \
    && apt-get update && apt-get install -y --no-install-recommends \
    python3.11 \
    python3.11-dev \
    python3.11-distutils \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set python3.11 as the default python3 and python
RUN ln -sf /usr/bin/python3.11 /usr/bin/python3 && \
    ln -sf /usr/bin/python3.11 /usr/bin/python

# Install pip for Python 3.11
RUN curl -sS https://bootstrap.pypa.io/get-pip.py | python3.11

# Copy requirements
COPY requirements.txt .

# Upgrade pip and install Python dependencies
RUN python3 -m pip install --upgrade pip && \
    python3 -m pip install --no-cache-dir -r requirements.txt

# Copy all project files
COPY . .

# Expose FastAPI on port 8000
EXPOSE 8000

# Start FastAPI with Uvicorn
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
