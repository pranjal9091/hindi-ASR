import React, { useState, useEffect, useRef } from "react";
import { Copy, Download, RotateCcw, Check, Sparkles, Search, Sliders, Activity, AlertTriangle } from "lucide-react";
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
          <div className="workspace-tabs-row" style={{ borderBottom: "none", marginBottom: 0 }}>
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
      {activeWorkspaceTab === "transcript" ? (
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
      ) : (
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
    </div>
  );
}
