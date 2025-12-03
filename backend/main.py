from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langchain_ollama import ChatOllama
from dotenv import load_dotenv
import os
import requests
from news_store import add_articles, search_articles

load_dotenv()

app = FastAPI(title="News Reporter API (Direct Ollama)")


origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

NEWSAPI_KEY = os.getenv("NEWSAPI_KEY")

llm = ChatOllama(
    model="llama3.1",
    temperature=0.5,
)

class RunNewsRequest(BaseModel):
    topic: str


class RunNewsResponse(BaseModel):
    result: str


@app.post("/refresh-news")
async def refresh_news():
    if not NEWSAPI_KEY:
        raise HTTPException(status_code=500, detail="NEWSAPI_KEY not set in environment.")
    
    url = "https://newsapi.org/v2/top-headlines"
    params = {
        "apiKey": NEWSAPI_KEY,
        "category": "technology",
        "pageSize": 50,
        "language": "en",
        "q": "AI OR artificial intelligence OR machine learning",
    }

    try:
        resp = requests.get(url, params=params, timeout=15)
        if resp.status_code != 200:
            raise HTTPException(
                status_code=500,
                detail=f"NewsAPI error: {resp.status_code} {resp.text}",
            )
        
        data = resp.json()
        raw_articles = data.get("articles", [])

        articles = []
        for idx, a in enumerate(raw_articles):
            articles.append(
                {
                    "id": f"{a.get('url') or idx}",
                    "title": a.get("title"),
                    "description": a.get("description"),
                    "content": a.get("content"),
                    "url": a.get("url"),
                    "source": (a.get("source") or {}).get("name"),
                    "published_at": a.get("publishedAt"),
                }
            )

        
        added = add_articles(articles)
        return {"fetched": len(raw_articles), "indexed": added}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error refreshing news: {e}")


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/run-news", response_model=RunNewsResponse)
async def run_news(req: RunNewsRequest):
    topic = req.topic.strip()
    if not topic:
        raise HTTPException(status_code=400, detail="Topic must not be empty.")

    try:
        # 1) Retrieve relevant news chunks from Chroma
        retrieved = search_articles(topic, k=6)

        if not retrieved:
            base_prompt = (
                "You are an expert technology news writer.\n"
                f"Write a clear, engaging markdown blog post about: {topic}.\n"
                "There is no external news context available, so rely on your general knowledge."
            )
        else:
            # Build context string with sources
            context_blocks = []
            for r in retrieved:
                meta_line = ""
                if r.get("title"):
                    meta_line += f"Title: {r['title']}\n"
                if r.get("source"):
                    meta_line += f"Source: {r['source']}\n"
                if r.get("published_at"):
                    meta_line += f"Published at: {r['published_at']}\n"
                if r.get("url"):
                    meta_line += f"URL: {r['url']}\n"
                block = f"{meta_line}\nContent:\n{r['chunk']}"
                context_blocks.append(block)

            context_text = "\n\n---\n\n".join(context_blocks)

            base_prompt = (
                "You are an expert AI/tech news journalist.\n"
                "Use ONLY the news context below to write an accurate, up-to-date article.\n"
                "If something is not supported by the context, do not invent facts.\n\n"
                f"User topic: {topic}\n\n"
                "News context:\n"
                f"{context_text}\n\n"
                "Now write a markdown article with:\n"
                "- A short, catchy introduction\n"
                "- 2–3 clear sections explaining the situation\n"
                "- A brief conclusion\n"
                "Include references to specific sources (by title or source name) where useful."
            )

        resp = llm.invoke(base_prompt)
        text = resp.content if hasattr(resp, "content") else str(resp)
        return RunNewsResponse(result=text)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating article: {e}")
