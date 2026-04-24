"""
Evaluation harness for the AI Playlist Builder.

Runs 5 predefined profiles (3 standard + 2 adversarial) directly through
the Recommender and guardrails layers — bypassing the agent for speed.
Prints a pass/fail summary table.
"""

# TODO: import modules once implemented
# from src.recommender import UserProfile, load_songs, Recommender
# from src.guardrails import validate_profile, confidence_score
# from src.scorer import gaussian_score_normalized, blend

TEST_PROFILES = [
    {
        "name": "High-Energy Pop",
        "profile": None,  # TODO: UserProfile(preferred_mood="happy", preferred_genre="pop", ...)
        "expect_energy_above": 0.8,
        "expect_genre": ["pop", "rock"],
    },
    {
        "name": "Chill Lofi",
        "profile": None,  # TODO: UserProfile(preferred_mood="chill", preferred_genre="lofi", ...)
        "expect_energy_below": 0.5,
        "expect_mood": ["chill", "peaceful", "focused"],
    },
    {
        "name": "Deep Intense Rock",
        "profile": None,  # TODO: UserProfile(preferred_mood="intense", preferred_genre="rock", ...)
        "expect_score_above": 6.0,
    },
    {
        "name": "Adversarial: unknown mood (sad)",
        "profile": None,  # TODO: UserProfile(preferred_mood="sad", ...)
        "expect_guardrail_warning": True,
        "expect_no_crash": True,
    },
    {
        "name": "Adversarial: sigma=0",
        "profile": None,  # TODO: UserProfile(..., sigma=0.0)
        "expect_guardrail_warning": True,
        "expect_no_crash": True,
    },
]


def run_harness() -> None:
    """Run all test profiles and print a formatted results table."""
    raise NotImplementedError("TODO: implement harness loop and table output")


if __name__ == "__main__":
    run_harness()
