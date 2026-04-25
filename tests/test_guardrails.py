"""Unit tests for src/guardrails.py — no API calls."""

from src.recommender import UserProfile
from src.guardrails import (
    validate_profile,
    validate_query,
    confidence_score,
    genre_dominance_flag,
)


def _make_profile(**kwargs) -> UserProfile:
    defaults = dict(
        preferred_mood="happy", preferred_genre="pop",
        target_energy=0.7, target_tempo_bpm=120,
        target_acousticness=0.2, target_speechiness=0.05, sigma=0.2,
    )
    defaults.update(kwargs)
    return UserProfile(**defaults)


# ── validate_profile ─────────────────────────────────────────────────────────

def test_validate_profile_valid():
    """Clean profile produces no warnings."""
    warnings = validate_profile(_make_profile())
    assert warnings == []


def test_validate_profile_unknown_mood():
    """A mood not in MOOD_GRAPH produces a warning."""
    warnings = validate_profile(_make_profile(preferred_mood="sad"))
    assert len(warnings) == 1
    assert "mood" in warnings[0].lower()


def test_validate_profile_sigma_zero():
    """sigma=0 produces a warning and is auto-clamped to 0.01."""
    profile = _make_profile(sigma=0.0)
    warnings = validate_profile(profile)
    assert len(warnings) == 1
    assert profile.sigma == 0.01


def test_validate_profile_tempo_out_of_range():
    """Tempo outside 52–168 BPM produces a warning."""
    warnings = validate_profile(_make_profile(target_tempo_bpm=300))
    assert len(warnings) == 1
    assert "tempo" in warnings[0].lower()


def test_validate_profile_multiple_issues():
    """Unknown mood + sigma=0 together produce two warnings."""
    profile = _make_profile(preferred_mood="sad", sigma=0.0)
    warnings = validate_profile(profile)
    assert len(warnings) == 2


# ── validate_query ───────────────────────────────────────────────────────────

def test_validate_query_empty():
    """Empty string produces a warning."""
    warnings = validate_query("")
    assert len(warnings) == 1


def test_validate_query_whitespace_only():
    """Whitespace-only string produces a warning."""
    warnings = validate_query("   ")
    assert len(warnings) == 1


def test_validate_query_no_music_keywords():
    """Non-music query produces a warning."""
    warnings = validate_query("I am going to the grocery store")
    assert len(warnings) == 1


def test_validate_query_valid_plain():
    """Standard music query produces no warnings."""
    warnings = validate_query("create a study playlist")
    assert warnings == []


def test_validate_query_punctuation():
    """Regression: punctuation mid-sentence must not block keyword matching."""
    warnings = validate_query("I'm in a good mood. Suggest some Bad Bunny hits")
    assert warnings == [], f"Expected no warnings, got: {warnings}"


def test_validate_query_artist_only():
    """Artist-only query with 'play' keyword produces no warnings."""
    warnings = validate_query("play some Bad Bunny")
    assert warnings == []


def test_validate_query_preset_study():
    """Preset study query produces no warnings."""
    warnings = validate_query("create a playlist for me to study to")
    assert warnings == []


def test_validate_query_preset_party():
    """Preset party query produces no warnings."""
    warnings = validate_query("I'm at a party, play something energetic")
    assert warnings == []


# ── confidence_score ─────────────────────────────────────────────────────────

def test_confidence_score_high_gap():
    """Gap ≥ 0.3 between rank-1 and rank-2 returns 1.0."""
    score = confidence_score([0.9, 0.5, 0.3])
    assert score == 1.0


def test_confidence_score_low_gap():
    """Gap < 0.05 returns a low confidence value."""
    score = confidence_score([0.6, 0.58, 0.4])
    assert score < 0.2


def test_confidence_score_single_entry():
    """Single score always returns 1.0."""
    assert confidence_score([0.75]) == 1.0


def test_confidence_score_empty():
    """Empty list returns 1.0 (no evidence of low confidence)."""
    assert confidence_score([]) == 1.0


# ── genre_dominance_flag ─────────────────────────────────────────────────────

def test_genre_dominance_flag_dominant():
    """Genre bonus > 40% of total → True."""
    assert genre_dominance_flag(total_score=4.0, genre_bonus=3.0) is True


def test_genre_dominance_flag_not_dominant():
    """Genre bonus < 40% of total → False."""
    assert genre_dominance_flag(total_score=6.0, genre_bonus=1.0) is False


def test_genre_dominance_flag_exactly_40_percent():
    """Exactly 40% is not dominant (strictly greater than)."""
    assert genre_dominance_flag(total_score=5.0, genre_bonus=2.0) is False


def test_genre_dominance_flag_zero_total():
    """Zero total score → False with no division-by-zero crash."""
    assert genre_dominance_flag(total_score=0.0, genre_bonus=0.0) is False
