import React, { useState, useEffect, useRef } from "react";
import { Mic, Square, X, Activity, MessageSquare, Flame } from "lucide-react";

export default function MicrophoneRecorder({ 
  onRecordingComplete, 
  onRecordingError, 
  onSilenceChange,
  wordCount = 0,
  disabled 
}) {
  const [isRecording, setIsRecording] = useState(false);
  const [duration, setDuration] = useState(0);
  const [isSilent, setIsSilent] = useState(false);
  const [error, setError] = useState("");

  const mediaRecorderRef = useRef(null);
  const streamRef = useRef(null);
  const audioContextRef = useRef(null);
  const analyserRef = useRef(null);
  const animationFrameRef = useRef(null);
  const timerIntervalRef = useRef(null);
  const chunksRef = useRef([]);
  const isCancelledRef = useRef(false);
  
  const micAreaRef = useRef(null);
  const barsRef = useRef([]);
  const silenceStartRef = useRef(null);

  // Check MediaRecorder browser support
  useEffect(() => {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia || !window.MediaRecorder) {
      const errorMsg = "Your browser does not support audio recording.";
      setError(errorMsg);
      if (onRecordingError) onRecordingError(errorMsg);
    }
  }, [onRecordingError]);

  // Clean up on unmount
  useEffect(() => {
    return () => {
      cleanupStream();
      if (timerIntervalRef.current) clearInterval(timerIntervalRef.current);
      if (animationFrameRef.current) cancelAnimationFrame(animationFrameRef.current);
    };
  }, []);

  const cleanupStream = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }
    if (audioContextRef.current && audioContextRef.current.state !== "closed") {
      audioContextRef.current.close();
      audioContextRef.current = null;
    }
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
    }
  };

  const startRecording = async () => {
    if (disabled || error) return;
    setError("");
    chunksRef.current = [];
    setDuration(0);
    isCancelledRef.current = false;
    setIsSilent(false);
    silenceStartRef.current = null;

    try {
      // Request microphone permissions
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;

      // Setup MediaRecorder
      let options = {};
      if (MediaRecorder.isTypeSupported("audio/webm;codecs=opus")) {
        options = { mimeType: "audio/webm;codecs=opus" };
      } else if (MediaRecorder.isTypeSupported("audio/webm")) {
        options = { mimeType: "audio/webm" };
      } else if (MediaRecorder.isTypeSupported("audio/ogg")) {
        options = { mimeType: "audio/ogg" };
      } else if (MediaRecorder.isTypeSupported("audio/mp4")) {
        options = { mimeType: "audio/mp4" };
      }

      const mediaRecorder = new MediaRecorder(stream, options);
      mediaRecorderRef.current = mediaRecorder;

      mediaRecorder.ondataavailable = (e) => {
        if (e.data && e.data.size > 0 && !isCancelledRef.current) {
          chunksRef.current.push(e.data);
        }
      };

      mediaRecorder.onstop = () => {
        if (isCancelledRef.current) {
          cleanupStream();
          return;
        }
        const mimeType = mediaRecorder.mimeType || "audio/webm";
        const blob = new Blob(chunksRef.current, { type: mimeType });
        if (onRecordingComplete) {
          onRecordingComplete(blob, mimeType);
        }
      };

      // Setup Web Audio API for volume/silence detection
      const audioContext = new (window.AudioContext || window.webkitAudioContext)();
      audioContextRef.current = audioContext;
      const source = audioContext.createMediaStreamSource(stream);
      const analyser = audioContext.createAnalyser();
      analyserRef.current = analyser;
      analyser.fftSize = 64;
      const bufferLength = analyser.frequencyBinCount;
      const dataArray = new Uint8Array(bufferLength);
      source.connect(analyser);

      // Volume visual scaling and silence detection loop
      const updateVisuals = () => {
        if (!analyserRef.current || !micAreaRef.current) return;
        analyserRef.current.getByteFrequencyData(dataArray);

        let sum = 0;
        for (let i = 0; i < bufferLength; i++) {
          sum += dataArray[i];
        }
        const average = sum / bufferLength;
        const volume = average / 255; // 0 to 1

        // Silence Detection (threshold 0.015, duration 2000ms)
        if (volume < 0.015) {
          if (!silenceStartRef.current) {
            silenceStartRef.current = Date.now();
          } else if (Date.now() - silenceStartRef.current > 2000) {
            if (!isSilent) {
              setIsSilent(true);
              if (onSilenceChange) onSilenceChange(true);
            }
          }
        } else {
          silenceStartRef.current = null;
          if (isSilent) {
            setIsSilent(false);
            if (onSilenceChange) onSilenceChange(false);
          }
        }

        // Pulse scale
        micAreaRef.current.style.setProperty("--volume-scale", `${1 + volume * 0.12}`);
        
        // Bars
        const frequencyIndices = [2, 6, 11, 17, 23];
        frequencyIndices.forEach((binIndex, barIndex) => {
          const bar = barsRef.current[barIndex];
          if (bar) {
            const val = dataArray[binIndex] || 0;
            const scale = 0.15 + (val / 255) * 0.85;
            bar.style.transform = `scaleY(${scale})`;
          }
        });

        animationFrameRef.current = requestAnimationFrame(updateVisuals);
      };

      mediaRecorder.start();
      setIsRecording(true);
      
      animationFrameRef.current = requestAnimationFrame(updateVisuals);

      // Start duration timer
      timerIntervalRef.current = setInterval(() => {
        setDuration(prev => prev + 1);
      }, 1000);

    } catch (err) {
      console.error("Microphone access failed: ", err);
      const permissionMsg = "Microphone permission denied.";
      setError(permissionMsg);
      if (onRecordingError) onRecordingError(permissionMsg);
    }
  };

  const stopRecording = () => {
    if (!isRecording) return;

    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== "inactive") {
      mediaRecorderRef.current.stop();
    }
    
    setIsRecording(false);
    
    if (timerIntervalRef.current) {
      clearInterval(timerIntervalRef.current);
      timerIntervalRef.current = null;
    }
    
    resetVisuals();
    cleanupStream();
  };

  const cancelRecording = () => {
    if (!isRecording) return;
    isCancelledRef.current = true;
    
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== "inactive") {
      mediaRecorderRef.current.stop();
    }

    setIsRecording(false);

    if (timerIntervalRef.current) {
      clearInterval(timerIntervalRef.current);
      timerIntervalRef.current = null;
    }

    setDuration(0);
    resetVisuals();
    cleanupStream();
  };

  const resetVisuals = () => {
    if (micAreaRef.current) {
      micAreaRef.current.style.setProperty("--volume-scale", "1");
    }
    barsRef.current.forEach(bar => {
      if (bar) bar.style.transform = "scaleY(0.15)";
    });
  };

  const getAccumulatedBlob = () => {
    if (!mediaRecorderRef.current || chunksRef.current.length === 0) return null;
    if (mediaRecorderRef.current.state === "recording") {
      mediaRecorderRef.current.requestData();
    }
    const mimeType = mediaRecorderRef.current.mimeType || "audio/webm";
    return new Blob(chunksRef.current, { type: mimeType });
  };

  const formatTimer = (secs) => {
    const mins = Math.floor(secs / 60);
    const remainingSecs = secs % 60;
    const pad = (num) => String(num).padStart(2, "0");
    return `${pad(mins)}:${pad(remainingSecs)}`;
  };

  const calculateSpeakingRate = () => {
    if (duration === 0) return 0;
    const rate = wordCount / (duration / 60);
    return Math.round(rate);
  };

  // Expose triggers to window
  useEffect(() => {
    window.startRecording = startRecording;
    window.stopRecording = stopRecording;
    window.cancelRecording = cancelRecording;
    window.isRecording = isRecording;
    window.getAccumulatedBlob = getAccumulatedBlob;
    return () => {
      delete window.startRecording;
      delete window.stopRecording;
      delete window.cancelRecording;
      delete window.isRecording;
      delete window.getAccumulatedBlob;
    };
  }, [isRecording, disabled, error, wordCount, duration]);

  return (
    <div className="recorder-container" aria-label="Microphone controller">
      {error && (
        <div className="error-banner" role="alert">
          <span>{error}</span>
        </div>
      )}

      {!error && (
        <div className="recorder-panel">
          <div className="voice-console">
            <div
              ref={micAreaRef}
              className={`mic-pulsing-area ${isRecording ? "recording" : "idle"}`}
            >
              <button
                type="button"
                className="mic-primary-btn"
                onClick={isRecording ? stopRecording : startRecording}
                disabled={disabled}
                aria-label={isRecording ? "Stop recording speech" : "Start recording speech"}
                title={isRecording ? "Stop Recording (Space)" : "Start Recording (Space)"}
              >
                {isRecording ? (
                  <Square className="mic-btn-icon stop-icon" />
                ) : (
                  <Mic className="mic-btn-icon play-icon" />
                )}
              </button>
              
              <div className="mic-glow-ring ring-1"></div>
              <div className="mic-glow-ring ring-2"></div>
            </div>

            <div className="voice-status-section">
              <p className="voice-state-label" aria-live="polite">
                {isRecording ? (isSilent ? "Listening..." : "Recording...") : "Ready"}
              </p>
              
              {isRecording ? (
                <p className="voice-timer" aria-label={`Recording duration: ${formatTimer(duration)}`}>
                  {formatTimer(duration)}
                </p>
              ) : (
                <div className="mic-shortcut-indicator">
                  <p className="voice-subprompt">Click microphone or press</p>
                  <kbd className="shortcut-kbd" aria-hidden="true">Space</kbd>
                </div>
              )}
            </div>
            
            {isRecording && (
              <>
                <div className="audio-visualizer" aria-hidden="true">
                  {[0, 1, 2, 3, 4].map(idx => (
                    <div
                      key={idx}
                      ref={el => barsRef.current[idx] = el}
                      className="visualizer-bar"
                      style={{ transform: "scaleY(0.15)" }}
                    ></div>
                  ))}
                </div>

                <div className="recorder-actions-row">
                  <button
                    type="button"
                    className="action-btn btn-cancel"
                    onClick={cancelRecording}
                    disabled={disabled}
                    aria-label="Cancel and discard recording"
                    title="Cancel Recording (Esc)"
                  >
                    <X className="btn-icon" />
                    <span>Cancel</span>
                    <kbd className="btn-shortcut-kbd">Esc</kbd>
                  </button>
                  <button
                    type="button"
                    className="action-btn btn-stop-rec"
                    onClick={stopRecording}
                    disabled={disabled}
                    aria-label="Stop and save recording"
                    title="Stop Recording (Space)"
                  >
                    <Square className="btn-icon" />
                    <span>Stop</span>
                    <kbd className="btn-shortcut-kbd">Space</kbd>
                  </button>
                </div>

                {/* Live Dictation Statistics Display */}
                <div className="live-statistics-panel fade-in">
                  <div className="live-stat-badge">
                    <Activity className="stat-icon" />
                    <span>Time: {formatTimer(duration)}</span>
                  </div>
                  <div className="live-stat-badge">
                    <MessageSquare className="stat-icon" />
                    <span>Words: {wordCount}</span>
                  </div>
                  <div className="live-stat-badge" title="Speaking speed rate in words per minute">
                    <Flame className="stat-icon" />
                    <span>Speed: {calculateSpeakingRate()} w/m</span>
                  </div>
                </div>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
