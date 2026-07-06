import React from "react";

export default function LoadingSpinner({ message }) {
  return (
    <div className="skeleton-workspace">
      {/* Live Progress Stage */}
      <div className="loading-badge-row">
        <div className="pulsing-pulse"></div>
        <p className="loading-stage-text">{message || "Processing..."}</p>
      </div>

      {/* Pulsing Document Skeleton */}
      <div className="skeleton-document">
        <div className="skeleton-header">
          <div className="skeleton-bar title-bar"></div>
          <div className="skeleton-actions">
            <div className="skeleton-circle"></div>
            <div className="skeleton-circle"></div>
            <div className="skeleton-circle"></div>
          </div>
        </div>
        
        <div className="skeleton-content">
          <div className="skeleton-bar line-bar line-1"></div>
          <div className="skeleton-bar line-bar line-2"></div>
          <div className="skeleton-bar line-bar line-3"></div>
        </div>
      </div>
    </div>
  );
}
