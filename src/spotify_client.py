"""
Spotify Web API client using Client Credentials (no user login required).

Note: /recommendations and /audio-features require extended quota approval for
apps created after Nov 27 2024. This client uses /search instead, with
genre-based audio feature defaults for Gaussian scoring.
"""

import os
import base64
import requests
from dotenv import load_dotenv
from src.recommender import Song

load_dotenv()

_TOKEN_URL = "https://accounts.spotify.com/api/token"
_API_BASE = "https://api.spotify.com/v1"

# Genre-based audio feature defaults — used since /audio-features is gated.
# These inform the Gaussian scorer; the LLM scorer is the primary differentiator.
_GENRE_DEFAULTS: dict[str, dict] = {
    "lo-fi":      {"energy": 0.35, "tempo": 75,  "acousticness": 0.70, "speechiness": 0.04},
    "ambient":    {"energy": 0.25, "tempo": 65,  "acousticness": 0.80, "speechiness": 0.03},
    "classical":  {"energy": 0.20, "tempo": 80,  "acousticness": 0.90, "speechiness": 0.02},
    "jazz":       {"energy": 0.45, "tempo": 95,  "acousticness": 0.75, "speechiness": 0.05},
    "pop":        {"energy": 0.70, "tempo": 120, "acousticness": 0.20, "speechiness": 0.06},
    "rock":       {"energy": 0.85, "tempo": 130, "acousticness": 0.10, "speechiness": 0.05},
    "hip-hop":    {"energy": 0.75, "tempo": 95,  "acousticness": 0.15, "speechiness": 0.25},
    "electronic": {"energy": 0.80, "tempo": 128, "acousticness": 0.05, "speechiness": 0.05},
    "dance":      {"energy": 0.85, "tempo": 125, "acousticness": 0.05, "speechiness": 0.06},
    "reggaeton":  {"energy": 0.80, "tempo": 100, "acousticness": 0.10, "speechiness": 0.10},
    "latin":      {"energy": 0.75, "tempo": 105, "acousticness": 0.20, "speechiness": 0.08},
    "r-n-b":      {"energy": 0.60, "tempo": 95,  "acousticness": 0.25, "speechiness": 0.10},
    "soul":       {"energy": 0.55, "tempo": 90,  "acousticness": 0.40, "speechiness": 0.05},
    "metal":      {"energy": 0.95, "tempo": 155, "acousticness": 0.05, "speechiness": 0.05},
    "acoustic":   {"energy": 0.40, "tempo": 90,  "acousticness": 0.85, "speechiness": 0.04},
    "indie":      {"energy": 0.55, "tempo": 110, "acousticness": 0.35, "speechiness": 0.05},
}
_FALLBACK = {"energy": 0.50, "tempo": 100, "acousticness": 0.40, "speechiness": 0.05}


def get_token() -> str:
    """Exchange client credentials for a Bearer token."""
    client_id = os.getenv("SPOTIFY_CLIENT_ID")
    client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
    credentials = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    response = requests.post(
        _TOKEN_URL,
        headers={"Authorization": f"Basic {credentials}"},
        data={"grant_type": "client_credentials"},
        timeout=10,
    )
    response.raise_for_status()
    return response.json()["access_token"]


def search_artist_id(name: str, token: str) -> str | None:
    """Return the Spotify artist ID for the first search match, or None."""
    response = requests.get(
        f"{_API_BASE}/search",
        headers={"Authorization": f"Bearer {token}"},
        params={"q": name, "type": "artist", "limit": 1},
        timeout=10,
    )
    response.raise_for_status()
    items = response.json().get("artists", {}).get("items", [])
    return items[0]["id"] if items else None


def _feature_defaults(genre: str) -> dict:
    """Return audio feature defaults for a genre string, falling back to averages."""
    for key in _GENRE_DEFAULTS:
        if key in genre.lower():
            return _GENRE_DEFAULTS[key]
    return _FALLBACK


def _infer_mood(energy: float, acousticness: float) -> str:
    """Map energy + acousticness to the closest mood in the mood graph."""
    if energy >= 0.75:
        return "euphoric" if acousticness < 0.2 else "intense"
    if energy >= 0.50:
        return "happy" if acousticness < 0.4 else "uplifted"
    if energy >= 0.30:
        return "focused" if acousticness < 0.5 else "relaxed"
    return "chill" if acousticness >= 0.5 else "melancholic"


def fetch_recommendations(
    token: str,
    seed_artists: list[str] | None = None,
    seed_genres: list[str] | None = None,
    target_energy: float = 0.5,
    target_tempo: float = 100.0,
    target_acousticness: float = 0.5,
    limit: int = 10,
) -> list[Song]:
    """
    Search Spotify for tracks and return them as Song objects.

    seed_artists: artist names (e.g. ["Bad Bunny"]) — searched via artist: filter.
    seed_genres:  genre keywords added to the search query.
    target_* params are kept for API compatibility with the agent but are not
    sent to Spotify (audio-features endpoint is gated for new apps).
    """
    query_parts: list[str] = []
    if seed_artists:
        query_parts.append(f"artist:{seed_artists[0]}")
    if seed_genres:
        query_parts.extend(seed_genres)
    if not query_parts:
        query_parts.append("top hits")

    response = requests.get(
        f"{_API_BASE}/search",
        headers={"Authorization": f"Bearer {token}"},
        params={"q": " ".join(query_parts), "type": "track", "limit": limit},
        timeout=10,
    )
    response.raise_for_status()
    tracks = response.json().get("tracks", {}).get("items", [])

    if not tracks:
        return []

    primary_genre = seed_genres[0] if seed_genres else "unknown"
    defaults = _feature_defaults(primary_genre)
    energy = defaults["energy"]
    acousticness = defaults["acousticness"]

    songs: list[Song] = []
    for i, track in enumerate(tracks):
        images = track.get("album", {}).get("images", [])
        songs.append(Song(
            id=i + 1,
            title=track["name"],
            artist=track["artists"][0]["name"],
            genre=primary_genre,
            mood=_infer_mood(energy, acousticness),
            energy=energy,
            tempo_bpm=defaults["tempo"],
            valence=0.5,
            danceability=0.5,
            acousticness=acousticness,
            speechiness=defaults["speechiness"],
            instrumentalness=0.0,
            cover_art_url=images[0]["url"] if images else "",
            spotify_id=track["id"],
        ))

    return songs
