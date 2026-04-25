# Project Completion Plan

## Environment
- [x] Virtual environment (`.venv`) created
- [x] Install dependencies — `pip install -r requirements.txt`
- [x] Create `.env` file with API keys (`ANTHROPIC_API_KEY`, `SPOTIFY_CLIENT_ID`, `SPOTIFY_CLIENT_SECRET`, `TAVILY_API_KEY`)

## Core Scorer — `src/scorer.py`
- [x] `gaussian_score_normalized()` — call `Recommender.score()` and divide by 8.0
- [x] `llm_relevance_batch()` — build batch prompt, call Claude API, parse JSON scores
- [x] `blend()` — weighted average of Gaussian and LLM scores

## Agent Loop — `src/agent.py`
- [x] `run_agent()` — implement the full Claude tool-calling agentic loop (parse intent → tavily search → Spotify fetch → score → explain)

## Streamlit UI — `app.py`
- [x] Import and wire `run_agent` once agent is implemented
- [x] Fix preset query buttons (populate `st.session_state["query"]` on click)
- [x] Call `run_agent()` on submit and store result
- [x] Display guardrail warnings (`result.guardrail_warnings`)
- [x] Render agent reasoning trace (`result.reasoning_steps`)
- [x] Replace placeholder song cards with `result.songs[:3]` and `result.explanations`
- [x] Render songs 4–10 as compact list (`result.songs[3:]`)
- [x] Implement Load More pagination

## UI Iteration 2 — Polish
- [x] Human-readable explanations — `explain_results` tool now accepts `explanations` input; Claude writes social-proof sentences from Tavily context instead of raw score labels
- [x] Remove confidence badge — `st.metric("Confidence", ...)` removed from results section
- [x] Fix slider reset — added `key="gaussian_weight"` so slider value persists across `st.rerun()` calls

## UI Iteration 3 — Deduplication & Song Count
- [x] Fix duplicate songs — `seen_ids` set in session state; Load More filters against it before appending
- [x] Fix 400 errors from Spotify — cap genres at 2 terms, quote multi-word artist names, add per-query fallback search
- [x] Fix short song lists — top-up pass fills remaining slots with a simpler genre-only search when primary query returns fewer than `limit` results (Spotify Client Credentials hard-caps search at 10)

## UI Iteration 4 — Scoring & Reasoning
- [x] Clear stale reasoning — `st.session_state.result = None` before each new run; expander labeled `Agent Reasoning — "query"` so users know which run it belongs to
- [x] Fix identical scores — added `synthwave`, `trap`, `chill`, `rap`, `workout`, `focus` to `_GENRE_DEFAULTS`; applied position-based feature variation (±0.25 energy, ±25 BPM tempo) so Gaussian scores spread meaningfully across tracks
- [x] Artist deduplication — post-ranking pass pushes repeat artists to the back of the list; skipped when user explicitly requested a specific artist

## Tests
- [x] Run existing tests and confirm they pass — `pytest`
- [x] Add tests for `scorer.py` (`gaussian_score_normalized`, `blend`)
- [x] Add tests for `guardrails.py` (`validate_profile`, `confidence_score`, `genre_dominance_flag`)
- [x] Implement `tests/eval_harness.py` — run adversarial profiles and log results

## Docs (last)
- [ ] Rewrite `README.md` to reflect full project scope
- [ ] Update `model_card.md` to reflect full system

## Possible Features
- [ ] Some random facts about music while loading
- [ ] center the test to mimic how a chat interface looks
