import concurrent.futures
import httpx
import time
import sqlite3
import os
import httpx
import logging
import time
from fastapi import FastAPI, HTTPException, Request, Query, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional
from fastapi import APIRouter
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
DB_PATH = os.path.join(os.path.dirname(__file__), 'strings.db')

def init_db():
    #sql sql sql dance
    if not os.path.exists(DB_PATH):
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        open(DB_PATH, 'a').close()
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
        c.execute('''CREATE TABLE IF NOT EXISTS smartling_keys (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            secret TEXT NOT NULL,
            project_id TEXT,
            job_id TEXT,
            access_token TEXT,
            refresh_token TEXT,
            token_expires INTEGER,
            account_id TEXT,
            locale TEXT
        )''')
        c.execute('''CREATE TABLE IF NOT EXISTS job_files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id TEXT NOT NULL,
            file_uri TEXT NOT NULL,
            project_id TEXT
        )''')
        c.execute('''CREATE TABLE IF NOT EXISTS smartling_job_files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id TEXT NOT NULL,
            file_uri TEXT NOT NULL,
            project_id TEXT NOT NULL
        )''')
        c.execute('''CREATE TABLE IF NOT EXISTS smartling_translations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id TEXT NOT NULL,
            file_uri TEXT NOT NULL,
            locale TEXT NOT NULL,
            parsed_string_text TEXT,
            translation TEXT,
            status TEXT NOT NULL DEFAULT 'pending',
            confidence REAL,
            reason TEXT,
            flag INTEGER,
            hashcode TEXT UNIQUE
        )''')
        c.execute('''CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )''')
    c.execute('''CREATE TABLE IF NOT EXISTS smartling_job_files (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        job_id TEXT NOT NULL,
        file_uri TEXT NOT NULL,
        project_id TEXT NOT NULL
    )''')
    conn.commit()
init_db()
#Setup LLM 
class TranslationEvalRequest(BaseModel):
    source: str
    translation: str

class TranslationEvalResponse(BaseModel):
    score: int
    reason: str

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

MODEL_PATH = "microsoft/Phi-4-mini-instruct"

def get_setting(key: str, default=None):
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("SELECT value FROM settings WHERE key=?", (key,))
        row = c.fetchone()
        return row[0] if row else default

def set_setting(key: str, value: str):
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
        conn.commit()

# --- Model download flag logic ---
MODEL_DOWNLOAD_FLAG = get_setting('download_model', 'false') == 'true'

if MODEL_DOWNLOAD_FLAG:
    torch.random.manual_seed(0)
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_PATH,
        device_map="auto",
        torch_dtype="auto",
        trust_remote_code=False,
    )
    tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
    pipe = pipeline(
        "text-generation",
        model=model,
        tokenizer=tokenizer,
    )
else:
    model = None
    tokenizer = None
    pipe = None

generation_args = {
    "max_new_tokens": 500,
    "return_full_text": False,
    "temperature": 0.0,
    "do_sample": False,
}



app = FastAPI()
@app.post("/admin/smartling-toggle-status")
async def smartling_toggle_status(data: dict = Body(...)):
    row_id = data.get("id")
    status = data.get("status")
    if row_id is None or status not in ("pending", "completed"):
        return JSONResponse(status_code=400, content={"success": False, "message": "Missing id or invalid status"})
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("UPDATE smartling_translations SET status=? WHERE id=?", (status, row_id))
        conn.commit()
    return {"success": True}

@app.post("/admin/smartling-bulk-complete")
async def smartling_bulk_complete(data: dict = Body(...)):
    ids = data.get("ids")
    if not ids or not isinstance(ids, list):
        return JSONResponse(status_code=400, content={"success": False, "message": "Missing or invalid ids list"})
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.executemany("UPDATE smartling_translations SET status='completed' WHERE id=?", [(i,) for i in ids])
        conn.commit()
    return {"success": True, "updated": len(ids)}

async def refresh_smartling_token(refresh_token, user_id, secret, DB_PATH):
    async with httpx.AsyncClient() as client:
        res = await client.post(
            "https://api.smartling.com/auth-api/v2/authenticate/refresh",
            json={"refreshToken": refresh_token}
        )
        res.raise_for_status()
        data = res.json()
        new_access_token = data.get('response', {}).get('data', {}).get('accessToken')
        new_refresh_token = data.get('response', {}).get('data', {}).get('refreshToken')
        expires_in = data.get('response', {}).get('data', {}).get('expiresIn')
        new_token_expires = int(time.time()) + int(expires_in) if expires_in else None
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            c.execute("UPDATE smartling_keys SET access_token=?, refresh_token=?, token_expires=? WHERE user_id=? AND secret=?", (new_access_token, new_refresh_token, new_token_expires, user_id, secret))
            conn.commit()
        return new_access_token, new_refresh_token, new_token_expires

@app.post("/admin/flag-matching-strings")
async def flag_matching_strings(project_id: str = Query(None), locale: str = Query("ja-JP")):
    if not project_id:
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            c.execute("SELECT project_id FROM smartling_keys ORDER BY id DESC LIMIT 1")
            row = c.fetchone()
            if row and row[0]:
                project_id = row[0]
            else:
                return JSONResponse(status_code=400, content={"success": False, "message": "No project_id found in database and none provided."})
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("SELECT id, parsed_string_text, translation FROM smartling_translations WHERE project_id=? AND locale=?", (project_id, locale))
        rows = c.fetchall()
        flagged = 0
        for row in rows:
            row_id, src, tgt = row
            if src and tgt and src.strip().lower() == tgt.strip().lower():
                c.execute("UPDATE smartling_translations SET flag=1 WHERE id=?", (row_id,))
                flagged += 1
        conn.commit()
    return {"success": True, "message": f"Flagged {flagged} matching rows for project_id {project_id}."}

# I hate cors
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    
# will implement someday...
@app.post("/evaluate", response_model=StringPair)
def evaluate_string(req: EvaluationRequest):

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
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("SELECT user_id, secret, project_id, account_id, job_id, locale FROM smartling_keys ORDER BY id DESC LIMIT 1")
        row = c.fetchone()
        if row:
            return {"user_id": row[0], "secret": row[1], "project_id": row[2], "account_id": row[3], "job_id": row[4], "locale": row[5]}
        else:
            return {"user_id": "", "secret": "", "project_id": "", "account_id": "", "job_id": "", "locale": "ja-JP"}

@app.post("/admin/smartling-keys")
def set_smartling_keys(data: dict):
    user_id = data.get("user_id", "")
    secret = data.get("secret", "")
    project_id = data.get("project_id", "")
    account_id = data.get("account_id", "")
    job_id = data.get("job_id", "")
    locale = data.get("locale", "ja-JP")
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        # Check if a row exists
        c.execute("SELECT id FROM smartling_keys ORDER BY id DESC LIMIT 1")
        row = c.fetchone()
        if row:
         # preserve tokens
            c.execute("""
                UPDATE smartling_keys
                SET user_id=?, secret=?, project_id=?, account_id=?, job_id=?, locale=?
                WHERE id=?
            """, (user_id, secret, project_id, account_id, job_id, locale, row[0]))
        else:
            c.execute("INSERT INTO smartling_keys (user_id, secret, project_id, account_id, job_id, locale) VALUES (?, ?, ?, ?, ?, ?)", (user_id, secret, project_id, account_id, job_id, locale))
        conn.commit()
    return {"status": "ok"}

@app.get("/admin/smartling-projects")
async def get_smartling_projects():
    import time
    SMARTLING_API_URL = None
    account_id = None
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("SELECT user_id, secret, project_id, account_id, access_token, refresh_token, token_expires FROM smartling_keys ORDER BY id DESC LIMIT 1")
        row = c.fetchone()
        if not row:
            return JSONResponse(status_code=400, content={"error": "No Smartling credentials set"})
        user_id, secret, project_id, account_id, access_token, refresh_token, token_expires = row
    if not account_id:
        return JSONResponse(status_code=400, content={"error": "No Smartling account ID set in admin"})
    SMARTLING_API_URL = f"https://api.smartling.com/accounts-api/v2/accounts/{account_id}/projects"
    now = int(time.time())
    token = access_token

    async def fetch_projects(token):
        async with httpx.AsyncClient() as client:
            headers = {"Authorization": f"Bearer {token}"}
            proj_res = await client.get(SMARTLING_API_URL, headers=headers)
            if proj_res.status_code == 401:
                raise Exception("unauthorized")
            proj_res.raise_for_status()
            projects = proj_res.json()["response"]["data"]["items"]
            return [f"{p['projectId']} - {p['projectName']}" for p in projects]

    if not token or (token_expires and now >= token_expires):
        token = None
    tried_refresh = False
    for attempt in range(2):
        try:
            if not token and refresh_token:
                token, _, _ = await refresh_smartling_token(refresh_token, user_id, secret, DB_PATH)
                tried_refresh = True
            if not token:
                return JSONResponse(status_code=401, content={"error": "No valid Smartling access token. Please authenticate again from the admin page."})
            return await fetch_projects(token)
        except Exception as e:
            if (not tried_refresh) and refresh_token and ("unauthorized" in str(e) or "401" in str(e)):
                token, _, _ = await refresh_smartling_token(refresh_token)
                tried_refresh = True
                continue
            print("[Smartling Auth Error]", e)
            import traceback; traceback.print_exc()
            return JSONResponse(status_code=500, content={"error": str(e)})
class SmartlingAuthRequest(BaseModel):
    user_id: str
    secret: str


@app.post("/admin/smartling-auth")
async def smartling_auth(req: SmartlingAuthRequest):
    try:
        async with httpx.AsyncClient() as client:
            res = await client.post(
                "https://api.smartling.com/auth-api/v2/authenticate",
                json={
                    "userIdentifier": req.user_id,
                    "userSecret": req.secret
                }
            )
            res.raise_for_status()
            data = res.json()
            logging.info(f"{data}")
            access_token = data.get('response', {}).get('data', {}).get('accessToken')
            refresh_token = data.get('response', {}).get('data', {}).get('refreshToken')
            expires_in = data.get('response', {}).get('data', {}).get('expiresIn')
            import time
            token_expires = int(time.time()) + int(expires_in) if expires_in else None
            with sqlite3.connect(DB_PATH) as conn:
                c = conn.cursor()
                c.execute("UPDATE smartling_keys SET access_token=?, refresh_token=?, token_expires=? WHERE user_id=? AND secret=?", (access_token, refresh_token, token_expires, req.user_id, req.secret))
                conn.commit()
            return data
    except Exception as e:
        logging.error(f"Smartling auth error: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})

# fetch jobs for a given project
@app.get("/admin/smartling-jobs")
async def get_smartling_jobs(project_id: str = Query(...)):
    """Fetch jobs for a given Smartling project ID (requires valid tokens in DB)"""
    import time
    SMARTLING_API_URL = None
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("SELECT user_id, secret, account_id, access_token, refresh_token, token_expires FROM smartling_keys ORDER BY id DESC LIMIT 1")
        row = c.fetchone()
        if not row:
            return JSONResponse(status_code=400, content={"error": "No Smartling credentials set"})
        user_id, secret, account_id, access_token, refresh_token, token_expires = row
    if not account_id:
        return JSONResponse(status_code=400, content={"error": "No Smartling account ID set in admin"})
    SMARTLING_API_URL = f"https://api.smartling.com/jobs-api/v3/projects/{project_id}/jobs"
    now = int(time.time())
    token = access_token

    async def fetch_jobs(token):
        async with httpx.AsyncClient() as client:
            headers = {"Authorization": f"Bearer {token}"}
            jobs_res = await client.get(SMARTLING_API_URL, headers=headers)
            if jobs_res.status_code == 401:
                raise Exception("unauthorized")
            jobs_res.raise_for_status()
            jobs = jobs_res.json().get("response", {}).get("data", {}).get("items", [])
            #print("[Smartling Jobs API response items]", jobs)
            result = []
            for j in jobs:
                job_id = j.get("translationJobUid") or j.get("jobId") or j.get("id")
                job_name = j.get("jobName") or j.get("name") or str(job_id)
                if job_id:
                    result.append({"jobId": job_id, "jobName": job_name})
            return result

    if not token or (token_expires and now >= token_expires):
        token = None
    tried_refresh = False
    for attempt in range(2):
        try:
            if not token and refresh_token:
                token, _, _ = await refresh_smartling_token(refresh_token, user_id, secret, DB_PATH)
                tried_refresh = True
            if not token:
                return JSONResponse(status_code=401, content={"error": "No valid Smartling access token. Please authenticate again from the admin page."})
            return await fetch_jobs(token)
        except Exception as e:
            if (not tried_refresh) and refresh_token and ("unauthorized" in str(e) or "401" in str(e)):
                token, _, _ = await refresh_smartling_token(refresh_token)
                tried_refresh = True
                continue
            print("[Smartling Jobs Error]", e)
            import traceback; traceback.print_exc()
            return JSONResponse(status_code=500, content={"error": str(e)})

# fetch and cache Smartling source strings and translations
@app.get("/admin/smartling-strings")
async def get_smartling_strings(project_id: str, locale: str = "ja-JP", page: int = 1, per_page: int = 50):
    import time
    import math
    import asyncio
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("DELETE FROM strings WHERE project_id=? AND locale=?", (project_id, locale))
        conn.commit()
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("SELECT user_id, secret, account_id, access_token, refresh_token, token_expires FROM smartling_keys ORDER BY id DESC LIMIT 1")
        row = c.fetchone()
        if not row:
            return JSONResponse(status_code=400, content={"error": "No Smartling credentials set"})
        user_id, secret, account_id, access_token, refresh_token, token_expires = row
    SMARTLING_API_URL = f"https://api.smartling.com/strings-api/v2/projects/{project_id}/source-strings"
    now = int(time.time())
    token = access_token

    async def fetch_translation_async(client, project_id, locale, string_id, string_text, token):
        try:
            trans_url = f"https://api.smartling.com/strings-api/v2/projects/{project_id}/translations"
            trans_params = {"targetLocaleId": locale, "stringId": string_id}
            headers = {"Authorization": f"Bearer {token}"}
            res = await client.get(trans_url, headers=headers, params=trans_params)
            translation = ""
            if res.status_code == 200:
                trans_data = res.json().get("response", {}).get("data", {})
                translation = trans_data.get("translation", "")
            return (string_id, string_text, translation)
        except Exception as e:
            print(f"[Async Translation Fetch Error] string_id={string_id}: {e}")
            return (string_id, string_text, "")

    async def fetch_strings(token):
        async with httpx.AsyncClient() as client:
            headers = {"Authorization": f"Bearer {token}"}
            params = {"limit": 500}
            res = await client.get(SMARTLING_API_URL, headers=headers, params=params)
            if res.status_code == 401:
                raise Exception("unauthorized")
            res.raise_for_status()
            items = res.json().get("response", {}).get("data", {}).get("items", [])
            # Launch all translation fetches concurrently
            tasks = [fetch_translation_async(client, project_id, locale, s.get("stringId"), s.get("stringText"), token) for s in items]
            translations = await asyncio.gather(*tasks)
            with sqlite3.connect(DB_PATH) as conn:
                c = conn.cursor()
                for string_id, source, translation in translations:
                    c.execute("INSERT OR REPLACE INTO strings (id, source, translation, project_id, locale) VALUES (?, ?, ?, ?, ?)", (string_id, source, translation, project_id, locale))
                conn.commit()
            return translations

    if not token or (token_expires and now >= token_expires):
        token = None
    tried_refresh = False
    for attempt in range(2):
        try:
            if not token and refresh_token:
                token, _, _ = await refresh_smartling_token(refresh_token, user_id, secret, DB_PATH)
                tried_refresh = True
            if not token:
                return JSONResponse(status_code=401, content={"error": "No valid Smartling access token. Please authenticate again from the admin page."})
            await fetch_strings(token)
            with sqlite3.connect(DB_PATH) as conn:
                c = conn.cursor()
                c.execute("SELECT COUNT(*) FROM strings WHERE project_id=? AND locale=?", (project_id, locale))
                count = c.fetchone()[0]
                c.execute("SELECT id, source, translation FROM strings WHERE project_id=? AND locale=? ORDER BY id LIMIT ? OFFSET ?", (project_id, locale, per_page, (page-1)*per_page))
                rows = c.fetchall()
                return {"total": count, "page": page, "per_page": per_page, "strings": [{"id": row[0], "source": row[1], "translation": row[2]} for row in rows]}
        except Exception as e:
            if (not tried_refresh) and refresh_token and ("unauthorized" in str(e) or "401" in str(e)):
                token, _, _ = await refresh_smartling_token(refresh_token)
                tried_refresh = True
                continue
            print("[Smartling Strings Error]", e)
            import traceback; traceback.print_exc()
            return JSONResponse(status_code=500, content={"error": str(e)})
         
@app.get("/admin/smartling-job-files")
def get_job_files(project_id: str):
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("SELECT job_id, file_uri FROM smartling_job_files WHERE project_id=?", (project_id,))
        rows = c.fetchall()
        return [{"job_id": row[0], "file_uri": row[1]} for row in rows]

@app.post("/admin/smartling-job-files")
async def fetch_and_save_job_files(data: dict = Body(...)):
    project_id = data.get("project_id")
    if not project_id:
        return JSONResponse(status_code=400, content={"error": "Missing project_id"})
    import time
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("SELECT user_id, secret, account_id, access_token, refresh_token, token_expires FROM smartling_keys ORDER BY id DESC LIMIT 1")
        row = c.fetchone()
        if not row:
            return JSONResponse(status_code=400, content={"error": "No Smartling credentials set"})
        user_id, secret, account_id, access_token, refresh_token, token_expires = row
    now = int(time.time())
    token = access_token

    async def fetch_job_files(token):
        async with httpx.AsyncClient() as client:
            headers = {"Authorization": f"Bearer {token}"}
            jobs_url = f"https://api.smartling.com/jobs-api/v3/projects/{project_id}/jobs"
            jobs_res = await client.get(jobs_url, headers=headers)
            jobs_res.raise_for_status()
            jobs = jobs_res.json().get("response", {}).get("data", {}).get("items", [])
            job_file_pairs = []
            for job in jobs:
                job_id = job.get("translationJobUid") or job.get("jobId") or job.get("id")
                job_status = job.get("jobStatus")
                if not job_id or job_status == "CANCELLED":
                    continue
                files_url = f"https://api.smartling.com/jobs-api/v3/projects/{project_id}/jobs/{job_id}/files"
                files_res = await client.get(files_url, headers=headers)
                files_res.raise_for_status()
                files = files_res.json().get("response", {}).get("data", {}).get("items", [])
                for f in files:
                    file_uri = f.get("uri") or f.get("fileUri")
                    if file_uri:
                        job_file_pairs.append((job_id, file_uri))
            with sqlite3.connect(DB_PATH) as conn:
                c = conn.cursor()
                for job_id, file_uri in job_file_pairs:
                    c.execute("INSERT OR IGNORE INTO smartling_job_files (job_id, file_uri, project_id) VALUES (?, ?, ?)", (job_id, file_uri, project_id))
                conn.commit()
            return job_file_pairs

    if not token or (token_expires and now >= token_expires):
        token = None
    tried_refresh = False
    for attempt in range(2):
        try:
            if not token and refresh_token:
                token, _, _ = await refresh_smartling_token(refresh_token, user_id, secret, DB_PATH)
                tried_refresh = True
            if not token:
                return JSONResponse(status_code=401, content={"error": "No valid Smartling access token. Please authenticate again from the admin page."})
            pairs = await fetch_job_files(token)
            return {"saved": len(pairs), "pairs": pairs}
        except Exception as e:
            if (not tried_refresh) and refresh_token and ("unauthorized" in str(e) or "401" in str(e)):
                token, _, _ = await refresh_smartling_token(refresh_token)
                tried_refresh = True
                continue
            print("[Smartling Job Files Error]", e)
            import traceback; traceback.print_exc()
            return JSONResponse(status_code=500, content={"error": str(e)})

# fetch and save all translations for all files in a project
@app.post("/admin/smartling-fetch-translations")
async def fetch_and_save_translations(data: dict = Body(...)):
    project_id = data.get("project_id")
    locale = data.get("locale", "ja-JP")
    if not project_id:
        return JSONResponse(status_code=400, content={"error": "Missing project_id"})
    # wtf was i doing. but may need this later
    # with sqlite3.connect(DB_PATH) as conn:
    #     c = conn.cursor()
    #     c.execute("DELETE FROM smartling_translations WHERE project_id=? AND locale=?", (project_id, locale))
    #     conn.commit()
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("SELECT DISTINCT file_uri FROM smartling_job_files WHERE project_id=?", (project_id,))
        file_uris = [row[0] for row in c.fetchall()]
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("SELECT user_id, secret, account_id, access_token, refresh_token, token_expires FROM smartling_keys ORDER BY id DESC LIMIT 1")
        row = c.fetchone()
        if not row:
            return JSONResponse(status_code=400, content={"error": "No Smartling credentials set"})
        user_id, secret, account_id, access_token, refresh_token, token_expires = row
    now = int(time.time())
    token = access_token
    async def fetch_translations(token):
        async with httpx.AsyncClient(timeout=60.0) as client:
            headers = {"Authorization": f"Bearer {token}"}
            saved_count = 0
            for file_uri in file_uris:
                offset = 0
                while True:
                    url = f"https://api.smartling.com/strings-api/v2/projects/{project_id}/translations"
                    params = {"targetLocaleId": locale, "fileUri": file_uri, "offset": offset}
                    res = await client.get(url, headers=headers, params=params)
                    if res.status_code == 401:
                        raise Exception("unauthorized")
                    res.raise_for_status()
                    items = res.json().get("response", {}).get("data", {}).get("items", [])
                    if not items:
                        break
                    with sqlite3.connect(DB_PATH) as conn:
                        c = conn.cursor()
                        for item in items:
                            parsed = item.get("parsedStringText")
                            translations = item.get("translations", [])
                            translation = translations[0]["translation"] if translations and "translation" in translations[0] else None
                            hashcode = item.get("hashcode")
                            c.execute("SELECT id, translation, reason, confidence, flag, status FROM smartling_translations WHERE project_id=? AND locale=? AND hashcode=?", (project_id, locale, hashcode))
                            existing = c.fetchone()
                            if existing:
                                current_id, current_translation, current_reason, current_confidence, current_flag, current_status = existing
                                # don't reset status if translation is the same
                                if current_translation != translation:
                                    new_status = 'pending'
                                else:
                                    new_status = current_status
                                c.execute("UPDATE smartling_translations SET parsed_string_text=?, translation=?, status=?, confidence=?, reason=?, flag=? WHERE id=?",
                                    (parsed, translation, new_status, current_confidence, current_reason, current_flag, current_id))
                            else:
                                c.execute(
                                    "INSERT INTO smartling_translations (project_id, file_uri, locale, parsed_string_text, translation, status, confidence, reason, flag, hashcode) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                                    (project_id, file_uri, locale, parsed, translation, 'pending', None, None, 0, hashcode)
                                )
                            saved_count += 1
                        conn.commit()
                    offset += len(items)
            return saved_count
    if not token or (token_expires and now >= token_expires):
        token = None
    tried_refresh = False
    for attempt in range(2):
        try:
            if not token and refresh_token:
                token, _, _ = await refresh_smartling_token(refresh_token, user_id, secret, DB_PATH)
                tried_refresh = True
            if not token:
                return JSONResponse(status_code=401, content={"error": "No valid Smartling access token. Please authenticate again from the admin page."})
            count = await fetch_translations(token)
            return {"saved": count}
        except Exception as e:
            if (not tried_refresh) and refresh_token and ("unauthorized" in str(e) or "401" in str(e)):
                token, _, _ = await refresh_smartling_token(refresh_token)
                tried_refresh = True
                continue
            print("[Smartling Fetch Translations Error]", e)
            import traceback; traceback.print_exc()
            return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/admin/smartling-translations-table")
async def get_smartling_translations_table(
    project_id: str,
    locale: str = "ja-JP",
    page: int = 1,
    per_page: int = 50,
    flag: int = None,
    status: str = None,
    search_type: str = None,
    search_text: str = None
):
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        query = "SELECT COUNT(*) FROM smartling_translations WHERE project_id=? AND locale=?"
        params = [project_id, locale]
        if flag is not None:
            query += " AND flag=?"
            params.append(flag)
        if status in ("completed", "pending"):
            query += " AND status=?"
            params.append(status)
        if search_type and search_text:
            if search_type == "source":
                query += " AND parsed_string_text LIKE ?"
                params.append(f"%{search_text}%")
            elif search_type == "translation":
                query += " AND translation LIKE ?"
                params.append(f"%{search_text}%")
        c.execute(query, params)
        count = c.fetchone()[0]
        query = "SELECT id, file_uri, parsed_string_text, translation, status, confidence, reason, flag, hashcode FROM smartling_translations WHERE project_id=? AND locale=?"
        params = [project_id, locale]
        if flag is not None:
            query += " AND flag=?"
            params.append(flag)
        if status in ("completed", "pending"):
            query += " AND status=?"
            params.append(status)
        if search_type and search_text:
            if search_type == "source":
                query += " AND parsed_string_text LIKE ?"
                params.append(f"%{search_text}%")
            elif search_type == "translation":
                query += " AND translation LIKE ?"
                params.append(f"%{search_text}%")
        query += " ORDER BY id LIMIT ? OFFSET ?"
        params.extend([per_page, (page-1)*per_page])
        c.execute(query, params)
        rows = c.fetchall()
        return {"total": count, "page": page, "per_page": per_page, "translations": [
            {"id": row[0], "file_uri": row[1], "parsed_string_text": row[2], "translation": row[3], "status": row[4], "confidence": row[5], "reason": row[6], "flag": row[7], "hashcode": row[8]} for row in rows
        ]}

@app.post("/admin/smartling-update-reason")
async def smartling_update_reason(data: dict = Body(...)):
    ids = data.get("ids")
    reason = data.get("reason") if "reason" in data else None
    if not ids:
        return JSONResponse(status_code=400, content={"success": False, "message": "Missing ids"})
    if not isinstance(ids, list):
        ids = [ids]
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.executemany("UPDATE smartling_translations SET reason=? WHERE id=?", [(reason, row_id) for row_id in ids])
        conn.commit()
    return {"success": True, "updated": len(ids)}

@app.post("/admin/smartling-toggle-flag")
async def smartling_toggle_flag(data: dict = Body(...)):
    row_id = data.get("id")
    flag = data.get("flag")
    if row_id is None or flag is None:
        return JSONResponse(status_code=400, content={"success": False, "message": "Missing id or flag"})
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("UPDATE smartling_translations SET flag=? WHERE id=?", (flag, row_id))
        conn.commit()
    return {"success": True}

@app.post("/evaluate-translation", response_model=TranslationEvalResponse)
def evaluate_translation(req: TranslationEvalRequest):
    import re, json
    system_prompt = (
    "You are an evaluation assistant. The user will send in a source and translation. Compare the two and evaluate the translation, providing a confidence score with a reason. Ensure that the given translation sounds natural. If there are any ways to improve the translation, include suggestions and provide an example sentence in Japanese. The reason and example SHOULD be included inside the {reason}. ONLY return a valid JSON object with keys 'score' (int, 0-100) and 'reason' (string). "
    "Do NOT include any explanation or text outside the JSON. Example: {\"score\": 95, \"reason\": \"Accurate and natural translation.\"} ONLY return one JSON object with the keys 'score' and 'reason'. "
)
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f'{{"source": "{req.source}", "translation": "{req.translation}"}}'},
        {"role": "user", "content": f'{{"source": "{req.source}", "translation": "{req.translation}"}}'},
    ]
    output = pipe(messages, **generation_args)
    raw = output[0]['generated_text']
    try:
        result = json.loads(raw)
    except Exception:
        match = re.search(r'\{.*\}', raw, re.DOTALL)
        if match:
            try:
                result = json.loads(match.group(0))
            except Exception as e2:
                return TranslationEvalResponse(score=0, reason=f"Model output parse error: {str(e2)} | Raw: {raw}")
        else:
            return TranslationEvalResponse(score=0, reason=f"Model output parse error: No JSON found | Raw: {raw}")
    try:
        score = int(result.get('score', 0))
        reason = result.get('reason', '')
    except Exception as e:
        return TranslationEvalResponse(score=0, reason=f"Model output parse error: {str(e)} | Raw: {raw}")
    try:
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            c.execute("UPDATE smartling_translations SET confidence=?, reason=? WHERE parsed_string_text=? AND translation=?", (score, reason, req.source, req.translation))
            conn.commit()
    except Exception as db_exc:
        print(f"[DB ERROR] Could not update confidence/reason: {db_exc}")
    print(f"[Translation Eval] Score: {score}, Reason: {reason}")
    return TranslationEvalResponse(score=score, reason=reason)

def get_setting(key: str, default=None):
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("SELECT value FROM settings WHERE key=?", (key,))
        row = c.fetchone()
        return row[0] if row else default

def set_setting(key: str, value: str):
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
        conn.commit()

@app.post("/admin/set-model-download-flag")
def set_model_download_flag(data: dict = Body(...)):
    flag = data.get("download_model", False)
    set_setting("download_model", "true" if flag else "false")
    return {"success": True, "download_model": flag}

@app.get("/admin/get-model-download-flag")
def get_model_download_flag():
    flag = get_setting("download_model", "false") == "true"
    return {"download_model": flag}
