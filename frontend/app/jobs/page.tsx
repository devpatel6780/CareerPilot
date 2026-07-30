"use client";

import { useEffect, useState } from "react";
import { api, JobRecord } from "@/lib/api";

export default function JobsPage() {
  const [jobs, setJobs] = useState<JobRecord[]>([]);
  const [source, setSource] = useState<"greenhouse" | "lever">("greenhouse");
  const [company, setCompany] = useState("");
  const [limit, setLimit] = useState(10);
  const [ingesting, setIngesting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [status, setStatus] = useState<string | null>(null);

  async function refresh() {
    try {
      const { jobs } = await api.listJobs();
      setJobs(jobs);
    } catch (err) {
      setError((err as Error).message);
    }
  }

  useEffect(() => {
    refresh();
  }, []);

  async function handleIngest() {
    if (!company.trim()) return;
    setIngesting(true);
    setError(null);
    setStatus(null);
    try {
      const result = await api.ingestJobs(source, company.trim(), limit);
      setStatus(`Ingested ${result.ingested} job(s) from ${company} (${source}).`);
      await refresh();
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setIngesting(false);
    }
  }

  return (
    <div>
      <h1>Jobs</h1>
      <p className="subtitle">Ingest open listings from a company's Greenhouse or Lever board.</p>

      <div className="card">
        <h2>Ingest new company</h2>
        <div className="form-row">
          <select value={source} onChange={(e) => setSource(e.target.value as "greenhouse" | "lever")}>
            <option value="greenhouse">Greenhouse</option>
            <option value="lever">Lever</option>
          </select>
          <input
            type="text"
            placeholder="company slug (e.g. stripe)"
            value={company}
            onChange={(e) => setCompany(e.target.value)}
          />
          <input
            type="number"
            min={1}
            max={100}
            value={limit}
            onChange={(e) => setLimit(Number(e.target.value))}
            style={{ width: 70 }}
          />
          <button onClick={handleIngest} disabled={ingesting || !company.trim()}>
            {ingesting ? "Ingesting..." : "Ingest"}
          </button>
        </div>
        {status && <p className="success-text">{status}</p>}
        {error && <p className="error">{error}</p>}
      </div>

      <div className="card">
        <h2>Ingested jobs ({jobs.length})</h2>
        {jobs.length === 0 && <p className="muted">No jobs ingested yet.</p>}
        {jobs.length > 0 && (
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>Title</th>
                <th>Company</th>
                <th>Location</th>
                <th>Source</th>
                <th>Required skills</th>
              </tr>
            </thead>
            <tbody>
              {jobs.map((job) => (
                <tr key={job.id}>
                  <td>{job.id}</td>
                  <td>{job.title}</td>
                  <td>{job.company}</td>
                  <td>{job.location}</td>
                  <td>{job.source}</td>
                  <td>
                    {job.structured.required_skills.slice(0, 4).join(", ")}
                    {job.structured.required_skills.length > 4 ? "…" : ""}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
