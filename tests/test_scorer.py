"""Unit tests for src/scorer.py — no API calls."""

from src.recommender import Song, UserProfile
from src.scorer import gaussian_score_normalized, blend


def _make_song(**kwargs) -> Song:
    defaults = dict(
        id=1, title="Test", artist="Artist", genre="pop", mood="happy",
        energy=0.7, tempo_bpm=120, valence=0.8, danceability=0.7,
        acousticness=0.2, speechiness=0.05, instrumentalness=0.0,
    )
    defaults.update(kwargs)
    return Song(**defaults)


def _make_profile(**kwargs) -> UserProfile:
    defaults = dict(
        preferred_mood="happy", preferred_genre="pop",
        target_energy=0.7, target_tempo_bpm=120,
        target_acousticness=0.2, target_speechiness=0.05, sigma=0.2,
    )
    defaults.update(kwargs)
    return UserProfile(**defaults)


# ── gaussian_score_normalized ────────────────────────────────────────────────

def test_gaussian_score_perfect_match():
    """Song that matches profile on every dimension scores near 1.0."""
    profile = _make_profile()
    song = _make_song(genre="pop", mood="happy", energy=0.7, tempo_bpm=120,
                      acousticness=0.2, speechiness=0.05)
    score = gaussian_score_normalized(profile, song)
    assert score >= 0.85, f"Expected near 1.0, got {score:.3f}"


def test_gaussian_score_no_match():
    """Song with completely different features scores near 0.0."""
    profile = _make_profile(preferred_mood="happy", preferred_genre="pop",
                             target_energy=0.9, target_tempo_bpm=160,
                             target_acousticness=0.05, sigma=0.05)
    song = _make_song(genre="classical", mood="peaceful", energy=0.1,
                      tempo_bpm=60, acousticness=0.95)
    score = gaussian_score_normalized(profile, song)
    assert score < 0.3, f"Expected near 0.0, got {score:.3f}"


def test_gaussian_score_output_range():
    """Score is always in [0.0, 1.0] regardless of input."""
    profile = _make_profile()
    songs = [
        _make_song(energy=0.0, tempo_bpm=52, acousticness=0.0),
        _make_song(energy=1.0, tempo_bpm=168, acousticness=1.0),
        _make_song(energy=0.5, tempo_bpm=100, acousticness=0.5),
    ]
    for song in songs:
        score = gaussian_score_normalized(profile, song)
        assert 0.0 <= score <= 1.0, f"Score {score:.3f} out of [0, 1]"


# ── blend ────────────────────────────────────────────────────────────────────

def test_blend_pure_gaussian():
    """gaussian_weight=1.0 returns g_scores unchanged."""
    g = [0.8, 0.6, 0.4]
    llm = [0.3, 0.5, 0.9]
    result = blend(g, llm, gaussian_weight=1.0)
    assert result == g


def test_blend_pure_llm():
    """gaussian_weight=0.0 returns llm_scores unchanged."""
    g = [0.8, 0.6, 0.4]
    llm = [0.3, 0.5, 0.9]
    result = blend(g, llm, gaussian_weight=0.0)
    assert result == llm


def test_blend_equal_weight():
    """gaussian_weight=0.5 returns element-wise average."""
    g = [0.8, 0.4]
    llm = [0.2, 0.6]
    result = blend(g, llm, gaussian_weight=0.5)
    assert abs(result[0] - 0.5) < 1e-9
    assert abs(result[1] - 0.5) < 1e-9


def test_blend_length_preserved():
    """Output length always matches input length."""
    g = [0.9, 0.7, 0.5, 0.3, 0.1]
    llm = [0.1, 0.3, 0.5, 0.7, 0.9]
    result = blend(g, llm, gaussian_weight=0.6)
    assert len(result) == len(g)
