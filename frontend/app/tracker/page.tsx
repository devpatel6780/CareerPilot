"use client";

import { useEffect, useState } from "react";
import { api, ApplicationRecord, APPLICATION_STATUSES } from "@/lib/api";

export default function TrackerPage() {
  const [applications, setApplications] = useState<ApplicationRecord[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [updatingId, setUpdatingId] = useState<number | null>(null);

  async function refresh() {
    try {
      const { applications } = await api.listApplications();
      setApplications(applications);
    } catch (err) {
      setError((err as Error).message);
    }
  }

  useEffect(() => {
    refresh();
  }, []);

  async function handleStatusChange(id: number, status: string) {
    setUpdatingId(id);
    setError(null);
    try {
      const dateApplied = status === "Applied" ? new Date().toISOString().slice(0, 10) : undefined;
      await api.updateApplicationStatus(id, status, dateApplied);
      await refresh();
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setUpdatingId(null);
    }
  }

  return (
    <div>
      <h1>Application tracker</h1>
      <p className="subtitle">
        Manually log status changes as you apply — nothing here auto-applies on your behalf.
      </p>

      {error && <p className="error">{error}</p>}

      <div className="card">
        {applications.length === 0 && (
          <p className="muted">
            No applications tracked yet. Run a match on the Matches page, then click "Track this application".
          </p>
        )}
        {applications.length > 0 && (
          <table>
            <thead>
              <tr>
                <th>Company</th>
                <th>Role</th>
                <th>Match score</th>
                <th>Resume version</th>
                <th>Date applied</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {applications.map((a) => (
                <tr key={a.id}>
                  <td>{a.company}</td>
                  <td>{a.title}</td>
                  <td>{a.match_score.toFixed(1)}</td>
                  <td>{a.resume_version_id ?? "original"}</td>
                  <td>{a.date_applied ?? "—"}</td>
                  <td>
                    <select
                      value={a.status}
                      disabled={updatingId === a.id}
                      onChange={(e) => handleStatusChange(a.id, e.target.value)}
                    >
                      {APPLICATION_STATUSES.map((s) => (
                        <option key={s} value={s}>
                          {s}
                        </option>
                      ))}
                    </select>
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
