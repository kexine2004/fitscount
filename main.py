"""
Fitscout — FastAPI Backend
Run: uvicorn main:app --reload --port 8000
"""

from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

import pandas as pd
import chromadb
import uuid, re, io, os, json, time
from typing import List

import PyPDF2
from docx import Document as DocxDocument
from groq import Groq
from sentence_transformers import SentenceTransformer

from dotenv import load_dotenv
import os

load_dotenv()   # 👈 this line is IMPORTANT

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
MODEL = "moonshotai/kimi-k2-instruct-0905"

app = FastAPI(title="Fitscout API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_methods=["*"], allow_headers=["*"],
)

# serve static HTML
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def root():
    return FileResponse("static/index.html")

# ── GLOBALS (loaded once) ──────────────────────────────────────────────────────
print("Loading sentence embedder…")
EMBEDDER = SentenceTransformer("all-MiniLM-L6-v2")
print("Embedder ready.")

# ── HELPERS ───────────────────────────────────────────────────────────────────
def embed(texts: list) -> list:
    return EMBEDDER.encode(texts, show_progress_bar=False).tolist()

def fresh_col(client, name: str):
    try: client.delete_collection(name)
    except: pass
    return client.create_collection(name)

def ingest(col, chunks: list, source: str):
    if not chunks: return
    embs = embed(chunks)
    ids  = [f"{source}_{uuid.uuid4().hex[:6]}" for _ in chunks]
    meta = [{"source": source}] * len(chunks)
    col.add(documents=chunks, embeddings=embs, ids=ids, metadatas=meta)

def retrieve(col, query: str, k: int = 10) -> list:
    if col.count() == 0: return []
    q_emb = embed([query])[0]
    res   = col.query(query_embeddings=[q_emb], n_results=min(k, col.count()))
    return res["documents"][0] if res["documents"] else []

def chunk_text(text: str, size=350, overlap=70) -> list:
    words = text.split()
    out, i = [], 0
    while i < len(words):
        out.append(" ".join(words[i:i+size]))
        i += size - overlap
    return [c for c in out if len(c.strip()) > 30]

def parse_pdf(data: bytes) -> str:
    buf = io.BytesIO(data)
    r = PyPDF2.PdfReader(buf)
    return "\n".join(p.extract_text() or "" for p in r.pages)

def parse_docx(data: bytes) -> str:
    buf = io.BytesIO(data)
    d = DocxDocument(buf)
    return "\n".join(p.text for p in d.paragraphs if p.text.strip())

def parse_resume_bytes(filename: str, data: bytes) -> str:
    n = filename.lower()
    if   n.endswith(".pdf"):  return parse_pdf(data)
    elif n.endswith(".docx"): return parse_docx(data)
    elif n.endswith(".txt"):  return data.decode("utf-8", errors="ignore")
    return ""

def slug(name: str) -> str:
    return re.sub(r"\s+", "_", name.strip().lower())

def resume_slug(filename: str) -> str:
    stem = filename.rsplit(".", 1)[0]
    s = re.sub(r"(?<=[a-z])(?=[A-Z])", "_", stem).lower()
    return s

def match_resumes(resume_map: dict, csv_names: list) -> dict:
    """csv_name → resume bytes (or None)"""
    slugs  = {slug(n): n for n in csv_names}
    result = {n: None for n in csv_names}
    for fname, data in resume_map.items():
        rs = resume_slug(fname)
        if rs in slugs:
            result[slugs[rs]] = (fname, data)
    return result

def score_from_text(text: str) -> int:
    m = re.search(r"(\d{1,3})\s*/\s*100", text)
    return int(m.group(1)) if m else 0

def verdict_from_text(text: str) -> str:
    if "STRONG FIT"    in text: return "STRONG FIT"
    if "POTENTIAL FIT" in text: return "POTENTIAL FIT"
    if "NOT A FIT"     in text: return "NOT A FIT"
    return "UNKNOWN"

# ── NLP INSIGHTS ──────────────────────────────────────────────────────────────
def extract_nlp_insights(candidates_results: list, job_desc: str) -> dict:
    """
    Ask LLM to generate cross-candidate NLP insights:
    - Skill frequency across all resumes
    - Cohort strengths & gaps
    - Sentiment/tone of candidate profiles
    - Job-fit keyword overlap
    - Recommended interview focus areas per candidate
    """
    client = Groq(api_key=GROQ_API_KEY)

    summary_block = "\n".join(
        f"- {r['name']} | Score:{r['score']}/100 | Verdict:{r['verdict']} | "
        f"GPA:{r.get('gpa','?')} | Skills snippet: {r.get('skills_hint','')}"
        for r in candidates_results
    )

    prompt = f"""You are an expert HR data scientist. Analyse this cohort of {len(candidates_results)} candidates for the job below.

## Job Description
{job_desc}

## Candidate Summary
{summary_block}

Return ONLY a valid JSON object (no markdown, no extra text) with this exact structure:
{{
  "top_skills_in_cohort": ["skill1","skill2","skill3","skill4","skill5"],
  "missing_skills_in_cohort": ["skill1","skill2","skill3"],
  "cohort_strength": "2-3 sentence summary of what this batch does well collectively",
  "cohort_gap": "2-3 sentence summary of what the whole batch is missing",
  "sentiment_summary": "2-3 sentences on the overall tone and confidence level across candidate profiles",
  "job_keyword_overlap": {{
    "high_overlap": ["keyword1","keyword2"],
    "low_overlap": ["keyword1","keyword2"]
  }},
  "interview_focus": [
    {{"name": "CandidateName", "focus": "What to probe in interview — 1 sentence"}},
    {{"name": "CandidateName", "focus": "..."}}
  ],
  "hiring_recommendation": "Overall 3-4 sentence hiring strategy recommendation for HR"
}}"""

    resp = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
        max_tokens=1200,
    )
    raw = resp.choices[0].message.content.strip()
    # strip markdown fences if present
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)
    try:
        return json.loads(raw)
    except Exception:
        return {"raw": raw, "parse_error": True}

# ── CANDIDATE ANALYSIS ────────────────────────────────────────────────────────
def analyse_one(name: str, csv_row: dict, resume_text: str,
                job_desc: str, chroma_client) -> dict:
    col = fresh_col(chroma_client, f"c_{slug(name)[:20]}")

    csv_chunk = "ACADEMIC RECORD — " + " | ".join(f"{k}: {v}" for k, v in csv_row.items())
    ingest(col, [csv_chunk], "marks")
    if resume_text.strip():
        ingest(col, chunk_text(resume_text), "resume")

    ctx = retrieve(col, job_desc, k=10)
    if not ctx:
        return {"score": 0, "verdict": "UNKNOWN", "report": "No data available."}

    client = Groq(api_key=GROQ_API_KEY)
    system = (
        "You are a senior HR analyst with 15 years of experience. "
        "Evaluate candidates holistically. Be concise and structured."
    )
    user = f"""## Job Description
{job_desc}

## Candidate Data
{chr(10).join(ctx)}

## Task — Evaluate {name}

### 📊 Academic Performance
Summarise marks, GPA, strengths/weaknesses in 3-4 sentences.

### 💼 Skills & Experience Match
Map their skills/projects/experience to job requirements.

### ✅ Key Strengths
- (3-4 bullet points)

### ⚠️ Gaps or Concerns
- (2-3 bullet points)

### 🔬 NLP Communication Analysis
Analyse the tone, clarity, and vocabulary sophistication of their resume text.
Comment on: confidence level, use of action verbs, quantified achievements, keyword density.

### 🎯 FINAL VERDICT
Start with exactly one of: **STRONG FIT** / **POTENTIAL FIT** / **NOT A FIT**
Then 2 sentences of justification.

### 📈 Match Score
**XX / 100** — one line reason.
"""

    resp = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "system", "content": system},
                  {"role": "user",   "content": user}],
        temperature=0.25,
        max_tokens=1000,
    )
    answer  = resp.choices[0].message.content
    score   = score_from_text(answer)
    verdict = verdict_from_text(answer)

    # extract a skills hint for NLP insights
    skills_hint = ""
    m = re.search(r"Skills.*?:(.*?)(\n###|\Z)", answer, re.DOTALL | re.IGNORECASE)
    if m:
        skills_hint = m.group(1).strip()[:120]

    return {
        "score":       score,
        "verdict":     verdict,
        "report":      answer,
        "skills_hint": skills_hint,
        "gpa":         csv_row.get("GPA", "?"),
    }

# ── API ROUTES ────────────────────────────────────────────────────────────────
@app.post("/api/analyse")
async def analyse(
    job_description: str = Form(...),
    csv_file:        UploadFile = File(...),
    resumes:         List[UploadFile] = File(...),
):
    # 1. Parse CSV
    csv_bytes = await csv_file.read()
    try:
        df = pd.read_csv(io.BytesIO(csv_bytes))
    except Exception as e:
        raise HTTPException(400, f"CSV parse error: {e}")

    name_col = next((c for c in df.columns if "name" in c.lower()), df.columns[0])
    names    = df[name_col].tolist()

    # 2. Read resumes into memory
    resume_map = {}
    for r in resumes:
        data = await r.read()
        resume_map[r.filename] = data

    # 3. Match resumes → CSV names
    matched = match_resumes(resume_map, names)

    # 4. Analyse each candidate
    chroma_client = chromadb.Client()
    results       = []
    errors        = []

    for name in names:
        row        = df[df[name_col] == name].iloc[0].to_dict()
        res_info   = matched.get(name)
        res_text   = ""
        if res_info:
            fname, rdata = res_info
            res_text = parse_resume_bytes(fname, rdata)

        try:
            out = analyse_one(name, row, res_text, job_description, chroma_client)
            results.append({
                "name":        name,
                "email":       str(row.get("Email", "—")),
                "score":       out["score"],
                "verdict":     out["verdict"],
                "report":      out["report"],
                "has_resume":  res_info is not None,
                "gpa":         str(row.get("GPA", "?")),
                "skills_hint": out.get("skills_hint", ""),
            })
        except Exception as e:
            errors.append({"name": name, "error": str(e)})
            results.append({
                "name": name, "email": str(row.get("Email","—")),
                "score": 0, "verdict": "ERROR",
                "report": f"Analysis failed: {e}",
                "has_resume": False, "gpa": "?", "skills_hint": "",
            })
        time.sleep(0.3)

    # 5. Sort by score
    results.sort(key=lambda x: x["score"], reverse=True)
    for i, r in enumerate(results, 1):
        r["rank"] = i

    # 6. NLP cohort insights
    nlp_insights = {}
    try:
        nlp_insights = extract_nlp_insights(results, job_description)
    except Exception as e:
        nlp_insights = {"error": str(e)}

    # 7. Summary stats
    verdicts = [r["verdict"] for r in results]
    summary = {
        "total":     len(results),
        "strong":    verdicts.count("STRONG FIT"),
        "potential": verdicts.count("POTENTIAL FIT"),
        "not_fit":   verdicts.count("NOT A FIT"),
        "top_candidate": results[0]["name"] if results else "",
        "top_score":     results[0]["score"] if results else 0,
        "errors":        errors,
    }

    return JSONResponse({
        "candidates":   results,
        "summary":      summary,
        "nlp_insights": nlp_insights,
    })

# ── CHAT ENDPOINT (STREAMING) ─────────────────────────────────────────────────
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

class ChatMessage(BaseModel):
    role: str      # "user" or "assistant"
    content: str

class ChatRequest(BaseModel):
    messages:    list[ChatMessage]
    context:     str   # full analysis dump passed from frontend

@app.post("/api/chat")
async def chat_stream(req: ChatRequest):
    """
    Streaming chat endpoint.
    The frontend passes:
      - context: stringified analysis results (JD + all candidate data)
      - messages: full conversation history
    """
    client = Groq(api_key=GROQ_API_KEY)

    system_prompt = f"""You are Fitscout AI — a senior hiring consultant embedded inside the Fitscout recruiting platform.

You have just completed a full AI analysis of a batch of candidates for a job role. All analysis data is provided below.

Your job is to answer the HR manager's questions about the candidates, the role, and the hiring decision. Be concise, direct, and insightful. Use bullet points where helpful. Never make up data — only use what's in the analysis context.

You can help with:
- Comparing candidates
- Explaining scores and verdicts
- Drafting interview questions or invite emails  
- Suggesting shortlists or next steps
- Flagging red flags or hidden strengths
- Simulating "what if" scenarios based on the data

─────────────────────────────────────────
FULL ANALYSIS CONTEXT
─────────────────────────────────────────
{req.context}
─────────────────────────────────────────
"""

    groq_messages = [{"role": "system", "content": system_prompt}]
    for m in req.messages:
        groq_messages.append({"role": m.role, "content": m.content})

    def generate():
        # Groq SDK: pass stream=True to create_with_streaming
        stream = client.chat.completions.create(
            model=MODEL,
            messages=groq_messages,
            temperature=0.35,
            max_tokens=1000,
            stream=True,
        )
        for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield f"data: {json.dumps({'text': delta})}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        }
    )