"""Input validation and output confidence checks for the AI Playlist Builder."""

import re
from src.recommender import Song, UserProfile, MOOD_GRAPH

_TEMPO_MIN = 52.0
_TEMPO_MAX = 168.0

MUSIC_KEYWORDS = {
    "song", "songs", "music", "playlist", "track", "tracks", "listen",
    "play", "vibe", "vibes", "beat", "beats", "study", "workout", "party",
    "drive", "relax", "chill", "focus", "sleep", "run", "gym", "artist",
    "album", "genre", "mood", "energy", "upbeat", "mellow", "hype",
    "hits", "suggest", "recommend", "tune", "tunes", "banger", "bangers",
    "jam", "jams", "mix", "singer", "rapper", "band",
}


def validate_profile(profile: UserProfile) -> list[str]:
    """
    Check a UserProfile for known failure modes. Returns a list of warning strings.
    Auto-fixes sigma=0 by clamping to 0.01 in place.
    """
    warnings = []

    if profile.preferred_mood not in MOOD_GRAPH:
        warnings.append(
            f"Unknown mood '{profile.preferred_mood}' — not in the mood graph. "
            "Mood scoring will be disabled (every song scores 0 on this dimension)."
        )

    if profile.sigma == 0.0:
        profile.sigma = 0.01
        warnings.append(
            "sigma=0 would cause a division-by-zero crash. Auto-clamped to 0.01."
        )

    if not (_TEMPO_MIN <= profile.target_tempo_bpm <= _TEMPO_MAX):
        warnings.append(
            f"Target tempo {profile.target_tempo_bpm} BPM is outside the catalog range "
            f"({int(_TEMPO_MIN)}–{int(_TEMPO_MAX)} BPM). "
            "Tempo scoring will be near-zero for all songs."
        )

    return warnings


def validate_query(query: str) -> list[str]:
    """
    Basic sanity checks on the raw user query string.
    Returns a list of warning strings (empty list = all clear).
    """
    warnings = []

    if not query.strip():
        warnings.append("Query is empty. Please describe what you're about to do.")
        return warnings

    words = set(re.sub(r"[^\w\s]", "", query.lower()).split())
    if not words & MUSIC_KEYWORDS:
        warnings.append(
            "Your query doesn't mention music or an activity. "
            "Try something like 'songs for studying' or 'playlist for a workout'."
        )

    return warnings


def confidence_score(blended_scores: list[float]) -> float:
    """
    Return a confidence value 0.0–1.0 based on the gap between rank-1 and rank-2.
    Expects scores sorted descending. Returns 1.0 if only one score is provided.
    """
    if len(blended_scores) < 2:
        return 1.0

    gap = blended_scores[0] - blended_scores[1]
    # A gap of 0.3+ on a 0–1 scale is a strong signal; clamp to [0, 1].
    return min(gap / 0.3, 1.0)


def genre_dominance_flag(total_score: float, genre_bonus: float) -> bool:
    """
    Return True if the genre bonus accounts for more than 40% of the song's total score.
    Signals that a genre match is carrying a song that is weak on all other dimensions.
    total_score and genre_bonus are both on the raw 0–8.0 scale.
    """
    if total_score <= 0:
        return False
    return (genre_bonus / total_score) > 0.40
