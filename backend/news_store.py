import os
from typing import List, Dict, Any

import chromadb
from chromadb.utils import embedding_functions

# Dir where chromadb will store the data
CHROMA_DIR = os.path.join(os.path.dirname(__file__), "chroma_db")

_client = chromadb.PersistentClient(path=CHROMA_DIR)

embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)

# single collection for AL/Tech News
_collection = _client.get_or_create_collection(
    name="ai-tech-news",
    embedding_function=embedding_fn,
)

def add_articles(articles: List[Dict[str, Any]]) -> int:
    """
    Add a list of articles to Chroma.
    Each article: {id, title, description, content, url, source, published_at}
    """
    if not articles:
        return 0
    
    ids = []
    documents = []
    metadatas = []

    for a in articles:
        aid = str(a["id"])
        text_parts = [
            a.get("title") or "",
            a.get("description") or "",
            a.get("content") or "",
        ]
        doc = "\n\n".join(p for p in text_parts if p)
        if not doc.strip():
            continue

        ids.append(aid)
        documents.append(doc)
        metadatas.append(
            {
                "title": a.get("title"),
                "url": a.get("url"),
                "source": a.get("source"),
                "published_at": a.get("published_at"),
            }
        )
    
    if not ids:
        return 0
    
    _collection.upsert(ids=ids, documents=documents, metadatas=metadatas)
    return len(ids)

def search_articles(query: str, k: int = 5) -> List[Dict[str, Any]]:
    """
    Retrieve top-k relevant articles for a query from Chroma.
    """
    if not query.strip():
        return []
    
    res = _collection.query(
        query_texts=[query],
        n_results=k,
    )

    if not res["documents"]:
        return []
    
    results = []
    docs = res["documents"][0]
    metas = res["metadatas"][0]

    for doc, meta in zip(docs, metas):
        item = {
            "chunk": doc,
            "title": meta.get("title"),
            "url": meta.get("url"),
            "source": meta.get("source"),
            "published_at": meta.get("published_at"),
        }
        results.append(item)

    return results
