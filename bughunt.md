# Bug Hunt Log

Bugs discovered during live UI testing across iterations 2–4.

---

## Iteration 2

### Explanations are too scientific
**Status:** Solved
**Screenshot:** `iterui/solved-Explanation are too scientific.png`
**Symptom:** The `explain_results` step output raw Gaussian scoring labels — `genre match (+2.0) | energy proximity (+1.21)...` — instead of human-readable sentences.
**Root cause:** The `explain_results` tool handler called `Recommender.score()` and joined the internal label strings directly into the explanation.
**Fix:** Changed the `explain_results` tool schema to accept an `explanations` input field. Claude now generates social-proof style sentences from the Tavily editorial context already in its conversation (e.g. *"Students say this helps them focus"*). The handler simply reads `inputs["explanations"]` — no extra API call needed.
**Files:** `src/agent.py` — tool schema + handler

---

### Confidence badge not meaningful
**Status:** Solved
**Screenshot:** `iterui/solved-Confidence feature not needed.png`
**Symptom:** A 🟡 Medium badge appeared on every result, visually heavy and not useful to end users.
**Root cause:** Confidence was derived from the gap between rank-1 and rank-2 blended scores — a metric meaningful for debugging but not for listeners.
**Fix:** Removed the `conf_label` block and `st.metric("Confidence", ...)` from `app.py`. Also removed the orphaned `---` divider that followed it.
**Files:** `app.py`

---

### Algorithm slider resets on rerun / Load More unreliable
**Status:** Solved
**Screenshot:** `iterui/solved-Algorithm slider-load_more_not working.png`
**Symptom:** Moving the slider to 0.8 then clicking a preset button or Load More snapped it back to 0.5, causing false cache-hit detection and making Load More appear broken.
**Root cause:** The slider had no `key=` parameter, so Streamlit re-initialized it to `value=0.5` on every `st.rerun()`.
**Fix:** Added `key="gaussian_weight"` to the slider. Streamlit now persists the value in `st.session_state.gaussian_weight` automatically across reruns.
**Files:** `app.py`

---

## Iteration 3

### Duplicate songs in the recommended list
**Status:** Solved
**Screenshot:** `iterui/solved-duplicate songs in the recommended list.png`
**Symptom:** The same tracks appeared multiple times — once in the initial playlist and again after clicking Load More.
**Root cause:** `fetch_recommendations()` is called with the same seed artists/genres for both the initial agent run and Load More. Spotify's search is deterministic, so the same track IDs are returned each time. No deduplication existed before appending to `extra_songs`.
**Fix:** Added `seen_ids` (a `set`) to session state. After each agent run, `seen_ids` is populated with all `spotify_id`s from `result.songs`. Load More filters new results against `seen_ids` before appending, then adds new IDs to the set.
**Files:** `app.py`

---

### Algorithm dataset too limited (fewer than 10 songs)
**Status:** Solved
**Screenshot:** `iterui/solved-algorithm dataset too limited.png`
**Symptom:** Some queries — especially specific genre+artist combinations — produced only 4–6 songs instead of the expected 10.
**Root cause:** `fetch_recommendations` requested `limit=10` from Spotify's search API. For specific queries (e.g. `artist:"Lofi Girl" lofi chillhop`), Spotify returns fewer than 10 results. Additionally, Spotify's Client Credentials flow caps search at `limit=10` — requests above this return a 400 error. Also discovered: genre strings like "pop dance edm party" (3+ terms) and unquoted multi-word artist names (e.g. `artist:Lofi Girl`) triggered 400 Bad Request errors.
**Fix (3 parts):**
1. Capped genres at 2 terms in the search query to avoid Spotify rejecting overly long mixed queries.
2. Quoted multi-word artist names: `artist:"Lofi Girl"` instead of `artist:Lofi Girl`.
3. Added a top-up pass: if the primary query returns fewer tracks than `limit`, a second genre-only search fills the remaining slots (deduped by track ID).
**Files:** `src/spotify_client.py` — `fetch_recommendations`

---

### Repeat songs in list
**Status:** Solved
**Screenshot:** `iterui/solved-repeats in songs.png`
**Symptom:** The same song appeared more than once within a single playlist result.
**Root cause:** Related to the deduplication gap above — tracks from the initial fetch and Load More could overlap with no ID-level check.
**Fix:** Covered by the `seen_ids` fix above (same change).
**Files:** `app.py`

---

## Iteration 4

### Agent Reasoning expander shows stale data across queries
**Status:** Solved
**Screenshot:** `iterui/bug-The reasoning need to update for each query.png`
**Symptom:** After running a new query, the Agent Reasoning expander still showed reasoning steps from the previous run. There was also no indication of which query the visible reasoning belonged to.
**Root cause:** `st.session_state.result` was not cleared before calling `run_agent()`, so the old `AgentResult` (including its `reasoning_steps`) remained visible during the spinner. The expander also had a generic "Agent Reasoning" label with no query context.
**Fix:**
1. Set `st.session_state.result = None` immediately before the spinner, so no stale data is visible while the new run loads.
2. Store the active query in `st.session_state.result_query` after each run.
3. Updated expander label to `Agent Reasoning — "your query here"`.
**Files:** `app.py`

---

### All songs score identically / same artist repeats
**Status:** Solved
**Screenshot:** `iterui/bug-producing the same artist for late-night drive.png`
**Symptom:** All songs in a genre (e.g. synthwave) received the exact same blended score (e.g. 0.58), making ranking meaningless and causing the same artists to appear in the same order on every run.
**Root cause (2 parts):**
1. `fetch_recommendations` assigns every song in a genre the same static audio features from `_GENRE_DEFAULTS` — identical energy, tempo, acousticness, speechiness for all songs. The Gaussian scorer therefore produces the same value for every song. Spotify's `popularity` field is not returned under Client Credentials, so no per-track signal was available.
2. Several common genres (`synthwave`, `rap`, `trap`, `chill`, `workout`, `focus`) were missing from `_GENRE_DEFAULTS`, causing them to fall through to the generic fallback (energy=0.50, tempo=100).
**Fix:**
1. Added `synthwave`, `trap`, `chill`, `rap`, `workout`, `focus` to `_GENRE_DEFAULTS` with realistic values.
2. Used search-result **position** as a relevance proxy: position 0 (Spotify's top result) gets +0.5 deviation, the last result gets −0.5. This spreads energy (±0.25), tempo (±25 BPM), and acousticness (±0.15) across the fetched tracks, creating meaningful score differentiation.
3. Added post-ranking artist deduplication in the `score_songs` handler: keeps the highest-scored song per artist at the front and pushes duplicates to the back of the list (still visible in "More tracks"). Dedup is skipped when the user explicitly requested a specific artist.
**Files:** `src/spotify_client.py` — `_GENRE_DEFAULTS`, `fetch_recommendations`; `src/agent.py` — `score_songs` handler
