from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import os
import requests

load_dotenv()

app = FastAPI(title="News Reporter API (Cloud)")

origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    https://news-reporter-one.vercel.app/
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class RunNewsRequest(BaseModel):
    topic: str


class RunNewsResponse(BaseModel):
    result: str


GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")  # example model name


def call_groq(prompt: str) -> str:
    if not GROQ_API_KEY:
        raise RuntimeError("GROQ_API_KEY not set")

    # Groq OpenAI-compatible endpoint
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }
    data = {
        "model": GROQ_MODEL,
        "messages": [
            {"role": "system", "content": "You are an expert AI/tech news journalist."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.5,
    }
    resp = requests.post(url, json=data, headers=headers, timeout=30)
    if resp.status_code != 200:
        raise RuntimeError(f"Groq error {resp.status_code}: {resp.text}")

    j = resp.json()
    return j["choices"][0]["message"]["content"]


@app.get("/")
async def root():
    return {
        "message": "News Reporter API is running",
        "endpoints": ["/health", "/run-news"],
    }


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/run-news", response_model=RunNewsResponse)
async def run_news(req: RunNewsRequest):
    topic = req.topic.strip()
    if not topic:
        raise HTTPException(status_code=400, detail="Topic must not be empty.")

    try:
        prompt = (
            "Write a clear, engaging markdown news article about the following topic.\n"
            "Use up-to-date, accurate information where possible.\n\n"
            f"Topic: {topic}\n\n"
            "Structure:\n"
            "- Short intro\n"
            "- 2–3 sections explaining key points, pros/cons, and impact\n"
            "- Brief conclusion\n"
        )
        text = call_groq(prompt)
        return RunNewsResponse(result=text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating article: {e}")
