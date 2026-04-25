"""
Evaluation harness for the AI Playlist Builder.

Runs 5 predefined profiles (3 standard + 2 adversarial) directly through
the Recommender and guardrails layers — bypassing the agent for speed.
Prints a pass/fail summary table.

Usage:
    python tests/eval_harness.py
"""

from src.recommender import UserProfile, load_songs, Recommender
from src.guardrails import validate_profile, confidence_score
from src.scorer import gaussian_score_normalized

TEST_PROFILES = [
    {
        "name": "High-Energy Pop",
        "profile": UserProfile(
            preferred_mood="happy",
            preferred_genre="pop",
            target_energy=0.8,
            target_tempo_bpm=120,
            target_acousticness=0.2,
            target_speechiness=0.06,
            sigma=0.20,
        ),
        "expect_energy_above": 0.7,
        "expect_genre": ["pop", "rock"],
    },
    {
        "name": "Chill Lofi",
        "profile": UserProfile(
            preferred_mood="chill",
            preferred_genre="lo-fi",
            target_energy=0.3,
            target_tempo_bpm=75,
            target_acousticness=0.7,
            target_speechiness=0.04,
            sigma=0.25,
        ),
        "expect_energy_below": 0.5,
        "expect_mood": ["chill", "peaceful", "focused"],
    },
    {
        "name": "Deep Intense Rock",
        "profile": UserProfile(
            preferred_mood="intense",
            preferred_genre="rock",
            target_energy=0.9,
            target_tempo_bpm=140,
            target_acousticness=0.1,
            target_speechiness=0.05,
            sigma=0.15,
        ),
        "expect_score_above": 4.0,
    },
    {
        "name": "Adversarial: unknown mood (sad)",
        "profile": UserProfile(
            preferred_mood="sad",
            preferred_genre="pop",
            target_energy=0.5,
            target_tempo_bpm=100,
            target_acousticness=0.4,
            target_speechiness=0.05,
            sigma=0.20,
        ),
        "expect_guardrail_warning": True,
        "expect_no_crash": True,
    },
    {
        "name": "Adversarial: sigma=0",
        "profile": UserProfile(
            preferred_mood="happy",
            preferred_genre="pop",
            target_energy=0.7,
            target_tempo_bpm=120,
            target_acousticness=0.2,
            target_speechiness=0.05,
            sigma=0.0,
        ),
        "expect_guardrail_warning": True,
        "expect_no_crash": True,
    },
]

_COL_WIDTH = 32


def _check(entry: dict, songs: list, warnings: list[str]) -> tuple[bool, list[str]]:
    """Run assertions for one profile entry. Returns (passed, failure_messages)."""
    failures = []
    top = songs[0] if songs else None

    if entry.get("expect_guardrail_warning") and not warnings:
        failures.append("Expected guardrail warning but got none")

    if "expect_energy_above" in entry and top:
        if top.energy < entry["expect_energy_above"]:
            failures.append(f"Top song energy {top.energy:.2f} < {entry['expect_energy_above']}")

    if "expect_energy_below" in entry and top:
        if top.energy > entry["expect_energy_below"]:
            failures.append(f"Top song energy {top.energy:.2f} > {entry['expect_energy_below']}")

    if "expect_genre" in entry and top:
        if top.genre not in entry["expect_genre"]:
            failures.append(f"Top genre '{top.genre}' not in {entry['expect_genre']}")

    if "expect_mood" in entry and top:
        if top.mood not in entry["expect_mood"]:
            failures.append(f"Top mood '{top.mood}' not in {entry['expect_mood']}")

    if "expect_score_above" in entry and top:
        raw, _ = Recommender.score(entry["profile"], top)
        if raw < entry["expect_score_above"]:
            failures.append(f"Top song raw score {raw:.2f} < {entry['expect_score_above']}")

    return (len(failures) == 0), failures


def run_harness() -> None:
    """Run all test profiles and print a formatted results table."""
    songs = load_songs("data/songs.csv")
    rec = Recommender(songs)

    print("\n" + "=" * 72)
    print("  AI Playlist Builder — Evaluation Harness")
    print("=" * 72)
    print(f"{'Profile':<{_COL_WIDTH}} {'Result':<8} Details")
    print("-" * 72)

    all_passed = True
    for entry in TEST_PROFILES:
        profile = entry["profile"]
        try:
            warnings = validate_profile(profile)
            results = rec.recommend(profile, k=5)
            passed, failures = _check(entry, results, warnings)
        except Exception as exc:
            passed = False
            failures = [f"CRASH: {exc}"]

        status = "PASS ✓" if passed else "FAIL ✗"
        detail = "  ".join(failures) if failures else ""
        print(f"{entry['name']:<{_COL_WIDTH}} {status:<8} {detail}")
        if not passed:
            all_passed = False

    print("=" * 72)
    print(f"  {'All profiles passed.' if all_passed else 'Some profiles FAILED — see above.'}\n")


if __name__ == "__main__":
    run_harness()
