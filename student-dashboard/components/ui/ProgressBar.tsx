"use client";

import { useState, useEffect } from "react";

interface ProgressBarProps {
  pct: number;
  variant?: "green" | "gold";
}

export default function ProgressBar({ pct, variant = "green" }: ProgressBarProps) {
  const [w, setW] = useState(0);
  useEffect(() => {
    const t = setTimeout(() => setW(pct), 350);
    return () => clearTimeout(t);
  }, [pct]);

  return (
    <div className="progress-track">
      <div className={`progress-fill ${variant}`} style={{ width: `${w}%` }} />
    </div>
  );
}
