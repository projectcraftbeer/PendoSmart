from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional
import sqlite3
import os
import httpx
from smartling_config import SMARTLING_USER_ID, SMARTLING_SECRET, SMARTLING_PROJECT_ID, update_env_var

app = FastAPI()

# Allow CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_PATH = os.path.join(os.path.dirname(__file__), 'strings.db')

# Database setup

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS strings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT NOT NULL,
            japanese TEXT NOT NULL,
            confidence REAL,
            reason TEXT,
            suggestion TEXT
        )''')
        conn.commit()

init_db()

class StringPair(BaseModel):
    id: Optional[int]
    source: str
    japanese: str
    confidence: Optional[float] = None
    reason: Optional[str] = None
    suggestion: Optional[str] = None

class EvaluationRequest(BaseModel):
    id: int
    source: str
    japanese: str

@app.get("/strings", response_model=List[StringPair])
def get_strings():
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("SELECT id, source, japanese, confidence, reason, suggestion FROM strings")
        rows = c.fetchall()
        return [StringPair(id=row[0], source=row[1], japanese=row[2], confidence=row[3], reason=row[4], suggestion=row[5]) for row in rows]

@app.post("/strings", response_model=StringPair)
def add_string(pair: StringPair):
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("INSERT INTO strings (source, japanese) VALUES (?, ?)", (pair.source, pair.japanese))
        conn.commit()
        pair.id = c.lastrowid
        return pair

@app.post("/evaluate", response_model=StringPair)
def evaluate_string(req: EvaluationRequest):
    # Call Azure OpenAI here (mocked for now)
    # Replace with actual Azure OpenAI call
    confidence = 0.85
    reason = "Translation is mostly natural, but could be improved."
    suggestion = "Use より自然な表現 here."
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("""
            UPDATE strings SET confidence=?, reason=?, suggestion=? WHERE id=?
        """, (confidence, reason, suggestion, req.id))
        conn.commit()
    return StringPair(id=req.id, source=req.source, japanese=req.japanese, confidence=confidence, reason=reason, suggestion=suggestion)

@app.get("/admin/smartling-keys")
def get_smartling_keys():
    return {
        "user_id": SMARTLING_USER_ID,
        "secret": bool(SMARTLING_SECRET),
        "project_id": SMARTLING_PROJECT_ID
    }

@app.post("/admin/smartling-keys")
def set_smartling_keys(data: dict):
    user_id = data.get("user_id", "")
    secret = data.get("secret", "")
    project_id = data.get("project_id", "")
    update_env_var("SMARTLING_USER_ID", user_id)
    update_env_var("SMARTLING_SECRET", secret)
    update_env_var("SMARTLING_PROJECT_ID", project_id)
    return {"status": "ok"}

# TODO: Add Smartling API integration and real Azure OpenAI call
