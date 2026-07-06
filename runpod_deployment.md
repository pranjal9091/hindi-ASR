# RunPod GPU Deployment Guide — Hindi-ASR Beta

This guide provides instructions to deploy the production-ready Hindi-ASR backend API on a RunPod GPU instance for low-latency GPU-accelerated speech recognition.

---

## 1. RunPod Pod Requirements

### GPU Recommendations
- **Recommended GPU**: **NVIDIA RTX 4090** or **NVIDIA L4** (excellent performance-to-cost ratio for inference).
- **Alternative (High Traffic)**: **NVIDIA A100** or **A10G**.
- **Minimum VRAM**: **16 GB** (required to comfortably load `faster-whisper` `large-v3` model with `float16` compute type).

### System Disk and Volume Storage
- **Container Disk**: **15 GB** (for the OS base layers, FFmpeg, CUDA runtime, and application libraries).
- **Volume Disk**: **15 GB** (configured at `/root/.cache/huggingface` or similar cache paths to persist downloaded Faster-Whisper weights, preventing redownloading weights on container restarts).
- **Total Storage Recommended**: **30 GB**.

---

## 2. Environment Variables Configuration

Set these environment variables inside the RunPod template or environment configuration panel:

| Environment Variable | Recommended Value | Description |
| --- | --- | --- |
| `MODEL_SIZE` | `large-v3` | Model weights version to load from Hugging Face |
| `DEVICE` | `cuda` | Target execution device (`cuda` or `cpu` fallback) |
| `COMPUTE_TYPE` | `float16` | floating point compute precision for optimal GPU speed |
| `MAX_UPLOAD_SIZE` | `52428800` | Max file upload limit in bytes (50MB default) |
| `LOG_LEVEL` | `INFO` | Console output verbosity |
| `UPLOAD_DIR` | `uploads` | Directory for temporary files storage |
| `MOCK_ASR` | `false` | Set to `true` ONLY to bypass model loading for testing |

---

## 3. Docker Build and Push Instructions

To run the container on RunPod, build and push your Docker image to a registry (e.g., Docker Hub or GitHub Packages):

```bash
# 1. Build the CUDA-compatible Docker image
docker build -t <your-docker-username>/hindi-asr-backend:latest .

# 2. Log in to your Docker Hub account
docker login

# 3. Push the image to the public registry
docker push <your-docker-username>/hindi-asr-backend:latest
```

---

## 4. Launching the RunPod Instance

1. Log in to **[RunPod.io](https://runpod.io)** and navigate to **Templates** -> **New Template**.
2. Set the following settings:
   - **Template Name**: `hindi-asr-service`
   - **Container Image**: `<your-docker-username>/hindi-asr-backend:latest`
   - **Docker Command**: `uvicorn app:app --host 0.0.0.0 --port 8000`
   - **Container Port**: `8000`
   - **Exposed Port (HTTP/TCP)**: `8000`
3. Add the required **Environment Variables** (from Section 2).
4. Navigate to **GPU Pods** and select a GPU (e.g. **RTX 4090**).
5. Deploy the template. Once started, RunPod will map port `8000` to a public URL.

---

## 5. Connecting the React Frontend

1. Retrieve the public URL from the RunPod dashboard (it will look like `https://<pod-id>-8000.proxy.runpod.net`).
2. When starting or building the React frontend, configure the API target by setting the environment variable:
   ```bash
   # For local development targeting RunPod backend
   VITE_BACKEND_URL="https://<pod-id>-8000.proxy.runpod.net" npm run dev
   ```
3. The React app will automatically communicate with the public RunPod endpoint, routing audio recordings directly to the GPU server.
