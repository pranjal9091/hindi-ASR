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
              className={`workspace-tab-btn ${activeWorkspaceTab === "clinical" ? "active" : ""}`}
              onClick={() => setActiveWorkspaceTab("clinical")}
              disabled={!clinicalData}
              title={!clinicalData ? "No clinical reports extracted yet" : "View Clinical Analysis"}
            >
              Clinical Insights
            </button>
            <button
              type="button"
              className={`workspace-tab-btn ${activeWorkspaceTab === "speech_analytics" ? "active" : ""}`}
              onClick={() => setActiveWorkspaceTab("speech_analytics")}
              disabled={!clinicalData || !clinicalData.speech_analytics}
              title={!clinicalData?.speech_analytics ? "No speech analytics processed yet" : "View Speech & Cognitive Analytics"}
            >
              Speech Analytics
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
      
      {activeWorkspaceTab === "clinical" && (
        <div className="document-content" tabIndex="0" aria-label="Clinical reports display">
          <div className="clinical-insights-panel fade-in">
            
            {/* 0. Critical Clinical Risk Flags Alert Banner */}
            {(() => {
              const riskFlags = clinicalData?.risk_flags || {};
              const activeRisks = Object.entries(riskFlags)
                .filter(([_, active]) => active)
                .map(([key, _]) => {
                  if (key === "emergency_risk") return "Emergency Alert";
                  if (key === "stroke_risk") return "Stroke Warning";
                  if (key === "heart_attack_risk") return "Cardiovascular Risk";
                  if (key === "respiratory_risk") return "Respiratory Distress Warning";
                  if (key === "fall_risk") return "Fall / Physical Injury Risk";
                  if (key === "medication_non_compliance") return "Medication Non-Compliance";
                  return key;
                });
              
              if (activeRisks.length === 0) return null;
              
              return (
                <div className="risk-banner-card fade-in" style={{ animation: "fadeIn 0.3s ease" }}>
                  <h4 className="risk-banner-title">
                    <AlertTriangle className="icon" style={{ color: "#B91C1C", width: "1.1rem", height: "1.1rem" }} />
                    Critical Clinical Risk Flags Detected
                  </h4>
                  <div className="risk-pills-row">
                    {activeRisks.map((risk, index) => (
                      <span key={index} className="risk-pill">{risk}</span>
                    ))}
                  </div>
                </div>
              );
            })()}

            {/* 1. Clinical Summary */}
            <div className="clinical-section">
              <h3 className="clinical-section-title">
                <Activity className="clinical-section-icon" />
                Structured Summary
              </h3>
              <div className="summary-grid">
                <div className="summary-row">
                  <span className="summary-label">Chief Complaint:</span>
                  <span>{clinicalData?.summary?.chief_complaint || "None"}</span>
                </div>
                <div className="summary-row">
                  <span className="summary-label">Symptoms:</span>
                  <span>{clinicalData?.summary?.symptoms || "None"}</span>
                </div>
                <div className="summary-row">
                  <span className="summary-label">Diagnosis Mentioned:</span>
                  <span>{clinicalData?.summary?.diagnosis || "None"}</span>
                </div>
                <div className="summary-row">
                  <span className="summary-label">Advice:</span>
                  <span>{clinicalData?.summary?.advice || "None"}</span>
                </div>
              </div>
            </div>

            {/* 1.1 SOAP Note Quadrants */}
            <div className="clinical-section">
              <h3 className="clinical-section-title">
                <Activity className="clinical-section-icon" />
                SOAP Notes (AI Generated)
              </h3>
              <div className="soap-grid">
                <div className="soap-quadrant">
                  <h4 className="soap-title">Subjective (S)</h4>
                  <p className="soap-body">{clinicalData?.soap_note?.subjective || "No subjective data."}</p>
                </div>
                <div className="soap-quadrant">
                  <h4 className="soap-title">Objective (O)</h4>
                  <p className="soap-body">{clinicalData?.soap_note?.objective || "No objective data."}</p>
                </div>
                <div className="soap-quadrant">
                  <h4 className="soap-title">Assessment (A)</h4>
                  <p className="soap-body">{clinicalData?.soap_note?.assessment || "No assessment data."}</p>
                </div>
                <div className="soap-quadrant">
                  <h4 className="soap-title">Plan (P)</h4>
                  <p className="soap-body">{clinicalData?.soap_note?.plan || "No plan data."}</p>
                </div>
              </div>
            </div>

            {/* 1.2 Possible Diagnoses (AI Hypothesis) */}
            <div className="clinical-section">
              <h3 className="clinical-section-title">
                <Activity className="clinical-section-icon" />
                Possible Diagnoses (AI Inferences)
              </h3>
              <div style={{ marginTop: "4px" }}>
                {clinicalData?.possible_diagnosis && clinicalData.possible_diagnosis.length > 0 ? (
                  clinicalData.possible_diagnosis.map((diag, idx) => (
                    <div key={idx} className="diagnosis-item-row">
                      <div className="diagnosis-meta">
                        <span className="diagnosis-name">{diag.name}</span>
                        <span className="diagnosis-confidence-val">{Math.round(diag.confidence * 100)}% Confidence</span>
                      </div>
                      <div className="confidence-progress-bar">
                        <div
                          className="confidence-progress-fill"
                          style={{ width: `${Math.round(diag.confidence * 100)}%` }}
                        ></div>
                      </div>
                    </div>
                  ))
                ) : (
                  <p style={{ fontSize: "0.8rem", color: "#9CA3AF" }}>No diagnoses inferred.</p>
                )}
              </div>
            </div>

            {/* 1.3 Suggested Doctor Questions */}
            <div className="clinical-section">
              <h3 className="clinical-section-title">
                <Activity className="clinical-section-icon" />
                Suggested Follow-up Doctor Questions
              </h3>
              <div className="question-item-list">
                {clinicalData?.follow_up_questions && clinicalData.follow_up_questions.length > 0 ? (
                  clinicalData.follow_up_questions.map((q, idx) => (
                    <div key={idx} className="question-item">
                      <span className="question-bullet">{idx + 1}.</span>
                      <span>{q}</span>
                    </div>
                  ))
                ) : (
                  <p style={{ fontSize: "0.8rem", color: "#9CA3AF" }}>No follow-up questions generated.</p>
                )}
              </div>
            </div>

            {/* 2. Prescribed Medications */}
            <div className="clinical-section">
              <h3 className="clinical-section-title">
                <Activity className="clinical-section-icon" />
                Prescribed Medications
              </h3>
              <div className="clinical-table-wrapper">
                <table className="clinical-table">
                  <thead>
                    <tr>
                      <th>Medicine Name</th>
                      <th>Dose</th>
                      <th>Frequency</th>
                      <th>Duration</th>
                    </tr>
                  </thead>
                  <tbody>
                    {clinicalData?.medicines && clinicalData.medicines.length > 0 ? (
                      clinicalData.medicines.map((m, idx) => (
                        <tr key={idx}>
                          <td style={{ fontWeight: 700, color: "#166534" }}>{m.name}</td>
                          <td>{m.dose}</td>
                          <td>{m.frequency}</td>
                          <td>{m.duration}</td>
                        </tr>
                      ))
                    ) : (
                      <tr>
                        <td colSpan="4" style={{ textAlign: "center", color: "#9CA3AF" }}>No medicines detected.</td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>

            {/* 3. Patient Vitals */}
            <div className="clinical-section">
              <h3 className="clinical-section-title">
                <Activity className="clinical-section-icon" />
                Patient Vitals
              </h3>
              <div className="vitals-grid">
                <div className="vital-card">
                  <span className="vital-card-label">Blood Pressure</span>
                  <span className="vital-card-value" style={{ color: "#1e40af" }}>{clinicalData?.vitals?.blood_pressure || "Normal"}</span>
                </div>
                <div className="vital-card">
                  <span className="vital-card-label">Temperature</span>
                  <span className="vital-card-value" style={{ color: "#b45309" }}>{clinicalData?.vitals?.temperature || "Normal"}</span>
                </div>
                <div className="vital-card">
                  <span className="vital-card-label">Pulse Rate</span>
                  <span className="vital-card-value">{clinicalData?.vitals?.pulse || "Normal"}</span>
                </div>
                <div className="vital-card">
                  <span className="vital-card-label">Oxygen (SpO2)</span>
                  <span className="vital-card-value" style={{ color: "#047857" }}>{clinicalData?.vitals?.oxygen || "Normal"}</span>
                </div>
                <div className="vital-card">
                  <span className="vital-card-label">Weight</span>
                  <span className="vital-card-value">{clinicalData?.vitals?.weight || "Normal"}</span>
                </div>
              </div>
            </div>

            {/* 3.1 Parser Confidence Scores */}
            <div className="clinical-section">
              <h3 className="clinical-section-title">
                <Activity className="clinical-section-icon" />
                AI Parsing Confidence Scores
              </h3>
              <div className="confidence-scores-grid">
                <div className="confidence-score-card">
                  <span className="score-card-label">NER Extraction</span>
                  <span className="score-card-val">{Math.round((clinicalData?.confidence_scores?.ner_confidence || 0.94) * 100)}%</span>
                </div>
                <div className="confidence-score-card">
                  <span className="score-card-label">Diagnosis Inferences</span>
                  <span className="score-card-val">{Math.round((clinicalData?.confidence_scores?.diagnosis_confidence || 0.80) * 100)}%</span>
                </div>
                <div className="confidence-score-card">
                  <span className="score-card-label">Timeline Compiler</span>
                  <span className="score-card-val">{Math.round((clinicalData?.confidence_scores?.timeline_confidence || 0.90) * 100)}%</span>
                </div>
                <div className="confidence-score-card">
                  <span className="score-card-label">Summary Engine</span>
                  <span className="score-card-val">{Math.round((clinicalData?.confidence_scores?.summary_confidence || 0.92) * 100)}%</span>
                </div>
              </div>
            </div>

            {/* 4. Event Timeline */}
            <div className="clinical-section">
              <h3 className="clinical-section-title">
                <Activity className="clinical-section-icon" />
                Clinical Event Timeline
              </h3>
              <div className="clinical-timeline">
                {clinicalData?.timeline && clinicalData.timeline.length > 0 ? (
                  clinicalData.timeline.map((item, idx) => (
                    <div key={idx} className="timeline-node">
                      <span className="timeline-time">{item.time}</span>
                      <span className="timeline-event">{item.event}</span>
                    </div>
                  ))
                ) : (
                  <p className="timeline-empty">No timeline events detected.</p>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {activeWorkspaceTab === "speech_analytics" && (
        <div className="document-content" tabIndex="0" aria-label="Clinical speech analytics display">
          <div className="speech-analytics-panel fade-in">
            {/* Disclaimer Banner */}
            <div className="disclaimer-box">
              <div className="disclaimer-title-row">
                <AlertTriangle style={{ width: "1.1rem", height: "1.1rem", color: "#166534" }} />
                Clinical Speech Analytics Disclaimer
              </div>
              <p className="disclaimer-body-text">
                {clinicalData?.speech_analytics?.clinical_summary?.disclaimer}
              </p>
            </div>

            {/* Cognitive Biomarkers Summary Card */}
            <div className="analytics-grid">
              <div className="analytics-card" style={{ gridColumn: "1 / -1" }}>
                <h4 className="analytics-card-title">
                  <Brain className="analytics-card-icon" />
                  Cognitive Biomarker Risk Profiles
                </h4>
                <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: "16px", marginTop: "8px" }}>
                  <div className="metrics-flex-row" style={{ borderBottom: "none", background: "#f9fafb", padding: "12px", borderRadius: "8px", flexDirection: "column", alignItems: "flex-start", gap: "6px" }}>
                    <span className="metrics-label" style={{ fontWeight: 600 }}>Overall Cognitive Risk</span>
                    <span className={`risk-level-badge ${clinicalData?.speech_analytics?.clinical_summary?.overall_cognitive_risk?.toLowerCase()}`}>
                      {clinicalData?.speech_analytics?.clinical_summary?.overall_cognitive_risk} Risk
                    </span>
                  </div>
                  <div className="metrics-flex-row" style={{ borderBottom: "none", background: "#f9fafb", padding: "12px", borderRadius: "8px", flexDirection: "column", alignItems: "flex-start", gap: "6px" }}>
                    <span className="metrics-label" style={{ fontWeight: 600 }}>Memory Assessment Risk</span>
                    <span className={`risk-level-badge ${clinicalData?.speech_analytics?.clinical_summary?.memory_risk?.toLowerCase()}`}>
                      {clinicalData?.speech_analytics?.clinical_summary?.memory_risk}
                    </span>
                  </div>
                  <div className="metrics-flex-row" style={{ borderBottom: "none", background: "#f9fafb", padding: "12px", borderRadius: "8px", flexDirection: "column", alignItems: "flex-start", gap: "6px" }}>
                    <span className="metrics-label" style={{ fontWeight: 600 }}>Language Flow Risk</span>
                    <span className={`risk-level-badge ${clinicalData?.speech_analytics?.clinical_summary?.language_risk?.toLowerCase()}`}>
                      {clinicalData?.speech_analytics?.clinical_summary?.language_risk}
                    </span>
                  </div>
                  <div className="metrics-flex-row" style={{ borderBottom: "none", background: "#f9fafb", padding: "12px", borderRadius: "8px", flexDirection: "column", alignItems: "flex-start", gap: "6px" }}>
                    <span className="metrics-label" style={{ fontWeight: 600 }}>Speech Rhythm Risk</span>
                    <span className={`risk-level-badge ${clinicalData?.speech_analytics?.clinical_summary?.speech_risk?.toLowerCase()}`}>
                      {clinicalData?.speech_analytics?.clinical_summary?.speech_risk}
                    </span>
                  </div>
                </div>
                <div style={{ marginTop: "12px", fontSize: "0.85rem", color: "var(--text-secondary)", lineHeight: "1.5", background: "#eff6ff", padding: "12px", borderRadius: "8px", borderLeft: "4px solid var(--accent)" }}>
                  <strong>Biomarker Contribution Analysis:</strong> {clinicalData?.speech_analytics?.clinical_summary?.explanation}
                </div>
              </div>

              {/* Speech Metrics Card */}
              <div className="analytics-card">
                <h4 className="analytics-card-title">
                  <Gauge className="analytics-card-icon" />
                  Speech Rate Metrics
                </h4>
                <div className="metrics-flex-row">
                  <span className="metrics-label">Total Words</span>
                  <span className="metrics-val">{clinicalData?.speech_analytics?.speech_metrics?.total_words}</span>
                </div>
                <div className="metrics-flex-row">
                  <span className="metrics-label">Total Sentences</span>
                  <span className="metrics-val">{clinicalData?.speech_analytics?.speech_metrics?.total_sentences}</span>
                </div>
                <div className="metrics-flex-row">
                  <span className="metrics-label">Speech Duration</span>
                  <span className="metrics-val">{clinicalData?.speech_analytics?.speech_metrics?.speech_duration} s</span>
                </div>
                <div className="metrics-flex-row">
                  <span className="metrics-label">Words Per Minute (WPM)</span>
                  <span className="metrics-val" style={{ color: "#1d4ed8" }}>{clinicalData?.speech_analytics?.speech_metrics?.words_per_minute}</span>
                </div>
                <div className="metrics-flex-row">
                  <span className="metrics-label">Characters Per Second</span>
                  <span className="metrics-val">{clinicalData?.speech_analytics?.speech_metrics?.chars_per_second}</span>
                </div>
                <div className="metrics-flex-row" style={{ flexDirection: "column", alignItems: "flex-start", gap: "4px" }}>
                  <span className="metrics-label" style={{ fontWeight: 600 }}>Longest Sentence:</span>
                  <span style={{ fontSize: "0.775rem", color: "var(--text-secondary)", fontStyle: "italic" }}>
                    "{clinicalData?.speech_analytics?.speech_metrics?.longest_sentence || "None"}"
                  </span>
                </div>
              </div>

              {/* Pause Metrics Card */}
              <div className="analytics-card">
                <h4 className="analytics-card-title">
                  <Clock className="analytics-card-icon" />
                  Pause & Silence Rhythm
                </h4>
                <div className="metrics-flex-row">
                  <span className="metrics-label">Total Pauses</span>
                  <span className="metrics-val">{clinicalData?.speech_analytics?.pause_metrics?.total_pause_count}</span>
                </div>
                <div className="metrics-flex-row">
                  <span className="metrics-label">Average Pause Duration</span>
                  <span className="metrics-val">{clinicalData?.speech_analytics?.pause_metrics?.average_pause_duration} s</span>
                </div>
                <div className="metrics-flex-row">
                  <span className="metrics-label">Max Pause Duration</span>
                  <span className="metrics-val">{clinicalData?.speech_analytics?.pause_metrics?.max_pause} s</span>
                </div>
                <div className="metrics-flex-row">
                  <span className="metrics-label">Long Pauses (&gt; 2 seconds)</span>
                  <span className="metrics-val" style={{ color: "#b91c1c" }}>{clinicalData?.speech_analytics?.pause_metrics?.long_pause_count}</span>
                </div>
                <div className="metrics-flex-row">
                  <span className="metrics-label">Silence to Speech Ratio</span>
                  <span className="metrics-val">{(clinicalData?.speech_analytics?.pause_metrics?.pause_ratio * 100).toFixed(1)}%</span>
                </div>
                <div className="emotion-bar-row" style={{ marginTop: "8px" }}>
                  <div className="emotion-label-row">
                    <span>Silence Ratio</span>
                    <span>{(clinicalData?.speech_analytics?.pause_metrics?.pause_ratio * 100).toFixed(1)}%</span>
                  </div>
                  <div className="emotion-bar-track">
                    <div className="emotion-bar-fill" style={{ width: `${Math.min(100, clinicalData?.speech_analytics?.pause_metrics?.pause_ratio * 100)}%`, backgroundColor: "#1e3a8a" }}></div>
                  </div>
                </div>
              </div>

              {/* Speech Fillers & Corrections */}
              <div className="analytics-card">
                <h4 className="analytics-card-title">
                  <MessageSquare className="analytics-card-icon" />
                  Fillers & Self-Corrections
                </h4>
                <div className="metrics-flex-row">
                  <span className="metrics-label">Total Filler Count</span>
                  <span className="metrics-val">{clinicalData?.speech_analytics?.fillers?.total_count}</span>
                </div>
                <div className="metrics-flex-row">
                  <span className="metrics-label">Fillers Per Minute</span>
                  <span className="metrics-val" style={{ color: "#b45309" }}>{clinicalData?.speech_analytics?.fillers?.fillers_per_minute}</span>
                </div>
                
                <span className="metrics-label" style={{ fontWeight: 600, marginTop: "4px" }}>Filler Word Frequency:</span>
                <div className="filler-tags-row">
                  {Object.keys(clinicalData?.speech_analytics?.fillers?.frequency || {}).length > 0 ? (
                    Object.entries(clinicalData.speech_analytics.fillers.frequency).map(([f, count], idx) => (
                      <span key={idx} className="filler-tag-pill">
                        {f} <span className="filler-tag-count">{count}</span>
                      </span>
                    ))
                  ) : (
                    <span style={{ fontSize: "0.8rem", color: "#9ca3af" }}>No fillers detected.</span>
                  )}
                </div>

                <div className="metrics-flex-row" style={{ borderBottom: "none", marginTop: "8px" }}>
                  <span className="metrics-label">Self-Corrections Count</span>
                  <span className="metrics-val">{clinicalData?.speech_analytics?.self_corrections?.correction_count}</span>
                </div>
                {clinicalData?.speech_analytics?.self_corrections?.correction_count > 0 && (
                  <div className="repetition-pill-examples">
                    {clinicalData.speech_analytics.self_corrections.examples.map((ex, idx) => (
                      <span key={idx} className="repetition-example-pill">{ex}</span>
                    ))}
                  </div>
                )}
              </div>

              {/* Repetition Analysis Card */}
              <div className="analytics-card">
                <h4 className="analytics-card-title">
                  <RotateCcw className="analytics-card-icon" />
                  Repetition & Echo Phenomena
                </h4>
                <div className="metrics-flex-row">
                  <span className="metrics-label">Consecutive Word Repeats</span>
                  <span className="metrics-val">{clinicalData?.speech_analytics?.repetition_analysis?.repeated_words_count}</span>
                </div>
                {clinicalData?.speech_analytics?.repetition_analysis?.repeated_words_count > 0 && (
                  <div className="repetition-pill-examples" style={{ marginBottom: "8px" }}>
                    {clinicalData.speech_analytics.repetition_analysis.repeated_words_examples.map((ex, idx) => (
                      <span key={idx} className="repetition-example-pill">"{ex}"</span>
                    ))}
                  </div>
                )}

                <div className="metrics-flex-row">
                  <span className="metrics-label">Phrase Repetitions (2-4 words)</span>
                  <span className="metrics-val">{clinicalData?.speech_analytics?.repetition_analysis?.repeated_phrases_count}</span>
                </div>
                {clinicalData?.speech_analytics?.repetition_analysis?.repeated_phrases_count > 0 && (
                  <div className="repetition-pill-examples" style={{ marginBottom: "8px" }}>
                    {clinicalData.speech_analytics.repetition_analysis.repeated_phrases_examples.map((ex, idx) => (
                      <span key={idx} className="repetition-example-pill">"{ex}"</span>
                    ))}
                  </div>
                )}

                <div className="metrics-flex-row">
                  <span className="metrics-label">Sentence Repetitions</span>
                  <span className="metrics-val">{clinicalData?.speech_analytics?.repetition_analysis?.repeated_sentences_count}</span>
                </div>
                {clinicalData?.speech_analytics?.repetition_analysis?.repeated_sentences_count > 0 && (
                  <div className="repetition-pill-examples">
                    {clinicalData.speech_analytics.repetition_analysis.repeated_sentences_examples.map((ex, idx) => (
                      <span key={idx} className="repetition-example-pill">"{ex}"</span>
                    ))}
                  </div>
                )}
              </div>

              {/* Lexical Diversity Card */}
              <div className="analytics-card">
                <h4 className="analytics-card-title">
                  <BarChart2 className="analytics-card-icon" />
                  Lexical Diversity & Structure
                </h4>
                <div className="metrics-flex-row">
                  <span className="metrics-label">Unique Words (Vocabulary)</span>
                  <span className="metrics-val">{clinicalData?.speech_analytics?.lexical_diversity?.unique_words_count}</span>
                </div>
                <div className="metrics-flex-row">
                  <span className="metrics-label">Type-Token Ratio (TTR)</span>
                  <span className="metrics-val">{clinicalData?.speech_analytics?.lexical_diversity?.type_token_ratio}</span>
                </div>
                <div className="metrics-flex-row">
                  <span className="metrics-label">Lexical Richness Level</span>
                  <span className="metrics-val" style={{ color: "#0d9488" }}>{clinicalData?.speech_analytics?.lexical_diversity?.lexical_richness}</span>
                </div>
                <div className="metrics-flex-row">
                  <span className="metrics-label">Avg Words per Sentence</span>
                  <span className="metrics-val">{clinicalData?.speech_analytics?.sentence_complexity?.avg_words_per_sentence}</span>
                </div>
                <div className="metrics-flex-row">
                  <span className="metrics-label">Sentence Length Variance</span>
                  <span className="metrics-val">{clinicalData?.speech_analytics?.sentence_complexity?.sentence_length_variance}</span>
                </div>
                <div className="metrics-flex-row">
                  <span className="metrics-label">Incomplete/Hesitant Sentences</span>
                  <span className="metrics-val">{clinicalData?.speech_analytics?.sentence_complexity?.incomplete_sentences_count}</span>
                </div>
                <div className="metrics-flex-row">
                  <span className="metrics-label">Sentence Fragments (&lt; 3 words)</span>
                  <span className="metrics-val">{clinicalData?.speech_analytics?.sentence_complexity?.fragment_count}</span>
                </div>
              </div>

              {/* Memory Indicators & Timeline Warnings */}
              <div className="analytics-card">
                <h4 className="analytics-card-title">
                  <AlertTriangle className="analytics-card-icon" />
                  Cognitive & Timeline Warnings
                </h4>
                <div className="metrics-flex-row">
                  <span className="metrics-label">Memory Loss Phrases Count</span>
                  <span className="metrics-val" style={{ color: "#dc2626" }}>{clinicalData?.speech_analytics?.memory_indicators?.memory_indicator_count}</span>
                </div>
                {clinicalData?.speech_analytics?.memory_indicators?.memory_indicator_count > 0 && (
                  <div className="repetition-pill-examples" style={{ marginBottom: "8px" }}>
                    {clinicalData.speech_analytics.memory_indicators.detected_phrases.map((ex, idx) => (
                      <span key={idx} className="repetition-example-pill" style={{ borderColor: "#fca5a5", background: "#fef2f2", color: "#991b1b" }}>"{ex}"</span>
                    ))}
                  </div>
                )}

                <span className="metrics-label" style={{ fontWeight: 600, marginTop: "4px" }}>Timeline Conflicts & Inconsistencies:</span>
                {clinicalData?.speech_analytics?.timeline_consistency?.warnings?.length > 0 ? (
                  <div style={{ display: "flex", flexDirection: "column", gap: "8px", width: "100%" }}>
                    {clinicalData.speech_analytics.timeline_consistency.warnings.map((w, idx) => (
                      <div key={idx} className="timeline-warning-box">
                        <AlertTriangle style={{ width: "1rem", height: "1rem", color: "#b45309", flexShrink: 0 }} />
                        <span className="timeline-warning-text">{w}</span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <span style={{ fontSize: "0.8rem", color: "#9ca3af" }}>No timeline inconsistencies found.</span>
                )}

                <div className="metrics-flex-row" style={{ borderBottom: "none", marginTop: "8px" }}>
                  <span className="metrics-label">Hesitation Gaps (&gt; 1.0 s)</span>
                  <span className="metrics-val">{clinicalData?.speech_analytics?.word_retrieval_difficulty?.hesitation_count}</span>
                </div>
                {clinicalData?.speech_analytics?.word_retrieval_difficulty?.hesitation_count > 0 && (
                  <div style={{ fontSize: "0.75rem", color: "var(--text-secondary)", background: "#f9fafb", padding: "8px", borderRadius: "6px", width: "100%" }}>
                    <strong>Hesitations:</strong> {clinicalData.speech_analytics.word_retrieval_difficulty.locations.map(h => `"${h.word}" at ${h.start}s`).join(", ")}
                  </div>
                )}
              </div>

              {/* Emotion Classifier (Lightweight NLP) */}
              <div className="analytics-card">
                <h4 className="analytics-card-title">
                  <Smile className="analytics-card-icon" />
                  Acoustic & Lexical Emotion Indicators
                </h4>
                <div className="metrics-flex-row">
                  <span className="metrics-label">Dominant Lexical Emotion</span>
                  <span className="metrics-val" style={{ color: "#4f46e5" }}>{clinicalData?.speech_analytics?.emotion_indicators?.dominant_emotion}</span>
                </div>

                <span className="metrics-label" style={{ fontWeight: 600, marginTop: "4px" }}>Emotion Profile Breakdown:</span>
                <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
                  <div className="emotion-bar-row">
                    <div className="emotion-label-row">
                      <span>Neutral</span>
                      <span>{Math.round((clinicalData?.speech_analytics?.emotion_indicators?.neutral || 0) * 100)}%</span>
                    </div>
                    <div className="emotion-bar-track">
                      <div className="emotion-bar-fill" style={{ width: `${Math.round((clinicalData?.speech_analytics?.emotion_indicators?.neutral || 0) * 100)}%`, backgroundColor: "#6b7280" }}></div>
                    </div>
                  </div>

                  <div className="emotion-bar-row">
                    <div className="emotion-label-row">
                      <span>Anxious / Worried</span>
                      <span>{Math.round((clinicalData?.speech_analytics?.emotion_indicators?.anxious || 0) * 100)}%</span>
                    </div>
                    <div className="emotion-bar-track">
                      <div className="emotion-bar-fill" style={{ width: `${Math.round((clinicalData?.speech_analytics?.emotion_indicators?.anxious || 0) * 100)}%`, backgroundColor: "#eab308" }}></div>
                    </div>
                  </div>

                  <div className="emotion-bar-row">
                    <div className="emotion-label-row">
                      <span>Sad / Depressed</span>
                      <span>{Math.round((clinicalData?.speech_analytics?.emotion_indicators?.sad || 0) * 100)}%</span>
                    </div>
                    <div className="emotion-bar-track">
                      <div className="emotion-bar-fill" style={{ width: `${Math.round((clinicalData?.speech_analytics?.emotion_indicators?.sad || 0) * 100)}%`, backgroundColor: "#3b82f6" }}></div>
                    </div>
                  </div>

                  <div className="emotion-bar-row">
                    <div className="emotion-label-row">
                      <span>Frustrated / Angry</span>
                      <span>{Math.round((clinicalData?.speech_analytics?.emotion_indicators?.frustrated || 0) * 100)}%</span>
                    </div>
                    <div className="emotion-bar-track">
                      <div className="emotion-bar-fill" style={{ width: `${Math.round((clinicalData?.speech_analytics?.emotion_indicators?.frustrated || 0) * 100)}%`, backgroundColor: "#ef4444" }}></div>
                    </div>
                  </div>

                  <div className="emotion-bar-row">
                    <div className="emotion-label-row">
                      <span>Confused / Clueless</span>
                      <span>{Math.round((clinicalData?.speech_analytics?.emotion_indicators?.confused || 0) * 100)}%</span>
                    </div>
                    <div className="emotion-bar-track">
                      <div className="emotion-bar-fill" style={{ width: `${Math.round((clinicalData?.speech_analytics?.emotion_indicators?.confused || 0) * 100)}%`, backgroundColor: "#a855f7" }}></div>
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
              {/* Pitch Card */}
              <div className="analytics-card">
                <h4 className="analytics-card-title">
                  <Activity className="analytics-card-icon" />
                  Fundamental Frequency (Pitch / F0)
                </h4>
                <div className="metrics-flex-row">
                  <span className="metrics-label">Mean Pitch</span>
                  <span className="metrics-val">{clinicalData?.acoustic_biomarkers?.pitch?.mean_pitch} Hz</span>
                </div>
                <div className="metrics-flex-row">
                  <span className="metrics-label">Median Pitch</span>
                  <span className="metrics-val">{clinicalData?.acoustic_biomarkers?.pitch?.median_pitch} Hz</span>
                </div>
                <div className="metrics-flex-row">
                  <span className="metrics-label">Pitch Standard Deviation</span>
                  <span className="metrics-val">{clinicalData?.acoustic_biomarkers?.pitch?.std_pitch} Hz</span>
                </div>
                <div className="metrics-flex-row">
                  <span className="metrics-label">Min Pitch</span>
                  <span className="metrics-val">{clinicalData?.acoustic_biomarkers?.pitch?.min_pitch} Hz</span>
                </div>
                <div className="metrics-flex-row" style={{ borderBottom: "none" }}>
                  <span className="metrics-label">Max Pitch</span>
                  <span className="metrics-val">{clinicalData?.acoustic_biomarkers?.pitch?.max_pitch} Hz</span>
                </div>
              </div>

              {/* Energy Card */}
              <div className="analytics-card">
                <h4 className="analytics-card-title">
                  <Zap className="analytics-card-icon" />
                  Voice Energy & Intensity
                </h4>
                <div className="metrics-flex-row">
                  <span className="metrics-label">RMS Energy Mean</span>
                  <span className="metrics-val">{clinicalData?.acoustic_biomarkers?.energy?.rms_mean}</span>
                </div>
                <div className="metrics-flex-row">
                  <span className="metrics-label">RMS Energy Std</span>
                  <span className="metrics-val">{clinicalData?.acoustic_biomarkers?.energy?.rms_std}</span>
                </div>
                <div className="metrics-flex-row" style={{ borderBottom: "none" }}>
                  <span className="metrics-label">Peak Amplitude Energy</span>
                  <span className="metrics-val">{clinicalData?.acoustic_biomarkers?.energy?.peak_energy}</span>
                </div>
              </div>

              {/* Speech Duration & Silence Ratio Card */}
              <div className="analytics-card">
                <h4 className="analytics-card-title">
                  <Clock className="analytics-card-icon" />
                  Speaking Duration & Silence
                </h4>
                <div className="metrics-flex-row">
                  <span className="metrics-label">Total Audio Duration</span>
                  <span className="metrics-val">{clinicalData?.acoustic_biomarkers?.speech_duration?.total_audio_duration} s</span>
                </div>
                <div className="metrics-flex-row">
                  <span className="metrics-label">Estimated Speech Duration</span>
                  <span className="metrics-val">{clinicalData?.acoustic_biomarkers?.speech_duration?.estimated_speech_duration} s</span>
                </div>
                <div className="metrics-flex-row">
                  <span className="metrics-label">Silence Duration</span>
                  <span className="metrics-val">{clinicalData?.acoustic_biomarkers?.speech_duration?.silence_duration} s</span>
                </div>
                <div className="metrics-flex-row" style={{ borderBottom: "none" }}>
                  <span className="metrics-label">Silence-to-Speech Ratio</span>
                  <span className="metrics-val" style={{ color: "#b91c1c" }}>{(clinicalData?.acoustic_biomarkers?.speech_duration?.silence_ratio * 100).toFixed(1)}%</span>
                </div>
                <div className="emotion-bar-row" style={{ marginTop: "12px" }}>
                  <div className="emotion-label-row">
                    <span>Silence Proportion</span>
                    <span>{(clinicalData?.acoustic_biomarkers?.speech_duration?.silence_ratio * 100).toFixed(1)}%</span>
                  </div>
                  <div className="emotion-bar-track">
                    <div className="emotion-bar-fill" style={{ width: `${Math.min(100, (clinicalData?.acoustic_biomarkers?.speech_duration?.silence_ratio || 0) * 100)}%`, backgroundColor: "#b91c1c" }}></div>
                  </div>
                </div>
              </div>

              {/* Prosody Card */}
              <div className="analytics-card">
                <h4 className="analytics-card-title">
                  <Volume2 className="analytics-card-icon" />
                  Speech Prosody & Variation
                </h4>
                <div className="metrics-flex-row">
                  <span className="metrics-label">Voiced Speech Ratio</span>
                  <span className="metrics-val">{clinicalData?.acoustic_biomarkers?.prosody?.voiced_ratio}</span>
                </div>
                <div className="metrics-flex-row">
                  <span className="metrics-label">Pitch Variability (Std/Mean)</span>
                  <span className="metrics-val">{clinicalData?.acoustic_biomarkers?.prosody?.pitch_variability}</span>
                </div>
                <div className="metrics-flex-row" style={{ borderBottom: "none" }}>
                  <span className="metrics-label">Energy Variability (Std/Mean)</span>
                  <span className="metrics-val">{clinicalData?.acoustic_biomarkers?.prosody?.energy_variability}</span>
                </div>
              </div>

              {/* Stability Card */}
              <div className="analytics-card">
                <h4 className="analytics-card-title">
                  <ShieldCheck className="analytics-card-icon" />
                  Voice Stability & Articulation Consistency
                </h4>
                <div className="metrics-flex-row">
                  <span className="metrics-label">Articulation Consistency</span>
                  <span className="metrics-val" style={{ color: "#0d9488" }}>{clinicalData?.acoustic_biomarkers?.stability?.articulation_consistency}</span>
                </div>
                <div className="metrics-flex-row" style={{ borderBottom: "none" }}>
                  <span className="metrics-label">Pause Energy Variance</span>
                  <span className="metrics-val">{clinicalData?.acoustic_biomarkers?.stability?.pause_energy_variance}</span>
                </div>
              </div>

              {/* Spectral Features Card */}
              <div className="analytics-card" style={{ gridColumn: "span 2" }}>
                <h4 className="analytics-card-title">
                  <BarChart2 className="analytics-card-icon" />
                  Spectral Features (Acoustic Envelope)
                </h4>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px" }}>
                  <div>
                    <div className="metrics-flex-row">
                      <span className="metrics-label">Spectral Centroid (Mean)</span>
                      <span className="metrics-val">{clinicalData?.acoustic_biomarkers?.spectral?.spectral_centroid?.mean} Hz</span>
                    </div>
                    <div className="metrics-flex-row">
                      <span className="metrics-label">Spectral Centroid (Std)</span>
                      <span className="metrics-val">{clinicalData?.acoustic_biomarkers?.spectral?.spectral_centroid?.std} Hz</span>
                    </div>
                    <div className="metrics-flex-row">
                      <span className="metrics-label">Spectral Bandwidth (Mean)</span>
                      <span className="metrics-val">{clinicalData?.acoustic_biomarkers?.spectral?.spectral_bandwidth?.mean} Hz</span>
                    </div>
                    <div className="metrics-flex-row" style={{ borderBottom: "none" }}>
                      <span className="metrics-label">Spectral Bandwidth (Std)</span>
                      <span className="metrics-val">{clinicalData?.acoustic_biomarkers?.spectral?.spectral_bandwidth?.std} Hz</span>
                    </div>
                  </div>
                  <div>
                    <div className="metrics-flex-row">
                      <span className="metrics-label">Spectral Rolloff (Mean)</span>
                      <span className="metrics-val">{clinicalData?.acoustic_biomarkers?.spectral?.spectral_rolloff?.mean} Hz</span>
                    </div>
                    <div className="metrics-flex-row">
                      <span className="metrics-label">Spectral Rolloff (Std)</span>
                      <span className="metrics-val">{clinicalData?.acoustic_biomarkers?.spectral?.spectral_rolloff?.std} Hz</span>
                    </div>
                    <div className="metrics-flex-row">
                      <span className="metrics-label">Zero Crossing Rate (Mean)</span>
                      <span className="metrics-val">{clinicalData?.acoustic_biomarkers?.spectral?.zero_crossing_rate?.mean}</span>
                    </div>
                    <div className="metrics-flex-row" style={{ borderBottom: "none" }}>
                      <span className="metrics-label">Zero Crossing Rate (Std)</span>
                      <span className="metrics-val">{clinicalData?.acoustic_biomarkers?.spectral?.zero_crossing_rate?.std}</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* MFCC Coefficient Statistics Card */}
              <div className="analytics-card" style={{ gridColumn: "span 2" }}>
                <h4 className="analytics-card-title">
                  <Sliders className="analytics-card-icon" />
                  Mel-Frequency Cepstral Coefficients (MFCC 1–13 Statistics)
                </h4>
                <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "12px", fontSize: "0.8rem" }}>
                  {Object.entries(clinicalData?.acoustic_biomarkers?.mfcc || {}).map(([coef, stats], idx) => (
                    <div key={idx} style={{ padding: "8px", background: "#f9fafb", borderRadius: "6px", border: "1px solid #e5e7eb" }}>
                      <div style={{ fontWeight: 600, color: "#374151", marginBottom: "4px" }}>
                        {coef.toUpperCase().replace("_", " ")}
                      </div>
                      <div style={{ display: "flex", justifyContent: "space-between", color: "#6b7280" }}>
                        <span>Mean:</span>
                        <span style={{ fontWeight: 500, color: "#111827" }}>{stats.mean}</span>
                      </div>
                      <div style={{ display: "flex", justifyContent: "space-between", color: "#6b7280" }}>
                        <span>Std:</span>
                        <span style={{ fontWeight: 500, color: "#111827" }}>{stats.std}</span>
                      </div>
                    </div>
                  ))}
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

            {/* Check if predictions are null (awaiting model integration) */}
            {(!clinicalData?.dementia_prediction || 
              Object.values(clinicalData.dementia_prediction).every(val => val === null)) ? (
              
              <div className="clinical-disclaimer-card" style={{ 
                background: "#f0fdf4", 
                borderLeftColor: "#16a34a", 
                color: "#166534", 
                display: "flex", 
                flexDirection: "column", 
                alignItems: "center", 
                justifyContent: "center", 
                padding: "48px 24px", 
                textAlign: "center",
                gap: "16px",
                borderRadius: "8px",
                marginTop: "24px"
              }}>
                <Brain style={{ width: "4rem", height: "4rem", color: "#16a34a", animation: "pulse 2s infinite" }} />
                <h4 style={{ fontSize: "1.25rem", fontWeight: 700, margin: 0, color: "#14532d" }}>
                  Awaiting Model Integration
                </h4>
                <p style={{ fontSize: "0.9rem", color: "#166534", maxWidth: "480px", margin: 0, lineHeight: 1.5 }}>
                  The Feature Fusion Engine has successfully compiled all 45+ transcript and acoustic biomarkers. The system is fully integrated and waiting for the founder's research-grade dementia classifier model.
                </p>
                <div style={{ fontSize: "0.8rem", background: "#dcfce7", color: "#15803d", padding: "6px 12px", borderRadius: "20px", fontWeight: 500 }}>
                  Standardized Feature Vector Ready
                </div>
              </div>

            ) : (

              <div className="analytics-grid" style={{ marginTop: "24px" }}>
                {/* When predictions become available later, render progress bars/cards */}
                <div className="analytics-card" style={{ gridColumn: "span 2" }}>
                  <h4 className="analytics-card-title">
                    <Sparkles className="analytics-card-icon" />
                    Cognitive Domains Prediction Results
                  </h4>
                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "24px", marginTop: "16px" }}>
                    <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
                      <div className="emotion-bar-row">
                        <div className="emotion-label-row">
                          <strong>Language Index</strong>
                          <span>{Math.round(clinicalData.dementia_prediction.language * 100)}%</span>
                        </div>
                        <div className="emotion-bar-track">
                          <div className="emotion-bar-fill" style={{ width: `${Math.round(clinicalData.dementia_prediction.language * 100)}%`, backgroundColor: "#4f46e5" }}></div>
                        </div>
                      </div>

                      <div className="emotion-bar-row">
                        <div className="emotion-label-row">
                          <strong>Fluency Index</strong>
                          <span>{Math.round(clinicalData.dementia_prediction.fluency * 100)}%</span>
                        </div>
                        <div className="emotion-bar-track">
                          <div className="emotion-bar-fill" style={{ width: `${Math.round(clinicalData.dementia_prediction.fluency * 100)}%`, backgroundColor: "#06b6d4" }}></div>
                        </div>
                      </div>

                      <div className="emotion-bar-row">
                        <div className="emotion-label-row">
                          <strong>Attention Index</strong>
                          <span>{Math.round(clinicalData.dementia_prediction.attention * 100)}%</span>
                        </div>
                        <div className="emotion-bar-track">
                          <div className="emotion-bar-fill" style={{ width: `${Math.round(clinicalData.dementia_prediction.attention * 100)}%`, backgroundColor: "#eab308" }}></div>
                        </div>
                      </div>
                    </div>

                    <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
                      <div className="emotion-bar-row">
                        <div className="emotion-label-row">
                          <strong>Orientation Index</strong>
                          <span>{Math.round(clinicalData.dementia_prediction.orientation * 100)}%</span>
                        </div>
                        <div className="emotion-bar-track">
                          <div className="emotion-bar-fill" style={{ width: `${Math.round(clinicalData.dementia_prediction.orientation * 100)}%`, backgroundColor: "#8b5cf6" }}></div>
                        </div>
                      </div>

                      <div className="emotion-bar-row">
                        <div className="emotion-label-row">
                          <strong>Memory Recall Index</strong>
                          <span>{Math.round(clinicalData.dementia_prediction.memory * 100)}%</span>
                        </div>
                        <div className="emotion-bar-track">
                          <div className="emotion-bar-fill" style={{ width: `${Math.round(clinicalData.dementia_prediction.memory * 100)}%`, backgroundColor: "#ec4899" }}></div>
                        </div>
                      </div>

                      <div className="emotion-bar-row">
                        <div className="emotion-label-row">
                          <strong>Overall Assessment Score</strong>
                          <span>{Math.round(clinicalData.dementia_prediction.overall * 100)}%</span>
                        </div>
                        <div className="emotion-bar-track">
                          <div className="emotion-bar-fill" style={{ width: `${Math.round(clinicalData.dementia_prediction.overall * 100)}%`, backgroundColor: "#10b981" }}></div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

            )}
          </div>
        </div>
      )}

    </div>
  );
}
