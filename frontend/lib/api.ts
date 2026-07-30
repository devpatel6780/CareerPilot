const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json", ...(options?.headers || {}) },
    ...options,
  });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail ? JSON.stringify(body.detail) : JSON.stringify(body);
    } catch {
      // response wasn't JSON — fall back to statusText
    }
    throw new Error(`${res.status} ${detail}`);
  }
  return res.json() as Promise<T>;
}

export interface Contact {
  name: string;
  email: string;
  location: string;
}

export interface ExperienceEntry {
  title: string;
  company: string;
  start_date: string;
  end_date: string;
  bullets: string[];
}

export interface EducationEntry {
  degree: string;
  institution: string;
  graduation_date: string;
}

export interface ProjectEntry {
  name: string;
  description: string;
  technologies: string[];
}

export interface ResumeProfile {
  contact: Contact;
  skills: string[];
  experience: ExperienceEntry[];
  education: EducationEntry[];
  projects: ProjectEntry[];
  achievements: string[];
}

export interface ResumeRecord {
  id: number;
  created_at: string;
  structured: ResumeProfile;
}

export interface JobProfile {
  title: string;
  company: string;
  location: string;
  source: string;
  source_url: string;
  requirements: string[];
  required_skills: string[];
  nice_to_have_skills: string[];
  responsibilities: string[];
  raw_description: string;
}

export interface JobRecord {
  id: number;
  created_at: string;
  title: string;
  company: string;
  location: string;
  source: string;
  source_url: string;
  structured: JobProfile;
}

export interface MatchRationale {
  strengths: string[];
  gaps: string[];
  embedding_similarity: number | null;
  llm_fit_score: number;
}

export interface MatchResult {
  match_id: number;
  match_score: number;
  rationale: MatchRationale;
  missing_skills: string[];
  strengths: string[];
}

export interface MatchRecord {
  id: number;
  created_at: string;
  resume_id: number;
  job_id: number;
  match_score: number;
  rationale: MatchRationale;
  job_title: string;
  job_company: string;
}

export interface TailorDiffEntry {
  company: string;
  title: string;
  bullet_index: number;
  original: string;
  tailored: string;
}

export interface TruthfulnessFlag {
  bullet: string;
  concern: string;
}

export interface TailorResult {
  resume_version_id: number;
  tailored_experience: ExperienceEntry[];
  tailored_skills: string[];
  diff: TailorDiffEntry[];
  truthfulness_flags: TruthfulnessFlag[];
}

export interface ApplicationRecord {
  id: number;
  created_at: string;
  status: string;
  date_applied: string | null;
  match_id: number;
  resume_version_id: number | null;
  company: string;
  title: string;
  match_score: number;
}

export const APPLICATION_STATUSES = ["Not Applied", "Applied", "Interview", "Rejected", "Offer"] as const;

export const api = {
  async uploadResume(file: File): Promise<{ resume_id: number; resume: ResumeProfile }> {
    const formData = new FormData();
    formData.append("file", file);
    const res = await fetch(`${API_BASE_URL}/resume/upload`, { method: "POST", body: formData });
    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      throw new Error(`${res.status} ${body.detail ? JSON.stringify(body.detail) : res.statusText}`);
    }
    return res.json();
  },

  listResumes: () => request<{ resumes: ResumeRecord[] }>("/resume"),

  listJobs: () => request<{ jobs: JobRecord[] }>("/jobs"),

  ingestJobs: (source: "greenhouse" | "lever", company: string, limit: number) =>
    request<{ ingested: number; jobs: { job_id: number; job: JobProfile }[] }>(
      `/jobs/ingest/${source}/${encodeURIComponent(company)}?limit=${limit}`,
      { method: "POST" }
    ),

  createMatch: (resumeId: number, jobId: number) =>
    request<MatchResult>("/match", {
      method: "POST",
      body: JSON.stringify({ resume_id: resumeId, job_id: jobId }),
    }),

  listMatches: () => request<{ matches: MatchRecord[] }>("/matches"),

  tailorResume: (resumeId: number, jobId: number) =>
    request<TailorResult>("/resume/tailor", {
      method: "POST",
      body: JSON.stringify({ resume_id: resumeId, job_id: jobId }),
    }),

  generateCoverLetter: (resumeId: number, jobId: number, tonePreference: string) =>
    request<{ cover_letter: string }>("/cover-letter/generate", {
      method: "POST",
      body: JSON.stringify({ resume_id: resumeId, job_id: jobId, tone_preference: tonePreference }),
    }),

  createApplication: (matchId: number, resumeVersionId: number | null) =>
    request<{ application_id: number }>("/applications", {
      method: "POST",
      body: JSON.stringify({ match_id: matchId, resume_version_id: resumeVersionId }),
    }),

  listApplications: () => request<{ applications: ApplicationRecord[] }>("/applications"),

  updateApplicationStatus: (applicationId: number, status: string, dateApplied?: string) =>
    request<{ application_id: number; status: string }>(`/applications/${applicationId}`, {
      method: "PATCH",
      body: JSON.stringify({ status, date_applied: dateApplied ?? null }),
    }),
};
