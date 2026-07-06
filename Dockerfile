# Use NVIDIA CUDA 11.8 Runtime with cuDNN 8 as base
FROM nvidia/cuda:11.8.0-cudnn8-runtime-ubuntu22.04

# Avoid prompt interaction during installation
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Set the working directory
WORKDIR /app

# Install Python 3, pip, and ffmpeg
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    python3-dev \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Set python3 as the default python
RUN ln -sf /usr/bin/python3 /usr/bin/python

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
