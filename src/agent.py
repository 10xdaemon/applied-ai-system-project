import os
import anthropic
from dataclasses import dataclass, field
from dotenv import load_dotenv
from src.recommender import Song, UserProfile

load_dotenv()


@dataclass
class AgentResult:
    songs: list[Song] = field(default_factory=list)
    scores: list[float] = field(default_factory=list)
    explanations: list[str] = field(default_factory=list)   # top 3 only
    reasoning_steps: list[dict] = field(default_factory=list)  # [{tool, input, output}]
    guardrail_warnings: list[str] = field(default_factory=list)
    confidence: float = 0.0


def run_agent(query: str, gaussian_weight: float = 0.5) -> AgentResult:
    """
    Run the Claude agentic loop for a user playlist query.

    Steps the agent executes via tool calls:
    1. parse_user_intent  → UserProfile + seed info
    2. tavily_search      → editorial context string
    3. spotify_fetch      → list of Song candidates
    4. score_songs        → hybrid blended scores
    5. explain_results    → one-line explanations for top 3 songs

    gaussian_weight: 0.0 = full LLM scoring, 1.0 = full Gaussian scoring.
    Returns an AgentResult with all intermediate steps captured.
    """
    raise NotImplementedError("TODO: implement Claude tool-calling agentic loop")
