import anthropic
from src.recommender import Song, UserProfile, Recommender


def gaussian_score_normalized(user: UserProfile, song: Song) -> float:
    """
    Run the existing Gaussian + mood/genre scoring on a single song.
    Returns a value in 0.0–1.0 (raw score divided by max 8.0).
    """
    raise NotImplementedError("TODO: call Recommender.score() and normalize by 8.0")


def llm_relevance_batch(
    songs: list[Song],
    editorial_context: str,
    user_description: str,
    client: anthropic.Anthropic,
) -> list[float]:
    """
    Ask Claude to rate each song 0–1 for how well it fits the user and editorial context.
    Uses a single API call with all songs in the prompt. Returns a list parallel to songs.
    """
    raise NotImplementedError("TODO: build batch prompt, call Claude, parse JSON response")


def blend(
    g_scores: list[float],
    llm_scores: list[float],
    gaussian_weight: float,
) -> list[float]:
    """
    Combine Gaussian and LLM scores using a weighted average.
    gaussian_weight=1.0 means pure algorithm; 0.0 means pure LLM.
    Returns a list of blended scores parallel to the input lists.
    """
    raise NotImplementedError("TODO: gaussian_weight * g + (1 - gaussian_weight) * llm")
