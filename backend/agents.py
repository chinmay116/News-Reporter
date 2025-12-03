from crewai import Agent
from tools import tool
from langchain_ollama import ChatOllama
from dotenv import load_dotenv

load_dotenv()

import os
from dotenv import load_dotenv

load_dotenv()

# Force CrewAI to use Ollama and not OpenAI
os.environ.pop("OPENAI_API_KEY", None)
os.environ["CREWAI_LLM_PROVIDER"] = "ollama"
os.environ["CREWAI_EMBEDDINGS_PROVIDER"] = "ollama"

llm = ChatOllama(
    model="llama3.1",
    temperature=0.5,
)

news_researcher = Agent(
    role="Senior Researcher",
    goal="Uncover ground breaking technologies in {topic}",
    verbose=True,
    memory=True,
    backstory=(
        "Driven by curiosity, you're at the forefront of innovation,"
        " eager to explore and share knowledge that could change the world."
    ),
    tools=[tool],
    llm=llm,
    allow_delegation=True,
)

news_writer = Agent(
    role="Writer",
    goal="Narrate compelling tech stories about {topic}",
    verbose=True,
    memory=True,
    backstory=(
        "With a flair for simplifying complex topics, you craft engaging"
        " narratives that captivate and educate, bringing new discoveries"
        " to light in an accessible manner."
    ),
    tools=[tool],
    llm=llm,
    allow_delegation=False,
)
