"use client";

import { useEffect, useState } from "react";
import { api, ResumeRecord } from "@/lib/api";

export default function ResumePage() {
  const [resumes, setResumes] = useState<ResumeRecord[]>([]);
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function refresh() {
    try {
      const { resumes } = await api.listResumes();
      setResumes(resumes);
    } catch (err) {
      setError((err as Error).message);
    }
  }

  useEffect(() => {
    refresh();
  }, []);

  async function handleUpload() {
    if (!file) return;
    setUploading(true);
    setError(null);
    try {
      await api.uploadResume(file);
      setFile(null);
      await refresh();
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setUploading(false);
    }
  }

  return (
    <div>
      <h1>Resume</h1>
      <p className="subtitle">Upload a PDF or DOCX resume to extract a structured profile.</p>

      <div className="card">
        <h2>Upload</h2>
        <div className="form-row">
          <input
            type="file"
            accept=".pdf,.docx"
            onChange={(e) => setFile(e.target.files?.[0] ?? null)}
          />
          <button onClick={handleUpload} disabled={!file || uploading}>
            {uploading ? "Uploading..." : "Upload"}
          </button>
        </div>
        {error && <p className="error">{error}</p>}
      </div>

      <div className="card">
        <h2>Uploaded resumes ({resumes.length})</h2>
        {resumes.length === 0 && <p className="muted">No resumes uploaded yet.</p>}
        {resumes.map((r) => (
          <div key={r.id} className="card" style={{ marginBottom: 12 }}>
            <div className="form-row" style={{ justifyContent: "space-between" }}>
              <strong>
                #{r.id} — {r.structured.contact.name || "(name not extracted)"}
              </strong>
              <span className="muted">{r.created_at}</span>
            </div>
            {r.structured.contact.email && <p className="muted">{r.structured.contact.email}</p>}
            <div>
              {r.structured.skills.slice(0, 12).map((s) => (
                <span key={s} className="tag">
                  {s}
                </span>
              ))}
              {r.structured.skills.length > 12 && (
                <span className="muted">+{r.structured.skills.length - 12} more</span>
              )}
            </div>
            <p className="muted">
              {r.structured.experience.length} experience entries · {r.structured.education.length} education
              entries
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}
