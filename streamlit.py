import streamlit as st
import pandas as pd
import chromadb
import uuid, re, io, time
import PyPDF2
from docx import Document
from groq import Groq
from sentence_transformers import SentenceTransformer

# ── CONFIG ────────────────────────────────────────────────────────────────────
from dotenv import load_dotenv
import os

load_dotenv()   # 👈 this line is IMPORTANT

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
MODEL        = "moonshotai/kimi-k2-instruct-0905"

st.set_page_config(page_title="SmartHire · Multi-Candidate RAG",
                   page_icon="🎯", layout="wide")

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:wght@300;400;500&family=JetBrains+Mono:wght@400;500&display=swap');

*, *::before, *::after { box-sizing: border-box; }

html, body, [data-testid="stAppViewContainer"] {
    background: #07080f;
    color: #ddd8f0;
    font-family: 'DM Sans', sans-serif;
}
[data-testid="stAppViewContainer"] {
    background:
        radial-gradient(ellipse 60% 40% at 15% 5%,  rgba(99,51,220,0.18) 0%, transparent 60%),
        radial-gradient(ellipse 50% 35% at 85% 95%, rgba(16,185,129,0.10) 0%, transparent 60%),
        #07080f;
}
[data-testid="stSidebar"] {
    background: rgba(10,8,20,0.97) !important;
    border-right: 1px solid rgba(99,51,220,0.2);
}

h1 {
    font-family: 'Syne', sans-serif !important;
    font-size: 2.4rem !important;
    font-weight: 800 !important;
    background: linear-gradient(120deg, #a78bfa 0%, #60a5fa 50%, #34d399 100%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    background-clip: text;
    letter-spacing: -0.02em;
    margin-bottom: 0 !important;
}
h2, h3 {
    font-family: 'Syne', sans-serif !important;
    color: #c4b5fd !important;
}

/* ── step cards ── */
.step-card {
    background: rgba(99,51,220,0.06);
    border: 1px solid rgba(99,51,220,0.22);
    border-radius: 18px;
    padding: 1.4rem 1.5rem;
    height: 100%;
}
.step-badge {
    display: inline-block;
    background: linear-gradient(135deg, #6333dc, #2563eb);
    color: #fff;
    font-size: 0.68rem; font-weight: 700;
    letter-spacing: 0.12em; text-transform: uppercase;
    padding: 0.18rem 0.75rem; border-radius: 20px;
    margin-bottom: 0.6rem;
}

/* ── leaderboard ── */
.lb-header {
    display: grid;
    grid-template-columns: 48px 1fr 110px 130px 100px;
    gap: 0.5rem;
    padding: 0.6rem 1.2rem;
    background: rgba(99,51,220,0.12);
    border-radius: 10px 10px 0 0;
    font-size: 0.75rem; font-weight: 600;
    letter-spacing: 0.08em; text-transform: uppercase;
    color: #9b8ec4;
    margin-bottom: 2px;
}
.lb-row {
    display: grid;
    grid-template-columns: 48px 1fr 110px 130px 100px;
    gap: 0.5rem;
    padding: 0.85rem 1.2rem;
    background: rgba(15,12,30,0.7);
    border: 1px solid rgba(99,51,220,0.14);
    border-radius: 10px;
    margin-bottom: 4px;
    align-items: center;
    transition: border-color 0.2s;
}
.lb-row:hover { border-color: rgba(99,51,220,0.4); }

.rank-badge { font-family:'Syne',sans-serif; font-weight:800; font-size:1.1rem; color:#7c3aed; }
.cand-name  { font-weight:600; font-size:1rem; color:#e8e4f8; }
.cand-email { font-size:0.78rem; color:#7c6fa0; margin-top:2px; }

.score-bar-wrap { display:flex; align-items:center; gap:8px; }
.score-bar-bg   { flex:1; height:6px; background:rgba(99,51,220,0.15); border-radius:4px; overflow:hidden; }
.score-bar-fill { height:100%; border-radius:4px; }
.score-num { font-family:'JetBrains Mono',monospace; font-size:0.88rem; font-weight:500; color:#a78bfa; min-width:32px; }

.verdict-pill {
    display:inline-block; padding:0.25rem 0.8rem;
    border-radius:20px; font-size:0.78rem; font-weight:700;
    letter-spacing:0.05em; white-space:nowrap;
}
.v-strong   { background:rgba(16,185,129,0.15); color:#34d399; border:1px solid rgba(16,185,129,0.35); }
.v-potential{ background:rgba(245,158,11,0.15); color:#fbbf24; border:1px solid rgba(245,158,11,0.35); }
.v-notfit   { background:rgba(239,68,68,0.12);  color:#f87171; border:1px solid rgba(239,68,68,0.3); }
.v-pending  { background:rgba(107,114,128,0.15);color:#9ca3af; border:1px solid rgba(107,114,128,0.3); }

/* ── expandable card ── */
.detail-card {
    background: rgba(12,9,25,0.85);
    border: 1px solid rgba(99,51,220,0.22);
    border-radius: 14px;
    padding: 1.4rem 1.6rem;
    margin-top: 0.5rem;
    font-size: 0.93rem;
    line-height: 1.75;
    color: #ccc8e8;
}

/* ── progress / status ── */
.prog-row {
    display:flex; align-items:center; gap:10px;
    padding:0.45rem 0;
    font-size:0.88rem; color:#a09ab8;
    border-bottom:1px solid rgba(99,51,220,0.1);
}
.dot-done { color:#34d399; }
.dot-wait { color:#4b5563; }
.dot-run  { color:#fbbf24; }

.info-chip {
    display:inline-block;
    background:rgba(99,51,220,0.1);
    border:1px solid rgba(99,51,220,0.25);
    border-radius:8px; padding:0.35rem 0.85rem;
    font-size:0.82rem; color:#b5aadc; margin:0.2rem 0;
}

/* ── buttons ── */
.stButton > button {
    background: linear-gradient(135deg,#6333dc,#2563eb) !important;
    color:#fff !important; border:none !important;
    border-radius:12px !important;
    padding:0.65rem 2rem !important;
    font-family:'DM Sans',sans-serif !important;
    font-weight:600 !important; font-size:0.95rem !important;
    width:100%; transition:all 0.2s !important;
}
.stButton > button:hover {
    transform:translateY(-2px) !important;
    box-shadow:0 8px 24px rgba(99,51,220,0.4) !important;
}
.stButton > button:disabled {
    background: rgba(99,51,220,0.2) !important;
    color:#6b7280 !important;
}

.stTextArea textarea, .stTextInput input {
    background:rgba(10,8,20,0.8) !important;
    border:1px solid rgba(99,51,220,0.28) !important;
    border-radius:12px !important;
    color:#e0dcf4 !important;
    font-family:'DM Sans',sans-serif !important;
}
.stFileUploader {
    background:rgba(10,8,20,0.5) !important;
    border:1px dashed rgba(99,51,220,0.32) !important;
    border-radius:12px !important;
}
[data-testid="stExpander"] {
    background:rgba(12,9,25,0.7) !important;
    border:1px solid rgba(99,51,220,0.18) !important;
    border-radius:12px !important;
}
</style>
""", unsafe_allow_html=True)


# ── HELPERS ───────────────────────────────────────────────────────────────────
@st.cache_resource(show_spinner=False)
def load_embedder():
    return SentenceTransformer("all-MiniLM-L6-v2")

def fresh_collection(client, name):
    try: client.delete_collection(name)
    except Exception: pass
    return client.create_collection(name)

def embed(texts, model):
    return model.encode(texts, show_progress_bar=False).tolist()

def parse_pdf(f):
    import io
    # Always build a fresh BytesIO — PyPDF2 needs tell() and full seek support
    f.seek(0)
    buf = io.BytesIO(f.read())
    r = PyPDF2.PdfReader(buf)
    return "\n".join(p.extract_text() or "" for p in r.pages)

def parse_docx(f):
    import io
    f.seek(0)
    buf = io.BytesIO(f.read())
    d = Document(buf)
    return "\n".join(p.text for p in d.paragraphs if p.text.strip())

def parse_resume_file(f):
    """Parse resume — works with both UploadedFile and BytesFile objects."""
    n = f.name.lower()
    if   n.endswith(".pdf"):  return parse_pdf(f)
    elif n.endswith(".docx"): return parse_docx(f)
    elif n.endswith(".txt"):
        f.seek(0)
        return f.read().decode("utf-8", errors="ignore")
    return ""

def chunk_text(text, size=350, overlap=70):
    words = text.split()
    out, i = [], 0
    while i < len(words):
        out.append(" ".join(words[i:i+size]))
        i += size - overlap
    return [c for c in out if len(c.strip()) > 30]

def slug(name: str) -> str:
    """Arjun Sharma → arjun_sharma — for filename matching."""
    return re.sub(r"\s+", "_", name.strip().lower())

def resume_slug(filename: str) -> str:
    """ArjunSharma.pdf → arjun_sharma"""
    stem = filename.rsplit(".", 1)[0]
    # insert underscore before each capital (CamelCase → camel_case)
    s = re.sub(r"(?<=[a-z])(?=[A-Z])", "_", stem).lower()
    return s

def match_resume_to_candidates(resume_files, csv_names):
    """Returns dict: csv_name → uploaded file (or None)."""
    mapping = {}
    slugs   = {slug(n): n for n in csv_names}
    used    = set()
    for f in resume_files:
        rs = resume_slug(f.name)
        if rs in slugs and slugs[rs] not in used:
            mapping[slugs[rs]] = f
            used.add(slugs[rs])
    # candidates with no resume
    for n in csv_names:
        if n not in mapping:
            mapping[n] = None
    return mapping

def ingest(col, chunks, source, embedder):
    if not chunks: return
    embs = embed(chunks, embedder)
    ids  = [f"{source}_{uuid.uuid4().hex[:6]}" for _ in chunks]
    meta = [{"source": source}] * len(chunks)
    col.add(documents=chunks, embeddings=embs, ids=ids, metadatas=meta)

def retrieve(col, query, embedder, k=8):
    if col.count() == 0: return []
    q_emb = embed([query], embedder)[0]
    res   = col.query(query_embeddings=[q_emb], n_results=min(k, col.count()))
    return res["documents"][0] if res["documents"] else []

def score_from_text(text):
    """Extract numeric score from LLM response."""
    m = re.search(r"(\d{1,3})\s*/\s*100", text)
    return int(m.group(1)) if m else 0

def verdict_from_text(text):
    if "STRONG FIT"    in text: return "STRONG FIT"
    if "POTENTIAL FIT" in text: return "POTENTIAL FIT"
    if "NOT A FIT"     in text: return "NOT A FIT"
    return "UNKNOWN"

def bar_color(score):
    if score >= 75: return "#10b981"
    if score >= 50: return "#f59e0b"
    return "#ef4444"

def verdict_class(v):
    if v == "STRONG FIT":    return "v-strong"
    if v == "POTENTIAL FIT": return "v-potential"
    if v == "NOT A FIT":     return "v-notfit"
    return "v-pending"

def analyse_candidate(name, csv_row, resume_text, job_desc, embedder, chroma_client):
    col = fresh_collection(chroma_client, f"c_{slug(name)}")
    # structured: CSV row
    csv_chunk = "ACADEMIC RECORD — " + " | ".join(f"{k}: {v}" for k, v in csv_row.items())
    ingest(col, [csv_chunk], "marks", embedder)
    # unstructured: resume
    if resume_text.strip():
        ingest(col, chunk_text(resume_text), "resume", embedder)
    # retrieve
    ctx = retrieve(col, job_desc, embedder, k=10)
    if not ctx:
        return None, None, "No data"
    # LLM
    client = Groq(api_key=GROQ_API_KEY)
    system = ("You are a senior HR analyst. Evaluate the candidate for the role. "
              "Be structured, concise, and give a clear FINAL VERDICT.")
    user = f"""## Job Description
{job_desc}

## Candidate Data
{chr(10).join(ctx)}

## Task
Evaluate **{name}** for this job.

### 📊 Academic Performance
(Summarise marks, GPA, strengths/weaknesses)

### 💼 Skills & Experience Match
(Map their skills/projects to job requirements)

### ✅ Key Strengths  (3–4 bullets)

### ⚠️ Gaps or Concerns  (2–3 bullets)

### 🎯 FINAL VERDICT
Start with exactly: **STRONG FIT** / **POTENTIAL FIT** / **NOT A FIT**
Then 2 sentences of justification.

### 📈 Match Score
**XX / 100** — one line reason.
"""
    resp = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "system", "content": system},
                  {"role": "user",   "content": user}],
        temperature=0.25, max_tokens=900,
    )
    answer  = resp.choices[0].message.content
    score   = score_from_text(answer)
    verdict = verdict_from_text(answer)
    return score, verdict, answer


# ─── UI ───────────────────────────────────────────────────────────────────────
st.markdown("# 🎯 SmartHire")
st.markdown("<p style='color:#7059a0;font-size:1rem;margin-top:0'>Multi-Candidate RAG · Structured + Unstructured Intelligence</p>",
            unsafe_allow_html=True)
st.markdown("---")

embedder = load_embedder()

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Status")
    jd_ok  = "job_desc"  in st.session_state
    csv_ok = "cand_df"   in st.session_state
    res_ok = "res_map"   in st.session_state

    for ok, label in [(jd_ok,"Job Description"),(csv_ok,"Candidates CSV"),(res_ok,"Resumes")]:
        ic = "✅" if ok else "⬜"
        st.markdown(f"<div class='info-chip'>{ic} {label}</div>", unsafe_allow_html=True)

    if jd_ok and csv_ok and res_ok:
        st.success("Ready to analyse!")
    else:
        st.info("Complete all 3 inputs.")
    st.markdown("---")
    st.markdown("**Model** `kimi-k2-instruct`")
    st.markdown("**DB** ChromaDB in-memory")
    st.markdown("**Embed** MiniLM-L6-v2")
    st.markdown("**Naming** `FirstnameLastname.pdf`")

# ── Input row ─────────────────────────────────────────────────────────────────
c1, c2, c3 = st.columns(3, gap="medium")

with c1:
    st.markdown("<div class='step-card'>", unsafe_allow_html=True)
    st.markdown("<span class='step-badge'>Step 1</span>", unsafe_allow_html=True)
    st.markdown("### 📋 Job Description")
    jd = st.text_area("JD", height=240, label_visibility="collapsed",
                       placeholder="Paste full job description here…")
    if st.button("💾 Save JD", key="sjd"):
        if jd.strip():
            st.session_state.job_desc = jd.strip()
            st.success("Saved!")
        else:
            st.warning("Please enter a job description.")
    st.markdown("</div>", unsafe_allow_html=True)

with c2:
    st.markdown("<div class='step-card'>", unsafe_allow_html=True)
    st.markdown("<span class='step-badge'>Step 2</span>", unsafe_allow_html=True)
    st.markdown("### 📊 Candidates CSV")
    csv_f = st.file_uploader("CSV", type=["csv"], label_visibility="collapsed", key="csv_up")
    if csv_f:
        df = pd.read_csv(csv_f)
        st.session_state.cand_df = df
        name_col = next((c for c in df.columns if "name" in c.lower()), df.columns[0])
        st.session_state.name_col = name_col
        st.success(f"✅ {len(df)} candidates loaded")
        with st.expander("Preview"):
            st.dataframe(df.head(), width='stretch')
    st.markdown("</div>", unsafe_allow_html=True)

with c3:
    st.markdown("<div class='step-card'>", unsafe_allow_html=True)
    st.markdown("<span class='step-badge'>Step 3</span>", unsafe_allow_html=True)
    st.markdown("### 📄 Resumes (multi-upload)")

    # Read uploaded files immediately into memory as bytes so they
    # survive Streamlit re-runs (widget state resets on each interaction)
    res_files_raw = st.file_uploader(
        "Upload all resumes at once (PDF / DOCX / TXT)",
        type=["pdf", "docx", "txt"],
        accept_multiple_files=True,
        label_visibility="collapsed",
        key="res_up",
    )

    # Persist file bytes in session_state the moment files appear
    if res_files_raw:
        saved = []
        for f in res_files_raw:
            data = f.read()          # read bytes NOW before re-run clears them
            saved.append({"name": f.name, "data": data})
        st.session_state.saved_resumes = saved

    # Work from the persisted copy so re-runs don't lose files
    saved_resumes = st.session_state.get("saved_resumes", [])

    if saved_resumes and "cand_df" in st.session_state:
        # Rebuild file-like objects from bytes for matching
        class BytesFile:
            def __init__(self, name, data):
                self.name = name
                self._data = data
                self._buf  = io.BytesIO(data)
            def read(self, *a):  return self._buf.read(*a)
            def seek(self, *a):  return self._buf.seek(*a)
            def tell(self):      return self._buf.tell()

        file_objs = [BytesFile(r["name"], r["data"]) for r in saved_resumes]
        names     = st.session_state.cand_df[st.session_state.name_col].tolist()
        res_map   = match_resume_to_candidates(file_objs, names)
        st.session_state.res_map      = res_map
        st.session_state.res_file_map = {r["name"]: r["data"] for r in saved_resumes}

        matched = sum(1 for v in res_map.values() if v is not None)
        st.success(f"✅ {len(saved_resumes)} files · {matched}/{len(names)} matched")
        with st.expander("Matching preview"):
            for name, f in res_map.items():
                icon = "🟢" if f else "🔴"
                fname = f.name if f else "no resume"
                st.markdown(f"{icon} **{name}** → `{fname}`")

    elif saved_resumes:
        st.info(f"📎 {len(saved_resumes)} files held — upload CSV first to match names.")
    else:
        st.markdown("<p style='color:#6b7280;font-size:0.85rem'>Select multiple files using Ctrl/Cmd+click</p>",
                    unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

# ── Analyse button ─────────────────────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
can_run = jd_ok and csv_ok and res_ok
bc1, bc2, bc3 = st.columns([1,2,1])
with bc2:
    run_btn = st.button("🚀 Rank All Candidates", disabled=not can_run, key="run")

if not can_run:
    st.markdown("<p style='text-align:center;color:#4b5563;font-size:0.85rem'>Complete all 3 steps to enable analysis</p>",
                unsafe_allow_html=True)

# ── Analysis loop ──────────────────────────────────────────────────────────────
if run_btn:
    df        = st.session_state.cand_df
    name_col  = st.session_state.name_col
    res_map   = st.session_state.res_map
    jd_text   = st.session_state.job_desc
    names     = df[name_col].tolist()

    st.markdown("---")
    st.markdown("## ⏳ Analysing Candidates…")

    chroma_client = chromadb.Client()
    results       = {}   # name → {score, verdict, report}

    prog_placeholder = st.empty()
    status_lines = {n: "wait" for n in names}

    def render_progress():
        html = "<div style='background:rgba(10,8,20,0.6);border:1px solid rgba(99,51,220,0.2);border-radius:14px;padding:1rem 1.4rem'>"
        icons = {"wait":"⬜","run":"🔄","done":"✅","fail":"❌"}
        for n, s in status_lines.items():
            html += f"<div class='prog-row'><span>{icons[s]}</span><span><b>{n}</b></span></div>"
        html += "</div>"
        prog_placeholder.markdown(html, unsafe_allow_html=True)

    render_progress()

    for name in names:
        status_lines[name] = "run"
        render_progress()

        row        = df[df[name_col] == name].iloc[0].to_dict()
        res_file   = res_map.get(name)
        res_text   = parse_resume_file(res_file) if res_file else ""

        try:
            score, verdict, report = analyse_candidate(
                name, row, res_text, jd_text, embedder, chroma_client)
            results[name] = {"score": score or 0, "verdict": verdict, "report": report,
                              "email": row.get("Email", "—"), "has_resume": bool(res_file)}
            status_lines[name] = "done"
        except Exception as e:
            results[name] = {"score": 0, "verdict": "UNKNOWN",
                              "report": f"Error: {e}", "email": "—", "has_resume": False}
            status_lines[name] = "fail"

        render_progress()
        time.sleep(0.4)   # small pause to avoid rate-limit bursts

    prog_placeholder.empty()

    # ── Sort by score ──────────────────────────────────────────────────────────
    ranked = sorted(results.items(), key=lambda x: x[1]["score"], reverse=True)

    st.markdown("---")
    st.markdown("## 🏆 Candidate Leaderboard")

    # download CSV
    rows_dl = []
    for i, (n, d) in enumerate(ranked, 1):
        rows_dl.append({"Rank": i, "Name": n, "Email": d["email"],
                        "Score": d["score"], "Verdict": d["verdict"]})
    dl_df  = pd.DataFrame(rows_dl)
    csv_dl = dl_df.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Download Results CSV", csv_dl,
                       file_name="smarthire_results.csv", mime="text/csv")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Header ─────────────────────────────────────────────────────────────────
    st.markdown("""
    <div class='lb-header'>
        <div>Rank</div>
        <div>Candidate</div>
        <div>Score</div>
        <div>Verdict</div>
        <div>Resume</div>
    </div>""", unsafe_allow_html=True)

    # ── Rows ───────────────────────────────────────────────────────────────────
    rank_icons = {1: "🥇", 2: "🥈", 3: "🥉"}
    for i, (name, data) in enumerate(ranked, 1):
        sc   = data["score"]
        ver  = data["verdict"]
        vc   = verdict_class(ver)
        bc   = bar_color(sc)
        ri   = rank_icons.get(i, f"#{i}")
        res_badge = "✅ Yes" if data["has_resume"] else "❌ No"

        st.markdown(f"""
        <div class='lb-row'>
            <div class='rank-badge'>{ri}</div>
            <div>
                <div class='cand-name'>{name}</div>
                <div class='cand-email'>{data['email']}</div>
            </div>
            <div class='score-bar-wrap'>
                <div class='score-bar-bg'>
                    <div class='score-bar-fill' style='width:{sc}%;background:{bc}'></div>
                </div>
                <span class='score-num'>{sc}</span>
            </div>
            <div><span class='verdict-pill {vc}'>{ver}</span></div>
            <div style='font-size:0.82rem;color:#9b8ec4'>{res_badge}</div>
        </div>""", unsafe_allow_html=True)

        with st.expander(f"📋 Full Report — {name}"):
            st.markdown(f"<div class='detail-card'>{data['report']}</div>",
                        unsafe_allow_html=True)

    # ── Summary stats ──────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### 📈 Summary")
    sc1, sc2, sc3, sc4 = st.columns(4)
    verdicts = [d["verdict"] for _, d in ranked]
    sc1.metric("Total Candidates", len(ranked))
    sc2.metric("Strong Fit",    verdicts.count("STRONG FIT"))
    sc3.metric("Potential Fit", verdicts.count("POTENTIAL FIT"))
    sc4.metric("Not a Fit",     verdicts.count("NOT A FIT"))

    # ── Top pick highlight ─────────────────────────────────────────────────────
    if ranked:
        top_name, top_data = ranked[0]
        st.markdown(f"""
        <div style='background:linear-gradient(135deg,rgba(16,185,129,0.1),rgba(5,150,105,0.06));
                    border:1.5px solid rgba(16,185,129,0.3);border-radius:16px;
                    padding:1.2rem 1.8rem;margin-top:1rem;text-align:center'>
            <div style='font-size:0.75rem;letter-spacing:0.12em;text-transform:uppercase;
                        color:#6ee7b7;margin-bottom:4px'>🏆 Top Recommended Candidate</div>
            <div style='font-family:Syne,sans-serif;font-size:1.6rem;font-weight:800;color:#34d399'>
                {top_name}
            </div>
            <div style='color:#6ee7b7;font-size:0.9rem;margin-top:4px'>
                Score: {top_data['score']}/100 · {top_data['verdict']}
            </div>
        </div>""", unsafe_allow_html=True)