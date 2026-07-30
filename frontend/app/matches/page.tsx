"use client";

import { useEffect, useState } from "react";
import {
  api,
  ResumeRecord,
  JobRecord,
  MatchRecord,
  MatchResult,
  TailorResult,
} from "@/lib/api";

export default function MatchesPage() {
  const [resumes, setResumes] = useState<ResumeRecord[]>([]);
  const [jobs, setJobs] = useState<JobRecord[]>([]);
  const [matches, setMatches] = useState<MatchRecord[]>([]);

  const [resumeId, setResumeId] = useState<number | null>(null);
  const [jobId, setJobId] = useState<number | null>(null);

  const [matching, setMatching] = useState(false);
  const [matchResult, setMatchResult] = useState<MatchResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const [tailoring, setTailoring] = useState(false);
  const [tailorResult, setTailorResult] = useState<TailorResult | null>(null);

  const [tone, setTone] = useState("professional");
  const [generatingLetter, setGeneratingLetter] = useState(false);
  const [coverLetter, setCoverLetter] = useState<string | null>(null);

  const [tracking, setTracking] = useState(false);
  const [trackedStatus, setTrackedStatus] = useState<string | null>(null);

  async function refreshAll() {
    try {
      const [r, j, m] = await Promise.all([api.listResumes(), api.listJobs(), api.listMatches()]);
      setResumes(r.resumes);
      setJobs(j.jobs);
      setMatches(m.matches);
      if (r.resumes.length > 0 && resumeId === null) setResumeId(r.resumes[0].id);
      if (j.jobs.length > 0 && jobId === null) setJobId(j.jobs[0].id);
    } catch (err) {
      setError((err as Error).message);
    }
  }

  useEffect(() => {
    refreshAll();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function handleMatch() {
    if (resumeId === null || jobId === null) return;
    setMatching(true);
    setError(null);
    setMatchResult(null);
    setTailorResult(null);
    setCoverLetter(null);
    setTrackedStatus(null);
    try {
      const result = await api.createMatch(resumeId, jobId);
      setMatchResult(result);
      const { matches } = await api.listMatches();
      setMatches(matches);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setMatching(false);
    }
  }

  async function handleTailor() {
    if (resumeId === null || jobId === null) return;
    setTailoring(true);
    setError(null);
    try {
      const result = await api.tailorResume(resumeId, jobId);
      setTailorResult(result);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setTailoring(false);
    }
  }

  async function handleCoverLetter() {
    if (resumeId === null || jobId === null) return;
    setGeneratingLetter(true);
    setError(null);
    try {
      const result = await api.generateCoverLetter(resumeId, jobId, tone);
      setCoverLetter(result.cover_letter);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setGeneratingLetter(false);
    }
  }

  async function handleTrack() {
    if (!matchResult) return;
    setTracking(true);
    setError(null);
    try {
      await api.createApplication(matchResult.match_id, tailorResult?.resume_version_id ?? null);
      setTrackedStatus("Added to application tracker.");
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setTracking(false);
    }
  }

  return (
    <div>
      <h1>Matches</h1>
      <p className="subtitle">Score fit between a resume and a job, then tailor or generate a cover letter.</p>

      <div className="card">
        <h2>Run a match</h2>
        <div className="form-row">
          <select value={resumeId ?? ""} onChange={(e) => setResumeId(Number(e.target.value))}>
            <option value="" disabled>
              Select resume
            </option>
            {resumes.map((r) => (
              <option key={r.id} value={r.id}>
                #{r.id} — {r.structured.contact.name || "unnamed"}
              </option>
            ))}
          </select>
          <select value={jobId ?? ""} onChange={(e) => setJobId(Number(e.target.value))}>
            <option value="" disabled>
              Select job
            </option>
            {jobs.map((j) => (
              <option key={j.id} value={j.id}>
                #{j.id} — {j.title} @ {j.company}
              </option>
            ))}
          </select>
          <button onClick={handleMatch} disabled={matching || resumeId === null || jobId === null}>
            {matching ? "Matching..." : "Run match"}
          </button>
        </div>
        {error && <p className="error">{error}</p>}

        {matchResult && (
          <div className="card" style={{ background: "transparent" }}>
            <div className="score">{matchResult.match_score.toFixed(1)} / 100</div>
            <p className="muted">
              embedding similarity: {matchResult.rationale.embedding_similarity?.toFixed(1) ?? "n/a"} · LLM fit
              score: {matchResult.rationale.llm_fit_score}
            </p>

            <h2>Strengths</h2>
            {matchResult.strengths.length === 0 && <p className="muted">None identified.</p>}
            <ul>
              {matchResult.strengths.map((s, i) => (
                <li key={i}>{s}</li>
              ))}
            </ul>

            <h2>Gaps</h2>
            {matchResult.rationale.gaps.length === 0 && <p className="muted">None identified.</p>}
            <ul>
              {matchResult.rationale.gaps.map((g, i) => (
                <li key={i}>{g}</li>
              ))}
            </ul>

            <h2>Missing skills</h2>
            <div>
              {matchResult.missing_skills.map((s) => (
                <span key={s} className="tag">
                  {s}
                </span>
              ))}
              {matchResult.missing_skills.length === 0 && <p className="muted">None identified.</p>}
            </div>

            <div className="form-row" style={{ marginTop: 16 }}>
              <button onClick={handleTailor} disabled={tailoring}>
                {tailoring ? "Tailoring..." : "Tailor resume for this job"}
              </button>
              <select value={tone} onChange={(e) => setTone(e.target.value)}>
                <option value="professional">Professional</option>
                <option value="enthusiastic">Enthusiastic</option>
                <option value="conversational">Conversational</option>
              </select>
              <button onClick={handleCoverLetter} disabled={generatingLetter}>
                {generatingLetter ? "Generating..." : "Generate cover letter"}
              </button>
              <button className="secondary" onClick={handleTrack} disabled={tracking}>
                {tracking ? "Adding..." : "Track this application"}
              </button>
            </div>
            {trackedStatus && <p className="success-text">{trackedStatus}</p>}
          </div>
        )}
      </div>

      {tailorResult && (
        <div className="card">
          <h2>Tailored resume (version #{tailorResult.resume_version_id})</h2>
          <p className="muted">{tailorResult.diff.length} bullet(s) changed</p>
          {tailorResult.diff.map((d, i) => (
            <div key={i} className="diff-line">
              <div className="original">{d.original}</div>
              <div className="tailored">{d.tailored}</div>
              <div className="muted">
                {d.company} — {d.title}
              </div>
            </div>
          ))}
          {tailorResult.diff.length === 0 && <p className="muted">No bullets were changed.</p>}

          <h2>Truthfulness flags</h2>
          {tailorResult.truthfulness_flags.length === 0 && (
            <p className="muted">No unsupported claims flagged.</p>
          )}
          {tailorResult.truthfulness_flags.map((f, i) => (
            <div key={i} className="flag">
              <strong>{f.bullet}</strong>
              <div>{f.concern}</div>
            </div>
          ))}
        </div>
      )}

      {coverLetter && (
        <div className="card">
          <h2>Cover letter</h2>
          <textarea readOnly value={coverLetter} />
        </div>
      )}

      <div className="card">
        <h2>Match history ({matches.length})</h2>
        {matches.length === 0 && <p className="muted">No matches yet.</p>}
        {matches.length > 0 && (
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>Job</th>
                <th>Company</th>
                <th>Score</th>
                <th>Created</th>
              </tr>
            </thead>
            <tbody>
              {matches.map((m) => (
                <tr key={m.id}>
                  <td>{m.id}</td>
                  <td>{m.job_title}</td>
                  <td>{m.job_company}</td>
                  <td>{m.match_score.toFixed(1)}</td>
                  <td>{m.created_at}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
