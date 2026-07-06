import React from "react";
import { Globe, Clock, Percent, FileText, Cpu } from "lucide-react";

export default function StatusBar({ data }) {
  const getLanguageName = (code) => {
    if (!code) return "—";
    return code === "hi" ? "Hindi" : code.toUpperCase();
  };

  const formatSeconds = (sec) => {
    if (sec === undefined || sec === null) return "—";
    return `${Number(sec).toFixed(1)}s`;
  };

  const formatConfidence = (val) => {
    if (val === undefined || val === null) return "—";
    return `${(Number(val) * 100).toFixed(1)}%`;
  };

  const formatCount = (count) => {
    if (count === undefined || count === null) return "—";
    return count;
  };

  const formatProcessingTime = (ms) => {
    if (ms === undefined || ms === null) return "—";
    return `${(ms / 1000).toFixed(2)}s`;
  };

  return (
    <div className="bottom-status-bar">
      <div className="status-pill" title="Language">
        <Globe className="pill-icon" />
        <span className="pill-label">Lang:</span>
        <span className="pill-value">{getLanguageName(data?.language)}</span>
      </div>

      <div className="status-pill" title="Audio Duration">
        <Clock className="pill-icon" />
        <span className="pill-label">Duration:</span>
        <span className="pill-value">{formatSeconds(data?.duration)}</span>
      </div>

      <div className="status-pill" title="ASR Confidence">
        <Percent className="pill-icon" />
        <span className="pill-label">Confidence:</span>
        <span className="pill-value">{formatConfidence(data?.confidence)}</span>
      </div>

      <div className="status-pill" title="Word Count">
        <FileText className="pill-icon" />
        <span className="pill-label">Words:</span>
        <span className="pill-value">{formatCount(data?.wordCount)}</span>
      </div>

      <div className="status-pill" title="Server Processing Time">
        <Cpu className="pill-icon" />
        <span className="pill-label">CPU:</span>
        <span className="pill-value">{formatProcessingTime(data?.processingTime)}</span>
      </div>
    </div>
  );
}
