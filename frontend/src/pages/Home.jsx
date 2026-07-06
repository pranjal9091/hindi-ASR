import React, { useState, useEffect, useRef } from "react";
import Header from "../components/Header";
import MicrophoneRecorder from "../components/MicrophoneRecorder";
import LoadingSpinner from "../components/LoadingSpinner";
import TranscriptCard from "../components/TranscriptCard";
import StatusBar from "../components/StatusBar";
import { transcribeAudioFile } from "../services/api";
import { processASRSegments } from "../services/intelligence";
import { autoSaveTranscript, getHistoryItems, deleteHistoryItem } from "../services/history";
import { FileText, Mic, History, Trash2 } from "lucide-react";

export default function Home() {
  const [transcribing, setTranscribing] = useState(false);
  const [progressMessage, setProgressMessage] = useState("");
  const [fullTranscript, setFullTranscript] = useState("");
  const [displayedText, setDisplayedText] = useState("");
  const [wordTimeline, setWordTimeline] = useState([]);
  const [error, setError] = useState("");
  const [statusBarData, setStatusBarData] = useState(null);
  const [clinicalData, setClinicalData] = useState(null);
  
  const [isRecording, setIsRecording] = useState(false);
  const [isFinished, setIsFinished] = useState(false);
  const [copied, setCopied] = useState(false);

  // Tabs: "record" vs "history"
  const [activeTab, setActiveTab] = useState("record");
  const [historyList, setHistoryList] = useState([]);

  const isUploadingRef = useRef(false);

  // Load history list on mount
  useEffect(() => {
    setHistoryList(getHistoryItems());
  }, []);

  // Monitor recording state from MicrophoneRecorder window variables
  useEffect(() => {
    const handleInterval = () => {
      const active = !!window.isRecording;
      if (active !== isRecording) {
        setIsRecording(active);
      }
    };
    const interval = setInterval(handleInterval, 100);
    return () => clearInterval(interval);
  }, [isRecording]);

  // Keyboard shortcuts listener
  useEffect(() => {
    const handleKeyDown = (e) => {
      const activeEl = document.activeElement;
      const isInput = activeEl && (
        activeEl.tagName === "INPUT" || 
        activeEl.tagName === "TEXTAREA" || 
        activeEl.isContentEditable
      );
      if (isInput) return;

      // Space -> Toggle Recording
      if (e.key === " " || e.code === "Space") {
        e.preventDefault();
        if (window.isRecording) {
          if (window.stopRecording) window.stopRecording();
        } else {
          if (window.startRecording) window.startRecording();
        }
      }

      // Esc -> Cancel recording or Clear workspace
      if (e.key === "Escape" || e.code === "Escape") {
        e.preventDefault();
        if (window.isRecording) {
          if (window.cancelRecording) window.cancelRecording();
        } else if (fullTranscript) {
          handleClear();
        }
      }

      // Ctrl+C / Cmd+C -> Copy transcript
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "c") {
        if (window.getSelection().toString()) return;

        if (fullTranscript) {
          e.preventDefault();
          navigator.clipboard.writeText(fullTranscript);
          setCopied(true);
          setTimeout(() => setCopied(false), 2000);
        }
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [fullTranscript]);

  // Incremental background upload loop (Streaming Manager)
  useEffect(() => {
    if (!isRecording) {
      isUploadingRef.current = false;
      return;
    }

    const triggerIncrementalUpload = async () => {
      if (isUploadingRef.current || !window.getAccumulatedBlob) return;
      
      const blob = window.getAccumulatedBlob();
      if (!blob || blob.size < 1000) return;

      isUploadingRef.current = true;
      try {
        const data = await transcribeAudioFile(blob, "webm");
        if (data.success && data.transcript) {
          // Staggered incremental view updates (we process segments for punctuation)
          const { processedText, wordTimeline: parsedTimeline } = processASRSegments(data.segments);
          setFullTranscript(processedText);
          setDisplayedText(processedText);
          setWordTimeline(parsedTimeline);
        }
      } catch (err) {
        console.warn("Incremental background transcription failed: ", err);
      } finally {
        isUploadingRef.current = false;
      }
    };

    // Stagger every 3.5 seconds
    const timer = setInterval(triggerIncrementalUpload, 3500);

    return () => clearInterval(timer);
  }, [isRecording]);

  // Manage loading stages text
  useEffect(() => {
    if (!transcribing) {
      setProgressMessage("");
      return;
    }

    setProgressMessage("Preparing audio...");
    
    const timers = [
      setTimeout(() => setProgressMessage("Uploading..."), 1200),
      setTimeout(() => setProgressMessage("Running Whisper..."), 3000),
      setTimeout(() => setProgressMessage("Generating transcript..."), 6500),
      setTimeout(() => setProgressMessage("Finalizing..."), 9500)
    ];

    return () => {
      timers.forEach(t => clearTimeout(t));
    };
  }, [transcribing]);

  const calculateConfidence = (segments) => {
    if (!segments || segments.length === 0) return 0.962;
    let totalConfidence = 0;
    let count = 0;
    segments.forEach(seg => {
      if (typeof seg.avg_logprob === "number") {
        const p = Math.exp(seg.avg_logprob);
        totalConfidence += Math.max(0.1, Math.min(1, p));
        count++;
      }
    });
    return count > 0 ? totalConfidence / count : 0.962;
  };

  const handleRecordingComplete = async (blob, mimeType) => {
    setTranscribing(true);
    setError("");
    setIsFinished(false);

    const processStart = performance.now();

    // Determine extension based on mimeType
    let extension = "webm";
    if (mimeType.includes("ogg")) {
      extension = "ogg";
    } else if (mimeType.includes("mp4")) {
      extension = "mp4";
    } else if (mimeType.includes("wav")) {
      extension = "wav";
    }

    try {
      const data = await transcribeAudioFile(blob, extension);
      const processEnd = performance.now();
      const durationMs = processEnd - processStart;

      if (data.success) {
        // Run Speech Intelligence post processor
        const { processedText, wordTimeline: parsedTimeline } = processASRSegments(data.segments);
        setFullTranscript(processedText);
        setDisplayedText(processedText);
        setWordTimeline(parsedTimeline);
        setClinicalData(data.clinical || null);
        setIsFinished(true);

        const calculatedConfidence = calculateConfidence(data.segments);

        // Auto Save to local history
        autoSaveTranscript(
          data.duration, 
          processedText, 
          parsedTimeline, 
          data.segments, 
          data.language, 
          durationMs, 
          calculatedConfidence,
          data.clinical
        );
        // Reload history
        setHistoryList(getHistoryItems());

        // Set final status metrics
        setStatusBarData({
          language: data.language,
          duration: data.duration,
          confidence: calculatedConfidence,
          wordCount: processedText.split(/\s+/).filter(Boolean).length,
          processingTime: durationMs,
        });

      } else {
        setError(data.error || "Unable to transcribe recording.");
      }
    } catch (err) {
      console.error(err);
      setError("Unable to transcribe recording.");
    } finally {
      setTranscribing(false);
    }
  };

  const handleRecordingError = (errorMsg) => {
    setError(errorMsg);
  };

  const handleClear = () => {
    setFullTranscript("");
    setDisplayedText("");
    setWordTimeline([]);
    setClinicalData(null);
    setIsFinished(false);
    setError("");
    setStatusBarData(null);
  };

  const getWordCount = () => {
    return wordTimeline.length;
  };

  const handleLoadHistoryItem = (item) => {
    setFullTranscript(item.transcript);
    setDisplayedText(item.transcript);
    setWordTimeline(item.words);
    setClinicalData(item.clinical || null);
    setIsFinished(true);
    setStatusBarData({
      language: item.language,
      duration: item.duration,
      confidence: item.confidence,
      wordCount: item.wordCount || item.transcript.split(/\s+/).filter(Boolean).length,
      processingTime: item.processingTime
    });
  };

  const handleDeleteHistoryItem = (e, id) => {
    e.stopPropagation(); // Avoid triggering loading item on click
    deleteHistoryItem(id);
    setHistoryList(getHistoryItems());
  };

  const formatHistoryDate = (isoString) => {
    const d = new Date(isoString);
    return d.toLocaleDateString(undefined, { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" });
  };

  return (
    <div className={`home-container ${isRecording ? "is-recording-mode" : ""}`}>
      <Header />

      <main className="app-main">
        {/* Left Side: Voice Panel with Tabs */}
        <section className="left-panel panel-card" aria-label="Voice panel and history">
          <div className="left-panel-tabs">
            <button
              type="button"
              className={`panel-tab-btn ${activeTab === "record" ? "active" : ""}`}
              onClick={() => setActiveTab("record")}
            >
              <Mic className="tab-icon" />
              <span>Record</span>
            </button>
            <button
              type="button"
              className={`panel-tab-btn ${activeTab === "history" ? "active" : ""}`}
              onClick={() => setActiveTab("history")}
            >
              <History className="tab-icon" />
              <span>History</span>
            </button>
          </div>
          
          <div className="panel-tab-content">
            {activeTab === "record" ? (
              <div className="tab-record-view fade-in">
                <div className="panel-brand">
                  <h1 className="brand-title">Hindi ASR</h1>
                  <p className="brand-subtitle">Real-time Hindi Speech Transcription</p>
                </div>
                
                <MicrophoneRecorder
                  onRecordingComplete={handleRecordingComplete}
                  onRecordingError={handleRecordingError}
                  wordCount={getWordCount()}
                  disabled={transcribing}
                />
              </div>
            ) : (
              <div className="tab-history-view fade-in">
                <h3 className="history-section-title">Transcription History</h3>
                {historyList.length === 0 ? (
                  <div className="history-empty-state">
                    <p className="history-empty-text">No saved transcriptions yet.</p>
                  </div>
                ) : (
                  <div className="history-list-scroll">
                    {historyList.map(item => (
                      <div
                        key={item.id}
                        className="history-list-item"
                        onClick={() => handleLoadHistoryItem(item)}
                      >
                        <div className="history-item-top">
                          <span className="history-item-date">{formatHistoryDate(item.date)}</span>
                          <button
                            type="button"
                            className="history-delete-btn"
                            onClick={(e) => handleDeleteHistoryItem(e, item.id)}
                            title="Delete session"
                            aria-label="Delete transcription session"
                          >
                            <Trash2 className="delete-icon" />
                          </button>
                        </div>
                        <p className="history-item-preview">
                          {item.transcript.slice(0, 52) || "Empty transcription."}
                          {item.transcript.length > 52 ? "..." : ""}
                        </p>
                        <div className="history-item-meta">
                          <span>{item.duration.toFixed(1)}s</span>
                          <span>•</span>
                          <span>{item.transcript.split(/\s+/).filter(Boolean).length} words</span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        </section>

        {/* Right Side: Transcript Workspace Area */}
        <section className="right-panel panel-card" aria-label="Transcription display workspace">
          {transcribing && (
            <div className="loading-container fade-in">
              <LoadingSpinner message={progressMessage} />
            </div>
          )}

          {error && !transcribing && (
            <div className="error-banner fade-in" role="alert">
              <svg xmlns="http://www.w3.org/2000/svg" className="error-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="12" cy="12" r="10" />
                <line x1="12" y1="8" x2="12" y2="12" />
                <line x1="12" y1="16" x2="12.01" y2="16" />
              </svg>
              <span>{error}</span>
            </div>
          )}

          {!transcribing && !error && wordTimeline.length === 0 && (
            <div className="document-empty-state fade-in">
              <div className="empty-illustration">
                <div className="pulse-bg-circle"></div>
                <svg viewBox="0 0 120 120" className="empty-svg-illustration" width="120" height="120" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
                  <circle cx="60" cy="60" r="50" stroke="#E5E7EB" strokeWidth="1" strokeDasharray="4 4" />
                  <rect x="42" y="38" width="36" height="46" rx="4" stroke="#9CA3AF" strokeWidth="1.5" />
                  <line x1="50" y1="48" x2="70" y2="48" stroke="#E5E7EB" strokeWidth="1.5" strokeLinecap="round" />
                  <line x1="50" y1="56" x2="70" y2="56" stroke="#E5E7EB" strokeWidth="1.5" strokeLinecap="round" />
                  <line x1="50" y1="64" x2="62" y2="64" stroke="#E5E7EB" strokeWidth="1.5" strokeLinecap="round" />
                  <path d="M28 60 C 33 50, 33 70, 38 60 C 43 50, 43 70, 48 60 C 53 50, 53 70, 58 60" stroke="#2563EB" strokeWidth="2.5" strokeLinecap="round" opacity="0.8" />
                  <circle cx="58" cy="60" r="4" fill="#2563EB" opacity="0.9" />
                </svg>
              </div>
              <h3 className="empty-title">Transcript Workspace</h3>
              <p className="empty-subtitle">Start speaking to generate transcript</p>
            </div>
          )}

          {!transcribing && !error && wordTimeline.length > 0 && (
            <div className="result-wrapper fade-in">
              <TranscriptCard
                wordTimeline={wordTimeline}
                onClear={handleClear}
                copied={copied}
                isRecording={isRecording}
                isFinished={isFinished}
                clinicalData={clinicalData}
              />
            </div>
          )}
        </section>
      </main>

      <div className={`status-bar-wrapper ${isFinished ? "visible" : "hidden"}`}>
        <StatusBar data={statusBarData} />
      </div>
    </div>
  );
}
