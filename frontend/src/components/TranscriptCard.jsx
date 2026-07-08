import React, { useState, useEffect, useRef } from "react";
import { Copy, Download, RotateCcw, Check, Sparkles, Search, Sliders, Activity, AlertTriangle, Brain, Clock, Smile, Gauge, MessageSquare, BarChart2, Zap, ShieldCheck, Volume2, Info } from "lucide-react";
import { exportToTXT, exportToPDF, exportToDOCX } from "../services/export";

export default function TranscriptCard({ 
  wordTimeline, 
  onClear, 
  copied, 
  isRecording,
  isFinished,
  clinicalData
}) {
  const [version, setVersion] = useState("edited"); // "original" or "edited"
  const [originalTimeline, setOriginalTimeline] = useState([]);
  const [editedTimeline, setEditedTimeline] = useState([]);
  
  // Undo/Redo stacks for edited timeline
  const [history, setHistory] = useState([[]]);
  const [historyIdx, setHistoryIdx] = useState(0);

  // Search & Config
  const [searchQuery, setSearchQuery] = useState("");
  const [confidenceThreshold, setConfidenceThreshold] = useState(0.80);
  const [showConfig, setShowConfig] = useState(false);

  // Workspace View Tabs: "transcript" vs "clinical"
  const [activeWorkspaceTab, setActiveWorkspaceTab] = useState("transcript");

  // Inline Word Editing
  const [editingIdx, setEditingIdx] = useState(-1);
  const [editText, setEditText] = useState("");
  const editInputRef = useRef(null);

  // Initialize and synchronize word timeline
  useEffect(() => {
    if (wordTimeline && wordTimeline.length > 0) {
      setOriginalTimeline(wordTimeline);
      setEditedTimeline(wordTimeline);
      setHistory([wordTimeline]);
      setHistoryIdx(0);
    } else {
      setOriginalTimeline([]);
      setEditedTimeline([]);
      setHistory([[]]);
      setHistoryIdx(0);
    }
  }, [wordTimeline]);

  // Global Undo / Redo keydowns
  useEffect(() => {
    const handleUndoRedo = (e) => {
      if (version !== "edited" || editingIdx !== -1) return;
      const isUndo = (e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "z" && !e.shiftKey;
      const isRedo = (e.ctrlKey || e.metaKey) && (e.key.toLowerCase() === "y" || (e.key.toLowerCase() === "z" && e.shiftKey));
      
      if (isUndo) {
        e.preventDefault();
        if (historyIdx > 0) {
          const nextIdx = historyIdx - 1;
          setHistoryIdx(nextIdx);
          setEditedTimeline(history[nextIdx]);
        }
      } else if (isRedo) {
        e.preventDefault();
        if (historyIdx < history.length - 1) {
          const nextIdx = historyIdx + 1;
          setHistoryIdx(nextIdx);
          setEditedTimeline(history[nextIdx]);
        }
      }
    };

    window.addEventListener("keydown", handleUndoRedo);
    return () => window.removeEventListener("keydown", handleUndoRedo);
  }, [version, history, historyIdx, editingIdx]);

  // Focus inline input on edit mode
  useEffect(() => {
    if (editingIdx !== -1 && editInputRef.current) {
      editInputRef.current.focus();
    }
  }, [editingIdx]);

  // Get active timeline list
  const activeTimeline = version === "original" ? originalTimeline : editedTimeline;

  // Group timeline flat words into paragraph lists based on >2.5s pauses
  const getParagraphs = (timeline) => {
    const paragraphs = [];
    let currentParagraph = [];
    
    timeline.forEach((word, idx) => {
      const prev = timeline[idx - 1];
      if (prev && (word.start - prev.end > 2.5)) {
        if (currentParagraph.length > 0) {
          paragraphs.push(currentParagraph);
        }
        currentParagraph = [word];
      } else {
        currentParagraph.push(word);
      }
    });
    
    if (currentParagraph.length > 0) {
      paragraphs.push(currentParagraph);
    }
    return paragraphs;
  };

  const paragraphs = getParagraphs(activeTimeline);

  // Build raw text copy representation (supporting paragraphs)
  const getRawTextRepresentation = () => {
    return paragraphs.map(para => para.map(w => w.text).join(" ")).join("\n\n");
  };

  const handleDoubleWordClick = (idx, wordText) => {
    if (version !== "edited" || isRecording) return;
    setEditingIdx(idx);
    setEditText(wordText);
  };

  const saveWordEdit = () => {
    if (editingIdx === -1) return;
    
    // Check if changed
    if (editedTimeline[editingIdx].text !== editText.trim()) {
      const updated = editedTimeline.map((w, i) => {
        if (i === editingIdx) {
          return { ...w, text: editText.trim() };
        }
        return w;
      });

      // Push history state
      const nextHistory = history.slice(0, historyIdx + 1);
      nextHistory.push(updated);
      setHistory(nextHistory);
      setHistoryIdx(nextHistory.length - 1);
      setEditedTimeline(updated);
    }

    setEditingIdx(-1);
    setEditText("");
  };

  const handleEditKeyDown = (e) => {
    if (e.key === "Enter") {
      saveWordEdit();
    } else if (e.key === "Escape") {
      setEditingIdx(-1);
      setEditText("");
    }
  };

  const handleExportSelect = (e) => {
    const format = e.target.value;
    if (!format) return;
    const text = getRawTextRepresentation();
    
    if (format === "txt") {
      exportToTXT(text);
    } else if (format === "pdf") {
      exportToPDF(text);
    } else if (format === "docx") {
      exportToDOCX(text);
    }
    
    e.target.value = ""; // Reset dropdown selection
  };

  // Compile helper sets for clinical keyword matching
  const medsSet = new Set((clinicalData?.medicines || []).map(m => m.name.toLowerCase()));
  const diseasesSet = new Set((clinicalData?.diseases || []).map(d => d.toLowerCase()));
  const symptomsSet = new Set((clinicalData?.symptoms || []).map(s => s.toLowerCase()));
  const proceduresSet = new Set((clinicalData?.procedures || []).map(p => p.toLowerCase()));
  const vitalKeywords = ["तापमान", "बुखार", "बीपी", "रक्तचाप", "वजन", "पल्स", "धड़कन", "ऑक्सीजन", "oxygen", "bp"];

  const getClinicalClass = (wordText) => {
    const clean = wordText.toLowerCase().replace(/[।?,.!]/g, "").trim();
    if (medsSet.has(clean)) return { className: "entity-medicine", type: "Medicine" };
    if (diseasesSet.has(clean)) return { className: "entity-disease", type: "Disease" };
    if (symptomsSet.has(clean)) return { className: "entity-disease", type: "Symptom" }; // symptomatic highlight
    if (proceduresSet.has(clean)) return { className: "entity-procedure", type: "Procedure" };
    if (vitalKeywords.some(k => clean.includes(k))) return { className: "entity-vital", type: "Vital Sign" };
    return null;
  };

  return (
    <div className="transcript-document" aria-label="Transcription workspace">
      {/* Notion Document Header */}
      <div className="document-header">
        <div className="document-header-left">
          {/* Workspace Switcher Tabs */}
          <div className="workspace-tabs-row">
            <button
              type="button"
              className={`workspace-tab-btn ${activeWorkspaceTab === "transcript" ? "active" : ""}`}
              onClick={() => setActiveWorkspaceTab("transcript")}
            >
              Transcript
            </button>
            <button
              type="button"
              className={`workspace-tab-btn ${activeWorkspaceTab === "speech_analytics" ? "active" : ""}`}
              onClick={() => setActiveWorkspaceTab("speech_analytics")}
              disabled={!clinicalData || !clinicalData.speech_analytics}
              title={!clinicalData?.speech_analytics ? "No speech biomarkers processed yet" : "View Speech Biomarkers"}
            >
              Speech Biomarkers
            </button>
            <button
              type="button"
              className={`workspace-tab-btn ${activeWorkspaceTab === "acoustic_biomarkers" ? "active" : ""}`}
              onClick={() => setActiveWorkspaceTab("acoustic_biomarkers")}
              disabled={!clinicalData || !clinicalData.acoustic_biomarkers}
              title={!clinicalData?.acoustic_biomarkers ? "No acoustic biomarkers processed yet" : "View Acoustic Speech Features"}
            >
              Acoustic Biomarkers
            </button>
            <button
              type="button"
              className={`workspace-tab-btn ${activeWorkspaceTab === "dementia_assessment" ? "active" : ""}`}
              onClick={() => setActiveWorkspaceTab("dementia_assessment")}
              disabled={!clinicalData || !clinicalData.dementia_prediction}
              title={!clinicalData?.dementia_prediction ? "No predictions processed yet" : "View Dementia Assessment"}
            >
              Dementia Assessment
            </button>
          </div>
          
          {isFinished && (
            <span className="completion-badge fade-in">
              <Sparkles className="badge-icon" />
              Clinical dictation processed
            </span>
          )}
        </div>
        
        <div className="document-actions">
          {/* Search bar input field */}
          <div className="document-search-box">
            <Search className="search-field-icon" />
            <input
              type="text"
              placeholder="Search transcript..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              aria-label="Search transcription words"
              className="search-field-input"
            />
          </div>

          {/* Config threshold slider toggle */}
          <button
            type="button"
            className={`action-icon-button ${showConfig ? "config-active" : ""}`}
            onClick={() => setShowConfig(!showConfig)}
            title="Configure Confidence Highlighter"
          >
            <Sliders className="icon" />
          </button>

          {/* Export Select Option Menu */}
          <div className="export-select-wrapper">
            <select
              className="export-dropdown-select"
              onChange={handleExportSelect}
              defaultValue=""
              aria-label="Export formats selection"
            >
              <option value="" disabled>Export</option>
              <option value="txt">TXT Plain text</option>
              <option value="pdf">PDF Document</option>
              <option value="docx">Word DOCX</option>
            </select>
          </div>

          <button
            type="button"
            className="action-icon-button danger-hover"
            onClick={onClear}
            title="Clear workspace (Esc)"
            aria-label="Clear workspace"
          >
            <RotateCcw className="icon" />
          </button>
        </div>
      </div>

      {/* Confidence threshold configurator panel */}
      {showConfig && (
        <div className="confidence-slider-bar fade-in">
          <label htmlFor="confidence-slider" className="slider-label">
            Highlight Confidence Under: <strong>{Math.round(confidenceThreshold * 100)}%</strong>
          </label>
          <input
            id="confidence-slider"
            type="range"
            min="0.0"
            max="1.0"
            step="0.05"
            value={confidenceThreshold}
            onChange={(e) => setConfidenceThreshold(parseFloat(e.target.value))}
            className="confidence-slider-input"
          />
        </div>
      )}
      
      {/* Dynamic Content Display */}
      {activeWorkspaceTab === "transcript" && (
        <div className="document-content" tabIndex="0" aria-label="Transcript content display">
          {/* Version Toggle Segment inside workspace body */}
          <div className="version-toggle-row" style={{ alignSelf: "flex-start", marginBottom: "16px", maxWidth: "120px" }}>
            <button
              type="button"
              className={`version-tab ${version === "edited" ? "active" : ""}`}
              onClick={() => setVersion("edited")}
            >
              Edited
            </button>
            <button
              type="button"
              className={`version-tab ${version === "original" ? "active" : ""}`}
              onClick={() => setVersion("original")}
            >
              Original
            </button>
          </div>

          <div className="hindi-text-display">
            {paragraphs.map((para, pIdx) => (
              <p key={pIdx} className="hindi-text-paragraph">
                {para.map((word) => {
                  const globalIdx = activeTimeline.indexOf(word);
                  const isMatch = searchQuery.trim() !== "" && word.text.toLowerCase().includes(searchQuery.toLowerCase());
                  const isLowConfidence = word.confidence < confidenceThreshold;
                  const clinicalHighlight = getClinicalClass(word.text);

                  if (globalIdx === editingIdx) {
                    return (
                      <input
                        key={globalIdx}
                        ref={editInputRef}
                        type="text"
                        className="inline-word-edit-input"
                        value={editText}
                        onChange={(e) => setEditText(e.target.value)}
                        onBlur={saveWordEdit}
                        onKeyDown={handleEditKeyDown}
                      />
                    );
                  }

                  // Determine class names
                  let wordClasses = "word-token animate-word";
                  let hoverTitle = isLowConfidence ? `Confidence: ${Math.round(word.confidence * 100)}%` : "";

                  if (isMatch) {
                    wordClasses += " search-match";
                  } else if (clinicalHighlight) {
                    wordClasses += ` ${clinicalHighlight.className}`;
                    hoverTitle = `[${clinicalHighlight.type}] ${hoverTitle}`;
                  } else if (isLowConfidence) {
                    wordClasses += " low-confidence-word";
                  }

                  if (version === "edited" && !isRecording) {
                    hoverTitle += " (Double-click to edit)";
                  }

                  return (
                    <span
                      key={globalIdx}
                      className={wordClasses}
                      onDoubleClick={() => handleDoubleWordClick(globalIdx, word.text)}
                      title={hoverTitle || undefined}
                      style={{ cursor: version === "edited" ? "pointer" : "default" }}
                    >
                      {word.text}{" "}
                    </span>
                  );
                })}
              </p>
            ))}
            
            {isRecording && (
              <span className="dictation-cursor" aria-hidden="true">|</span>
            )}
          </div>
        </div>
      )}
      


      {activeWorkspaceTab === "speech_analytics" && (
        <div className="workspace-tab-pane active fade-in" role="tabpanel" aria-label="Speech biomarkers view">
          <div className="document-content" tabIndex="0" aria-label="Speech biomarkers display">
            <div className="clinical-header-box">
              <div style={{ display: "flex", flexDirection: "column", gap: "2px" }}>
                <span className="clinical-meta-date">Transcript Biomarker Profiling</span>
                <h3 className="clinical-meta-id" style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                  Speech & Language Biomarkers
                </h3>
              </div>
              <span className="disclaimer-badge">
                Screening-Grade Features
              </span>
            </div>

            <div className="clinical-disclaimer-card" style={{ background: "#eff6ff", borderLeftColor: "#2563eb", color: "#1e3a8a", margin: "16px 0" }}>
              <Info style={{ width: "1.2rem", height: "1.2rem", flexShrink: 0, marginTop: "2px" }} />
              <div className="disclaimer-text" style={{ color: "#1e3a8a" }}>
                <strong>Biomarker Screening Disclaimer:</strong> These features represent objective, scientifically measurable properties derived from transcript and semantic analysis. They do not constitute a diagnosis and are designed for consumption by downstream machine learning assessment models.
              </div>
            </div>

            <div className="analytics-grid">
              <div className="analytics-card wide">
                <h4 className="analytics-card-title">
                  <Gauge className="analytics-card-icon" />
                  Speech & Language Biomarkers
                </h4>
                <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: "16px", marginTop: "12px" }}>
                  <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
                    <div className="metrics-flex-row">
                      <span className="metrics-label">Words Per Minute (WPM)</span>
                      <span className="metrics-val" style={{ fontWeight: 600, color: "#1e40af" }}>{clinicalData?.speech_analytics?.speech_fluency?.words_per_minute || 0}</span>
                    </div>
                    <div className="metrics-flex-row">
                      <span className="metrics-label">Articulation Rate</span>
                      <span className="metrics-val">{clinicalData?.speech_analytics?.speech_fluency?.articulation_rate || 0} words/min</span>
                    </div>
                    <div className="metrics-flex-row">
                      <span className="metrics-label">Total Pauses</span>
                      <span className="metrics-val">{clinicalData?.speech_analytics?.pause_metrics?.total_pause_count || 0}</span>
                    </div>
                    <div className="metrics-flex-row">
                      <span className="metrics-label">Long Pauses (&gt; 1 sec)</span>
                      <span className="metrics-val" style={{ color: "#b91c1c", fontWeight: 600 }}>{clinicalData?.speech_analytics?.pause_metrics?.significant_pauses_count || 0}</span>
                    </div>
                    <div className="metrics-flex-row">
                      <span className="metrics-label">Pause Ratio</span>
                      <span className="metrics-val">{((clinicalData?.speech_analytics?.pause_metrics?.pause_ratio || 0) * 100).toFixed(1)}%</span>
                    </div>
                  </div>

                  <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
                    <div className="metrics-flex-row">
                      <span className="metrics-label">Hesitation Count</span>
                      <span className="metrics-val">{clinicalData?.speech_analytics?.word_retrieval_difficulty?.hesitation_count || 0}</span>
                    </div>
                    <div className="metrics-flex-row">
                      <span className="metrics-label">Fillers Count</span>
                      <span className="metrics-val">{clinicalData?.speech_analytics?.fillers?.total_count || 0}</span>
                    </div>
                    <div className="metrics-flex-row">
                      <span className="metrics-label">Self Corrections</span>
                      <span className="metrics-val">{clinicalData?.speech_analytics?.self_corrections?.correction_count || 0}</span>
                    </div>
                    <div className="metrics-flex-row">
                      <span className="metrics-label">Repetition Count</span>
                      <span className="metrics-val">{clinicalData?.speech_analytics?.repetition_analysis?.total_repetition_count || 0}</span>
                    </div>
                    <div className="metrics-flex-row">
                      <span className="metrics-label">Word Retrieval Difficulty Count</span>
                      <span className="metrics-val" style={{ color: "#b45309", fontWeight: 600 }}>{clinicalData?.speech_analytics?.memory_indicators?.recall_difficulty_indicators_count || 0}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {activeWorkspaceTab === "acoustic_biomarkers" && (
        <div className="workspace-tab-pane active fade-in" role="tabpanel" aria-label="Acoustic biomarkers view">
          <div className="document-content" tabIndex="0" aria-label="Acoustic biomarkers display">
            <div className="clinical-header-box">
              <div style={{ display: "flex", flexDirection: "column", gap: "2px" }}>
                <span className="clinical-meta-date">Acoustic Biomarker Profiling</span>
                <h3 className="clinical-meta-id" style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                  Acoustic Speech Intelligence
                </h3>
              </div>
              <span className="disclaimer-badge">
                Research-Grade Features
              </span>
            </div>

            <div className="clinical-disclaimer-card" style={{ background: "#eff6ff", borderLeftColor: "#2563eb", color: "#1e3a8a" }}>
              <Info style={{ width: "1.2rem", height: "1.2rem", flexShrink: 0, marginTop: "2px" }} />
              <div className="disclaimer-text" style={{ color: "#1e3a8a" }}>
                <strong>Acoustic Screening Disclaimer:</strong> These features represent objective, low-level acoustic properties extracted directly from raw audio signal processing (pitch, energy, spectral, and cepstral features). They do not constitute a diagnosis and are designed for consumption by downstream machine learning assessment models.
              </div>
            </div>

            <div className="analytics-grid">
              <div className="analytics-card wide">
                <h4 className="analytics-card-title">
                  <Volume2 className="analytics-card-icon" />
                  Acoustic Speech Biomarkers
                </h4>
                <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: "16px", marginTop: "12px" }}>
                  <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
                    <div className="metrics-flex-row">
                      <span className="metrics-label">Mean Pitch</span>
                      <span className="metrics-val" style={{ fontWeight: 600, color: "#1e40af" }}>{clinicalData?.acoustic_biomarkers?.pitch?.mean_pitch || 0} Hz</span>
                    </div>
                    <div className="metrics-flex-row">
                      <span className="metrics-label">Pitch Variability</span>
                      <span className="metrics-val">{clinicalData?.acoustic_biomarkers?.prosody?.pitch_variability || 0}</span>
                    </div>
                    <div className="metrics-flex-row">
                      <span className="metrics-label">RMS Energy</span>
                      <span className="metrics-val">{clinicalData?.acoustic_biomarkers?.energy?.rms_mean || 0}</span>
                    </div>
                  </div>

                  <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
                    <div className="metrics-flex-row">
                      <span className="metrics-label">Silence Ratio</span>
                      <span className="metrics-val" style={{ color: "#b91c1c", fontWeight: 600 }}>{((clinicalData?.acoustic_biomarkers?.speech_duration?.silence_ratio || 0) * 100).toFixed(1)}%</span>
                    </div>
                    <div className="metrics-flex-row">
                      <span className="metrics-label">Voiced Ratio</span>
                      <span className="metrics-val">{clinicalData?.acoustic_biomarkers?.prosody?.voiced_ratio || 0}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {activeWorkspaceTab === "dementia_assessment" && (
        <div className="workspace-tab-pane active fade-in" role="tabpanel" aria-label="Dementia assessment predictions view">
          <div className="document-content" tabIndex="0" aria-label="Dementia assessment display">
            <div className="clinical-header-box">
              <div style={{ display: "flex", flexDirection: "column", gap: "2px" }}>
                <span className="clinical-meta-date">Model Classification Interface</span>
                <h3 className="clinical-meta-id" style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                  Dementia Cognitive Domain Assessment
                </h3>
              </div>
              <span className="disclaimer-badge">
                Prediction Platform
              </span>
            </div>

            <div className="clinical-disclaimer-card" style={{ 
              background: "#f0fdf4", 
              borderLeftColor: "#16a34a", 
              color: "#166534", 
              display: "flex", 
              flexDirection: "column", 
              alignItems: "center", 
              justifyContent: "center", 
              padding: "40px 24px", 
              textAlign: "center",
              gap: "12px",
              borderRadius: "8px",
              marginTop: "24px"
            }}>
              <Brain style={{ width: "3.5rem", height: "3.5rem", color: "#16a34a", animation: "pulse 2s infinite" }} />
              <h4 style={{ fontSize: "1.25rem", fontWeight: 700, margin: 0, color: "#14532d" }}>
                Awaiting Dementia Model
              </h4>
              <p style={{ fontSize: "0.875rem", color: "#166534", maxWidth: "480px", margin: 0, lineHeight: 1.5 }}>
                The feature vector has been compiled and is ready for model evaluation.
              </p>
            </div>

            <div className="analytics-grid" style={{ marginTop: "24px" }}>
              {["Language", "Fluency", "Attention", "Orientation", "Memory"].map((domain) => (
                <div key={domain} className="analytics-card" style={{ display: "flex", flexDirection: "column", justifyContent: "space-between", height: "100px", padding: "16px" }}>
                  <h5 style={{ margin: 0, fontSize: "0.9rem", fontWeight: 600, color: "var(--text-primary)" }}>{domain}</h5>
                  <span style={{ fontSize: "0.8rem", color: "var(--text-secondary)", fontStyle: "italic" }}>Waiting for model...</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

    </div>
  );
}
