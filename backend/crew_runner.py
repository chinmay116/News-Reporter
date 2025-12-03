from typing import Dict, Any
from crew import build_news_crew

def run_news_crew(topic: str) -> Dict[str, Any]:
    crew = build_news_crew()
    result_text = crew.kickoff(inputs={"topic": topic})
    return {
        "result": str(result_text),
        "output_file": "new-blog-post.md",
    }
