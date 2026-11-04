"""Safe AskDuka preview with a small, non-AI catalog Q&A demonstration."""
import re
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

app = FastAPI(title="AskDuka Development Preview")
FALLBACK = "I don't have that information. Please ask the business owner."
STOP = {"the", "and", "you", "your", "have", "what", "does", "are", "for", "how", "can", "with", "about", "sell", "please", "this"}


class DemoRequest(BaseModel):
    catalog: str = Field(min_length=1, max_length=12000)
    question: str = Field(min_length=1, max_length=500)


def words(text: str) -> set[str]:
    return {w for w in re.findall(r"[a-z0-9]+", text.lower()) if len(w) > 2 and w not in STOP}


def find_answer(catalog: str, question: str) -> dict:
    query = words(question)
    lines = [line.strip() for line in catalog.splitlines() if line.strip()]
    ranked = sorted(((len(query & words(line)), line) for line in lines), reverse=True)
    if not query or not ranked or ranked[0][0] == 0:
        return {"answer": FALLBACK, "matched": False, "mode": "keyword_demo"}
    return {"answer": ranked[0][1], "matched": True, "mode": "keyword_demo"}


@app.get("/", response_class=HTMLResponse)
def home():
    return """<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>AskDuka demo</title><style>body{font:16px system-ui;background:#f1f5f4;color:#17332c}main{max-width:680px;margin:5vh auto;background:white;padding:30px;border-radius:16px}h1{color:#12664b}label{display:block;margin-top:20px;font-weight:bold}textarea,input{width:100%;box-sizing:border-box;padding:12px;border:1px solid #aaa;border-radius:6px;font:inherit}textarea{height:140px}button{margin-top:20px;padding:12px 20px;background:#12664b;color:white;border:0;border-radius:6px;cursor:pointer}pre{white-space:pre-wrap;background:#e8f5ed;padding:18px;border-radius:6px}</style>
<main><h1>AskDuka</h1><p>Test how AskDuka can find answers in a business catalog.</p>
<p><small>Development demo: keyword matching, not generative AI. Nothing is saved. Do not enter private data.</small></p>
<form id="form"><label for="catalog">Business catalog — one fact per line</label>
<textarea id="catalog" required>We have 20-inch bone straight wigs available for ₦120,000.
Delivery in Lagos takes 1 to 2 days.
Our store opens Monday to Saturday.</textarea>
<label for="question">Customer question</label><input id="question" required value="Do you have bone straight wigs?">
<button>Find answer</button></form><h2>Answer</h2><pre id="answer" aria-live="polite">Ask a question above.</pre></main>
<script>document.getElementById('form').onsubmit=async e=>{e.preventDefault();const out=document.getElementById('answer');out.textContent='Searching...';try{const r=await fetch('/demo/ask',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({catalog:document.getElementById('catalog').value,question:document.getElementById('question').value})});if(!r.ok)throw Error();const d=await r.json();out.textContent=d.answer}catch(e){out.textContent='Request failed.'}}</script></html>"""


@app.post("/demo/ask")
def demo_ask(request: DemoRequest):
    return find_answer(request.catalog, request.question)


@app.get("/health")
def health():
    return {"status": "ok", "service": "askduka-preview"}


@app.get("/readiness")
def readiness():
    return {"ready_for_customers": False, "demo_mode": "keyword_matching_only",
            "pending": ["database and migrations", "document upload", "AI generation",
                        "WhatsApp signature verification", "end-to-end testing"]}
