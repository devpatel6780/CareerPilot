CREATE TABLE IF NOT EXISTS resumes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    raw_text TEXT,
    structured_json TEXT
);

CREATE TABLE IF NOT EXISTS jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    title TEXT,
    company TEXT,
    location TEXT,
    source TEXT,
    source_url TEXT,
    structured_json TEXT
);

CREATE TABLE IF NOT EXISTS matches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    resume_id INTEGER NOT NULL REFERENCES resumes(id),
    job_id INTEGER NOT NULL REFERENCES jobs(id),
    match_score REAL,
    rationale_json TEXT
);

CREATE TABLE IF NOT EXISTS resume_versions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    resume_id INTEGER NOT NULL REFERENCES resumes(id),
    job_id INTEGER NOT NULL REFERENCES jobs(id),
    tailored_text TEXT,
    diff_json TEXT
);

CREATE TABLE IF NOT EXISTS applications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    match_id INTEGER REFERENCES matches(id),
    resume_version_id INTEGER REFERENCES resume_versions(id),
    status TEXT DEFAULT 'Not Applied',
    date_applied TEXT
);
