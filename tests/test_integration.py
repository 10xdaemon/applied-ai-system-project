"""
Integration tests for the full AI Playlist Builder pipeline.

Requires a valid .env file with:
    ANTHROPIC_API_KEY, SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET, TAVILY_API_KEY

Run with:
    pytest tests/test_integration.py -v -m integration

These tests make real API calls (~10–20s each).
"""

import pytest
from src.agent import run_agent, AgentResult
from src.spotify_client import get_token, fetch_recommendations
from src.scorer import gaussian_score_normalized, blend
from src.recommender import UserProfile

pytestmark = pytest.mark.integration


# ── Helpers ──────────────────────────────────────────────────────────────────

def _assert_valid_result(result: AgentResult, min_songs: int = 3) -> None:
    """Common assertions every successful run should pass."""
    assert result is not None
    assert len(result.songs) >= min_songs, f"Expected ≥{min_songs} songs, got {len(result.songs)}"
    assert len(result.scores) == len(result.songs)
    assert len(result.explanations) == 3
    for score in result.scores:
        assert 0.0 <= score <= 1.0, f"Score {score:.3f} out of [0, 1]"
    for explanation in result.explanations:
        assert isinstance(explanation, str) and explanation.strip()


# ── Happy Path ────────────────────────────────────────────────────────────────

def test_study_session():
    """Standard study query returns a full valid result with no warnings."""
    result = run_agent("create a playlist for me to study to")
    _assert_valid_result(result)
    assert result.guardrail_warnings == []


def test_party_vibes():
    """Party query returns energetic songs with valid scores."""
    result = run_agent("I'm at a party, play something energetic")
    _assert_valid_result(result)
    assert result.guardrail_warnings == []


def test_late_night_drive():
    """Late-night drive query returns ≥3 songs, all scores in [0, 1]."""
    result = run_agent("make me a playlist for a late-night drive")
    _assert_valid_result(result)
    assert result.guardrail_warnings == []


def test_artist_query():
    """Artist-specific query with punctuation returns results without guardrail warnings."""
    result = run_agent("I'm in a good mood. Suggest some Bad Bunny hits")
    _assert_valid_result(result)
    assert result.guardrail_warnings == [], (
        f"Unexpected guardrail warnings: {result.guardrail_warnings}"
    )


def test_genre_query():
    """Genre-specific query returns songs and scores that are not all identical."""
    result = run_agent("play some lo-fi hip hop")
    _assert_valid_result(result)
    if len(result.scores) >= 2:
        spread = max(result.scores) - min(result.scores)
        assert spread > 0.01, f"All scores identical: {result.scores}"


# ── Edge Cases ────────────────────────────────────────────────────────────────

def test_guardrail_warning_non_music_query():
    """Non-music query still runs without crashing and produces a guardrail warning."""
    result = run_agent("what's the weather like today")
    assert result is not None
    assert len(result.guardrail_warnings) >= 1


def test_scores_not_all_identical():
    """Any genre query must produce spread scores, not a flat line."""
    result = run_agent("chill music for a rainy afternoon")
    _assert_valid_result(result)
    if len(result.scores) >= 2:
        spread = max(result.scores) - min(result.scores)
        assert spread > 0.01, f"Scores are all identical: {result.scores}"


def test_artist_cap_in_top3():
    """No single artist should appear more than twice in the top 3 cards."""
    result = run_agent("I'm about to clean, make me a playlist")
    _assert_valid_result(result)
    from collections import Counter
    top3_artists = [s.artist for s in result.songs[:3]]
    counts = Counter(top3_artists)
    for artist, count in counts.items():
        assert count <= 2, f"Artist '{artist}' appears {count} times in top 3"


def test_gaussian_weight_zero():
    """Pure LLM mode (gaussian_weight=0.0) runs without error."""
    result = run_agent("create a playlist for me to study to", gaussian_weight=0.0)
    _assert_valid_result(result)


def test_gaussian_weight_one():
    """Pure algorithmic mode (gaussian_weight=1.0) runs without error."""
    result = run_agent("create a playlist for me to study to", gaussian_weight=1.0)
    _assert_valid_result(result)


def test_gaussian_weight_affects_scores():
    """Scores at gaussian_weight=0.0 differ meaningfully from gaussian_weight=1.0."""
    result_llm = run_agent("study session playlist", gaussian_weight=0.0)
    result_gauss = run_agent("study session playlist", gaussian_weight=1.0)
    _assert_valid_result(result_llm)
    _assert_valid_result(result_gauss)
    # At least one score should differ between the two runs
    diffs = [abs(a - b) for a, b in zip(result_llm.scores, result_gauss.scores)]
    assert max(diffs) > 0.01, "Scores identical across gaussian_weight=0 and 1"


def test_reasoning_steps_populated():
    """Agent reasoning trace must include all 5 expected tool calls."""
    result = run_agent("create a playlist for me to study to")
    tools_called = [step["tool"] for step in result.reasoning_steps]
    for expected in ["parse_user_intent", "tavily_search", "spotify_fetch",
                     "score_songs", "explain_results"]:
        assert expected in tools_called, f"Missing tool call: {expected}"


def test_spotify_fetch_standalone():
    """Spotify fetch works independently and returns 10 songs."""
    token = get_token()
    songs = fetch_recommendations(token=token, seed_genres=["pop"], limit=10)
    assert len(songs) == 10
    for song in songs:
        assert song.title
        assert song.artist
        assert song.spotify_id


def test_no_duplicate_spotify_ids_in_result():
    """Initial result songs have no duplicate spotify_ids."""
    result = run_agent("party music")
    ids = [s.spotify_id for s in result.songs if s.spotify_id]
    assert len(ids) == len(set(ids)), f"Duplicate spotify_ids: {ids}"
