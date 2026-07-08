import logging
import os
import shutil
import uuid
import json
import time
import subprocess
import re
import numpy as np
from contextlib import asynccontextmanager

from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # Custom fallback for environments without python-dotenv
    def load_dotenv(dotenv_path=".env"):
        if os.path.exists(dotenv_path):
            with open(dotenv_path, "r") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if "=" in line:
                        key, val = line.split("=", 1)
                        key = key.strip()
                        val = val.strip().strip('"').strip("'")
                        os.environ[key] = val
    load_dotenv()

# Configuration settings via environment variables
MODEL_SIZE = os.getenv("MODEL_SIZE", "large-v3")
DEVICE = os.getenv("DEVICE", "cuda")
COMPUTE_TYPE = os.getenv("COMPUTE_TYPE", "float16")
MAX_UPLOAD_SIZE = int(os.getenv("MAX_UPLOAD_SIZE", "52428800"))  # Default 50MB (52,428,800 bytes)
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")
MOCK_ASR = os.getenv("MOCK_ASR", "false").lower() == "true"

# Configure logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("hindi-asr-backend")

# Auto-fallback logic: check if CUDA device is available
cuda_available = False
FALLBACK_TO_CPU = False

if not MOCK_ASR:
    try:
        import ctranslate2
        cuda_available = ctranslate2.get_cuda_device_count() > 0
    except Exception:
        pass

    if DEVICE == "cuda" and not cuda_available:
        FALLBACK_TO_CPU = True
        DEVICE = "cpu"
        COMPUTE_TYPE = "int8"


# Import the core ASR pipeline function
from src.main import transcribe_audio



class MockWhisperModel:
    def transcribe(self, audio_path, **kwargs):
        class MockSegment:
            def __init__(self):
                self.id = 0
                self.seek = 0
                self.start = 0.0
                self.end = 2.0
                self.text = " यह एक परीक्षण है।"
                self.tokens = []
                self.temperature = 0.0
                self.avg_logprob = -0.1
                self.compression_ratio = 1.0
                self.no_speech_prob = 0.0
                self.words = None
        class MockInfo:
            def __init__(self):
                self.language = "hi"
                self.language_probability = 0.99
                self.duration = 2.0
        return [MockSegment()], MockInfo()

# Performance metrics store
metrics_store = {
    "requests_processed": 0,
    "total_processing_time_ms": 0.0
}

# Application state for storing the loaded model instance
state = {}

def get_gpu_info():
    gpu_detected = False
    cuda_version = "Unknown"
    vram_total = "Unknown"
    vram_free = "Unknown"
    gpu_name = "Unknown"
    
    try:
        # Query nvidia-smi for GPU details and VRAM
        res = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.total,memory.free", "--format=csv,noheader,nounits"],
            capture_output=True, text=True, check=True
        )
        lines = res.stdout.strip().split("\n")
        if lines and lines[0]:
            parts = lines[0].split(",")
            gpu_name = parts[0].strip()
            vram_total = f"{parts[1].strip()} MB"
            vram_free = f"{parts[2].strip()} MB"
            gpu_detected = True
    except Exception:
        pass
        
    try:
        # Query nvidia-smi for CUDA version
        res_cuda = subprocess.run(["nvidia-smi"], capture_output=True, text=True)
        match = re.search(r"CUDA Version:\s*([\d\.]+)", res_cuda.stdout)
        if match:
            cuda_version = match.group(1)
    except Exception:
        pass
        
    return {
        "gpu_detected": gpu_detected,
        "gpu_name": gpu_name,
        "vram_total": vram_total,
        "vram_free": vram_free,
        "cuda_version": cuda_version
    }

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Log GPU validation details
    gpu_info = get_gpu_info()
    logger.info(f"GPU validation details:")
    logger.info(f"  - GPU Detected: {gpu_info['gpu_detected']}")
    logger.info(f"  - GPU Name: {gpu_info['gpu_name']}")
    logger.info(f"  - CUDA Version: {gpu_info['cuda_version']}")
    logger.info(f"  - VRAM Total: {gpu_info['vram_total']}, VRAM Free: {gpu_info['vram_free']}")
    logger.info(f"  - Target Inference Device: {DEVICE} ({COMPUTE_TYPE})")

    if FALLBACK_TO_CPU:
        logger.warning("CUDA device was requested, but no GPU was detected. Falling back to CPU/int8 mode.")

    # Load Faster-Whisper model on startup
    logger.info(f"ASR initialization started: model_size={MODEL_SIZE}, device={DEVICE}, compute_type={COMPUTE_TYPE}")
    if MOCK_ASR:
        state["model"] = MockWhisperModel()
        logger.info("ASR initialization completed: Mock Whisper model loaded (MOCK_ASR=True).")
    else:
        try:
            from faster_whisper import WhisperModel
            state["model"] = WhisperModel(MODEL_SIZE, device=DEVICE, compute_type=COMPUTE_TYPE)
            logger.info("ASR initialization completed: Faster-Whisper model loaded successfully.")
            
            # Model Warmup: Perform a small warmup inference with 1s of silence
            try:
                logger.info("Starting Whisper model warmup inference...")
                warmup_start = time.time()
                silence = np.zeros(16000, dtype=np.float32)
                # Consume the generator to execute model execution
                list(state["model"].transcribe(silence)[0])
                logger.info(f"Whisper model warmup completed in {time.time() - warmup_start:.2f} seconds.")
            except Exception as warmup_ex:
                logger.warning(f"Whisper model warmup inference encountered an issue: {warmup_ex}")
        except Exception as e:
            logger.critical(f"ASR initialization failed: Error loading model: {e}")
            state["model"] = None
    yield
    # Cleanup on shutdown
    state.clear()
    logger.info("Application shutdown: Cleaned up model state.")

app = FastAPI(
    title="Hindi ASR Backend Service",
    description="A FastAPI backend wrapping the Faster-Whisper Large-v3 transcription pipeline.",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception handlers for structured JSON errors
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": exc.detail
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal error"
        }
    )

@app.get("/")
async def root():
    return {
        "service": "Hindi-ASR",
        "status": "running"
    }

@app.get("/health")
async def health():
    model_loaded = state.get("model") is not None
    return {
        "status": "healthy" if model_loaded else "unhealthy",
        "model_loaded": model_loaded
    }

@app.get("/version")
async def version():
    return {
        "version": app.version
    }

@app.get("/metrics")
async def get_metrics():
    avg_time = 0.0
    if metrics_store["requests_processed"] > 0:
        avg_time = metrics_store["total_processing_time_ms"] / metrics_store["requests_processed"]
    return {
        "device": DEVICE,
        "model": MODEL_SIZE,
        "model_loaded": state.get("model") is not None,
        "requests_processed": metrics_store["requests_processed"],
        "avg_processing_time_ms": round(avg_time, 2)
    }

@app.post("/transcribe")
async def transcribe(file: UploadFile = File(...)):
    start_time = time.time()
    
    # 1. API request received
    logger.info(f"Request received: filename={file.filename if file else 'None'}")
    
    if not file or not file.filename:
        logger.warning("Rejected upload: Empty file or no filename")
        raise HTTPException(status_code=400, detail="Invalid audio")

    # Extract extension and content type
    _, ext = os.path.splitext(file.filename)
    content_type = file.content_type
    
    # 6. Add INFO logs that print Filename, Extension, Content-Type before validation
    logger.info(f"Incoming upload - Filename: {file.filename}, Extension: {ext}, Content-Type: {content_type}")

    # Request validation: Extension check
    allowed_extensions = {".wav", ".mp3", ".m4a", ".aac", ".webm"}
    if ext.lower() not in allowed_extensions:
        logger.warning(f"Rejected upload: unsupported file extension {ext}")
        raise HTTPException(status_code=400, detail="Invalid audio")

    # Request validation: Content-Type check
    allowed_content_types = {
        "audio/webm",
        "audio/webm;codecs=opus",
        "audio/ogg",
        "audio/wav",
        "audio/x-wav",
        "audio/mp3",
        "audio/mpeg",
        "audio/mp4",
        "audio/aac",
        "audio/m4a",
        "audio/x-m4a"
    }
    normalized_content_type = content_type.lower().replace(" ", "") if content_type else ""
    if normalized_content_type not in allowed_content_types:
        logger.warning(f"Rejected upload: unsupported Content-Type {content_type}")
        raise HTTPException(status_code=400, detail="Invalid audio")

    # Request validation: Content-Length check
    content_length = file.headers.get("content-length")
    if content_length and int(content_length) > MAX_UPLOAD_SIZE:
        logger.warning(f"Rejected upload: Content-Length {content_length} exceeds limit {MAX_UPLOAD_SIZE}")
        raise HTTPException(status_code=413, detail="File too large")

    # Verify model is ready
    model = state.get("model")
    if model is None:
        logger.error("Request failed: Whisper model is not initialized or failed to load.")
        raise HTTPException(status_code=500, detail="Internal error")

    # Setup temporary paths
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    
    request_id = str(uuid.uuid4())
    temp_audio_path = os.path.join(UPLOAD_DIR, f"{request_id}{ext}")
    temp_output_dir = os.path.join(UPLOAD_DIR, f"out_{request_id}")
    
    try:
        # Save uploaded file in chunks to limit memory usage and enforce file size check
        size = 0
        with open(temp_audio_path, "wb") as buffer:
            while True:
                chunk = await file.read(1024 * 1024)  # 1MB chunks
                if not chunk:
                     break
                size += len(chunk)
                if size > MAX_UPLOAD_SIZE:
                    logger.warning(f"Rejected upload: File size exceeds limit {MAX_UPLOAD_SIZE} during read")
                    raise HTTPException(status_code=413, detail="File too large")
                buffer.write(chunk)

        # 2. Audio saved
        logger.info(f"File saved: {temp_audio_path}")
        
        # 3. ASR started
        logger.info(f"ASR started: processing {temp_audio_path}")
        
        # Run transcription pipeline
        transcribe_audio(
            input_path=temp_audio_path,
            output_dir=temp_output_dir,
            normalize=False,
            denoise=False,
            model_size=MODEL_SIZE,
            device=DEVICE,
            compute_type=COMPUTE_TYPE,
            model=model
        )
        
        # 4. ASR completed
        logger.info(f"ASR completed: processed {temp_audio_path}")
        
        # Read the generated corrected_transcript.json
        corrected_json_path = os.path.join(temp_output_dir, "corrected_transcript.json")
        if not os.path.exists(corrected_json_path):
            raise FileNotFoundError("corrected_transcript.json was not generated by ASR pipeline.")
            
        with open(corrected_json_path, "r", encoding="utf-8") as f:
            corrected_data = json.load(f)
            
        # Processing NLP & clinical details
        from src.clinical_nlp import process_clinical_nlp
        from src.clinical_reasoner import reason_clinical_nlp
        from src.clinical_speech_analytics import analyze_clinical_speech
        
        transcript_text = corrected_data.get("full_transcript", "")
        clinical_base = process_clinical_nlp(transcript_text)
        clinical_data = reason_clinical_nlp(transcript_text, clinical_base)
        
        # Compute transcript-based cognitive speech biomarkers
        speech_analytics = analyze_clinical_speech(transcript_text, corrected_data.get("segments", []))
        clinical_data["speech_analytics"] = speech_analytics

        # Read acoustic biomarkers
        acoustic_json_path = os.path.join(temp_output_dir, "acoustic_biomarkers.json")
        acoustic_biomarkers = None
        if os.path.exists(acoustic_json_path):
            try:
                with open(acoustic_json_path, "r", encoding="utf-8") as af:
                    acoustic_biomarkers = json.load(af)
            except Exception as ae:
                logger.error(f"Failed to read acoustic biomarkers json: {ae}")
        clinical_data["acoustic_biomarkers"] = acoustic_biomarkers

        # Populate legacy SOAP fields with dementia-specific biomarkers
        clinical_data["soap_note"] = {
            "subjective": f"Subjective Cognitive Metrics: Memory indicators count: {speech_analytics['memory_indicators']['memory_loss_phrases_count']} ({', '.join(speech_analytics['memory_indicators']['memory_loss_phrases_examples']) if speech_analytics['memory_indicators']['memory_loss_phrases_examples'] else 'None'}). Uncertainty phrases count: {speech_analytics['memory_indicators']['uncertainty_phrases_count']}. Self-corrections count: {speech_analytics['memory_indicators']['self_corrections_count']}.",
            "objective": f"Objective Biomarkers: Speech Rate (WPM): {speech_analytics['speech_fluency']['words_per_minute']}. Articulation Rate (WPM): {speech_analytics['speech_fluency']['articulation_rate']}. Pause Ratio: {speech_analytics['pause_metrics']['pause_ratio']}. Hesitations (>0.3s): {speech_analytics['pause_metrics']['hesitation_pauses_count']}. Significant pauses (>1s): {speech_analytics['pause_metrics']['significant_pauses_count']}. Fillers per minute: {speech_analytics['fillers']['fillers_per_minute']}. Perseveration score: {speech_analytics['repetitions']['perseveration_score']}.",
            "assessment": f"Biomarker Assessment: Overall Risk Level: {speech_analytics['clinical_summary']['overall_cognitive_risk']} Risk. Memory Risk: {speech_analytics['clinical_summary']['memory_risk']}. Language Risk: {speech_analytics['clinical_summary']['language_risk']}. Speech Risk: {speech_analytics['clinical_summary']['speech_risk']}. Type-Token Ratio: {speech_analytics['lexical_features']['type_token_ratio']}. MATTR: {speech_analytics['lexical_features']['moving_average_ttr']}.",
            "plan": "Biomarker Platform recommendation: Conduct standardized verbal cognitive fluency assessments periodically. Monitor pause structures and filler/repetition scores to track cognitive trends. No diagnosis is estimated."
        }
        clinical_data["summary"] = {
            "chief_complaint": "Cognitive biomarker profiling screening assessment.",
            "symptoms": f"Hesitations: {speech_analytics['memory_indicators']['recall_difficulty_indicators_count']}, Self-corrections: {speech_analytics['memory_indicators']['self_corrections_count']}, Fillers: {sum(speech_analytics['fillers']['filler_frequency'].values())}",
            "diagnosis": "Cognitive biomarker profiling (Screening only)",
            "advice": "This is a transcript-based screening of cognitive biomarkers. Consult a medical specialist for clinical validation."
        }
        clinical_data["possible_diagnosis"] = []
        clinical_data["medicines"] = []
        clinical_data["vitals"] = {
            "blood_pressure": "N/A",
            "temperature": "N/A",
            "pulse": "N/A",
            "oxygen": "N/A",
            "weight": "N/A"
        }
        clinical_data["timeline"] = [
            {"time": "Biomarker Warning", "event": warning} for warning in speech_analytics["executive_function"]["timeline_inconsistencies"]
        ]
        clinical_data["follow_up_questions"] = [
            "Can you recall the three objects mentioned in the recall exercise?",
            "What year and month is it currently?",
            "Can you name the day of the week today?",
            "Please describe a simple task like brushing your teeth or preparing tea."
        ]

        response_data = {
            "success": True,
            "language": corrected_data.get("language", "hi"),
            "transcript": transcript_text,
            "duration": corrected_data.get("duration", 0.0),
            "segments": corrected_data.get("segments", []),
            "clinical": clinical_data
        }
        
        # 5. Processing time
        processing_time = time.time() - start_time
        logger.info(f"Processing time: {processing_time:.2f} seconds")
        
        # Track metrics
        metrics_store["requests_processed"] += 1
        metrics_store["total_processing_time_ms"] += processing_time * 1000
        
        return response_data
        
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error during transcription request: {e}")
        raise HTTPException(status_code=500, detail="Internal error")
        
    finally:
        # Automatically delete temporary files after transcription completes
        # 6. Cleanup complete
        if temp_audio_path and os.path.exists(temp_audio_path):
            try:
                os.remove(temp_audio_path)
            except Exception as ex:
                logger.error(f"Failed to delete temporary audio file {temp_audio_path}: {ex}")
                
        if temp_output_dir and os.path.exists(temp_output_dir):
            try:
                shutil.rmtree(temp_output_dir)
            except Exception as ex:
                logger.error(f"Failed to delete temporary output directory {temp_output_dir}: {ex}")
        
        logger.info(f"Cleanup complete for request {request_id}")
