import streamlit as st

# TODO: import run_agent once agent.py is implemented
# from src.agent import run_agent, AgentResult

st.set_page_config(page_title="AI Playlist Builder", page_icon="🎵", layout="wide")

# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Settings")

    gaussian_weight = st.slider(
        "Algorithm  ←→  AI",
        min_value=0.0,
        max_value=1.0,
        value=0.5,
        step=0.05,
        help="0 = full LLM scoring · 1 = full Gaussian scoring",
    )

    st.markdown("---")
    st.subheader("Preset Queries")

    # TODO: wire each button to populate the query input
    if st.button("Study session"):
        st.session_state["query"] = "create a playlist for me to study to"
    if st.button("Party vibes"):
        st.session_state["query"] = "I'm at a party, play something energetic"
    if st.button("Late-night drive"):
        st.session_state["query"] = "make me a playlist for a late-night drive"

    st.markdown("---")
    st.caption("API keys loaded from .env")

# ── Main ──────────────────────────────────────────────────────────────────────
st.title("🎵 AI Playlist Builder")
st.caption("Type what you're about to do and get a personalized playlist.")

query = st.text_area(
    "What are you up to?",
    value=st.session_state.get("query", ""),
    placeholder="e.g. 'create a playlist for studying' or 'my friend loves Bad Bunny, we're at a party'",
    height=80,
)

submitted = st.button("Build Playlist", type="primary")

if submitted and query.strip():
    with st.spinner("Agent is thinking..."):
        pass  # TODO: result = run_agent(query, gaussian_weight)

    # ── Guardrail warnings ───────────────────────────────────────────────────
    # TODO: if result.guardrail_warnings: st.warning(...)

    # ── Agent reasoning trace ────────────────────────────────────────────────
    with st.expander("Agent Reasoning", expanded=False):
        st.info("Reasoning steps will appear here once the agent is implemented.")
        # TODO: render result.reasoning_steps

    # ── Confidence badge ─────────────────────────────────────────────────────
    # TODO: show High / Medium / Low based on result.confidence

    st.markdown("---")

    # ── Top 3 songs: cover art + explanation ─────────────────────────────────
    st.subheader("Your Playlist")
    cols = st.columns(3)
    for i, col in enumerate(cols):
        with col:
            st.image("https://placehold.co/200x200?text=Song", width=200)
            st.markdown("**Song Title**")
            st.caption("Artist · Genre")
            st.markdown("`score placeholder`")
            st.markdown("_explanation placeholder_")
    # TODO: replace placeholders with result.songs[:3] and result.explanations

    # ── Songs 4–10: compact list ─────────────────────────────────────────────
    st.markdown("#### More tracks")
    st.markdown("Songs 4–10 will appear here.")
    # TODO: render result.songs[3:] as compact rows

    # ── Load More ────────────────────────────────────────────────────────────
    if st.button("Load More"):
        st.info("Load More will fetch the next 10 Spotify recommendations.")
        # TODO: implement pagination

elif submitted and not query.strip():
    st.warning("Please enter a query before building a playlist.")
