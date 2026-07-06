import React, { useState, useEffect } from "react";
import { AudioLines } from "lucide-react";
import { BACKEND_URL } from "../config";

export default function Header() {
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    const checkConnection = async () => {
      try {
        // Ping backend using a fast HEAD request
        const res = await fetch(BACKEND_URL + "/docs", { method: "HEAD" });
        if (res.ok || res.status === 200) {
          setConnected(true);
        } else {
          setConnected(false);
        }
      } catch (err) {
        setConnected(false);
      }
    };

    checkConnection();
    const interval = setInterval(checkConnection, 5000);

    return () => clearInterval(interval);
  }, []);

  return (
    <header className="main-header">
      <div className="header-logo">
        <AudioLines className="logo-icon" />
        <span className="logo-text">Hindi ASR</span>
      </div>
      
      <div className="header-status">
        <span className={`status-dot ${connected ? "connected" : "disconnected"}`}></span>
        <span className="status-text">
          {connected ? "Backend Connected" : "Disconnected"}
        </span>
      </div>
    </header>
  );
}
