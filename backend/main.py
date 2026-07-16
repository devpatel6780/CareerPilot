from fastapi import FastAPI

from db.init_db import init_db

app = FastAPI(title="AI Career Agent")


@app.on_event("startup")
def on_startup():
    init_db()


@app.get("/health")
def health():
    return {"status": "ok"}
