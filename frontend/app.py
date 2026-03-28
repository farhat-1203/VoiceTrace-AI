"""
VoiceTrace AI — Streamlit Frontend
"""
import os
import json
import time
import requests
import streamlit as st

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

# ═══════════════════════════════════════════════════════════════════════
#  Page Config
# ═══════════════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="VoiceTrace AI",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ═══════════════════════════════════════════════════════════════════════
#  Custom CSS
# ═══════════════════════════════════════════════════════════════════════

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    /* ── Global ─────────────────────────────────────────────────── */
    .stApp {
        font-family: 'Inter', sans-serif;
    }

    /* ── Header ─────────────────────────────────────────────────── */
    .hero-title {
        font-size: 2.8rem;
        font-weight: 700;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0;
        line-height: 1.2;
    }
    .hero-subtitle {
        font-size: 1.1rem;
        color: #94a3b8;
        margin-top: 4px;
        margin-bottom: 24px;
    }

    /* ── Cards ──────────────────────────────────────────────────── */
    .result-card {
        background: linear-gradient(145deg, #1e293b 0%, #0f172a 100%);
        border: 1px solid #334155;
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 16px;
        box-shadow: 0 4px 24px rgba(0,0,0,0.3);
    }
    .result-card h3 {
        margin-top: 0;
        font-size: 1.1rem;
        font-weight: 600;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .result-card .content {
        font-size: 0.95rem;
        line-height: 1.6;
        color: #cbd5e1;
    }

    /* ── Badges ─────────────────────────────────────────────────── */
    .badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    .badge-safe {
        background: rgba(34,197,94,0.15);
        color: #22c55e;
        border: 1px solid rgba(34,197,94,0.3);
    }
    .badge-unsafe {
        background: rgba(239,68,68,0.15);
        color: #ef4444;
        border: 1px solid rgba(239,68,68,0.3);
    }
    .badge-important {
        background: rgba(234,179,8,0.15);
        color: #eab308;
        border: 1px solid rgba(234,179,8,0.3);
    }
    .badge-routine {
        background: rgba(148,163,184,0.15);
        color: #94a3b8;
        border: 1px solid rgba(148,163,184,0.3);
    }

    /* ── Metric Card ───────────────────────────────────────────── */
    .metric-row {
        display: flex;
        gap: 12px;
        flex-wrap: wrap;
        margin-bottom: 16px;
    }
    .metric-card {
        flex: 1;
        min-width: 140px;
        background: linear-gradient(145deg, #1e293b 0%, #0f172a 100%);
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 16px;
        text-align: center;
    }
    .metric-card .label {
        font-size: 0.75rem;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .metric-card .value {
        font-size: 1.5rem;
        font-weight: 700;
        margin-top: 4px;
    }
    .value-green { color: #22c55e; }
    .value-red { color: #ef4444; }
    .value-blue { color: #60a5fa; }
    .value-purple { color: #a78bfa; }

    /* ── Memory Item ───────────────────────────────────────────── */
    .memory-item {
        background: rgba(99,102,241,0.08);
        border-left: 3px solid #6366f1;
        border-radius: 0 8px 8px 0;
        padding: 12px 16px;
        margin-bottom: 8px;
        font-size: 0.9rem;
        color: #cbd5e1;
    }
    .memory-score {
        font-size: 0.75rem;
        color: #818cf8;
        font-weight: 600;
    }

    /* ── Sidebar ───────────────────────────────────────────────── */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f172a 0%, #1e1b4b 100%);
    }

    /* ── Animations ────────────────────────────────────────────── */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(12px); }
        to { opacity: 1; transform: translateY(0); }
    }
    .result-card {
        animation: fadeIn 0.5s ease-out;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ═══════════════════════════════════════════════════════════════════════
#  Sidebar
# ═══════════════════════════════════════════════════════════════════════

with st.sidebar:
    st.markdown("### ⚙️ System Status")

    # Health check
    try:
        r = requests.get(f"{BACKEND_URL}/health", timeout=5)
        health = r.json()
        status = health.get("status", "unknown")
        services = health.get("services", {})

        if status == "healthy":
            st.success("🟢 System Online")
        else:
            st.warning(f"🟡 System: {status}")

        for svc, svc_status in services.items():
            icon = "✅" if svc_status in ("running", "connected") else "❌"
            st.caption(f"{icon} **{svc.title()}**: {svc_status}")

    except requests.exceptions.ConnectionError:
        st.error("🔴 Backend Offline")
        st.caption("Make sure the backend service is running.")

    st.markdown("---")
    st.markdown("### 📋 About")
    st.caption(
        "**VoiceTrace AI** processes voice recordings from business owners, "
        "extracts structured data, and builds long-term memory for insights."
    )
    st.caption("Built with WhisperX · Groq · LangGraph · Qdrant")

    st.markdown("---")
    st.markdown("### 🕐 Recent Sessions")
    try:
        r = requests.get(f"{BACKEND_URL}/memories/recent?limit=5", timeout=5)
        recent = r.json()
        if recent:
            for mem in recent:
                ts = mem.get("created_at", "N/A")
                imp = "⭐" if mem.get("is_important") else "📝"
                preview = (mem.get("transcript", "") or "")[:60]
                st.caption(f"{imp} `{ts[:16]}` — {preview}...")
        else:
            st.caption("No sessions yet.")
    except Exception:
        st.caption("Unable to load recent sessions.")


# ═══════════════════════════════════════════════════════════════════════
#  Main Content
# ═══════════════════════════════════════════════════════════════════════

st.markdown('<h1 class="hero-title">🎙️ VoiceTrace AI</h1>', unsafe_allow_html=True)
st.markdown(
    '<p class="hero-subtitle">'
    "Voice-powered business intelligence — speak your day, get insights instantly."
    "</p>",
    unsafe_allow_html=True,
)

# ── Upload ────────────────────────────────────────────────────────────

col_upload, col_info = st.columns([2, 1])

with col_upload:
    uploaded_file = st.file_uploader(
        "Upload your audio recording",
        type=["wav", "mp3", "m4a", "ogg", "flac", "webm"],
        help="Max 3 minutes. Supported: WAV, MP3, M4A, OGG, FLAC, WebM",
    )

with col_info:
    if uploaded_file:
        st.markdown(
            f"""
            <div class="result-card">
                <h3>📁 File Info</h3>
                <div class="content">
                    <b>Name:</b> {uploaded_file.name}<br>
                    <b>Size:</b> {uploaded_file.size / 1024:.1f} KB<br>
                    <b>Type:</b> {uploaded_file.type}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

# ── Audio Preview ─────────────────────────────────────────────────────
if uploaded_file:
    st.audio(uploaded_file, format=uploaded_file.type)

# ── Process Button ────────────────────────────────────────────────────
if uploaded_file:
    if st.button("🚀  Process Audio", type="primary", use_container_width=True):

        with st.spinner("Processing your audio through the AI pipeline..."):
            progress = st.progress(0, text="Uploading audio...")
            time.sleep(0.3)
            progress.progress(10, text="Transcribing with WhisperX...")

            try:
                # Send to backend
                files = {
                    "file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)
                }
                response = requests.post(
                    f"{BACKEND_URL}/process",
                    files=files,
                    timeout=120,
                )

                progress.progress(90, text="Rendering results...")

                if response.status_code != 200:
                    st.error(f"Backend error: {response.status_code} — {response.text}")
                    st.stop()

                data = response.json()
                progress.progress(100, text="Done!")
                time.sleep(0.3)
                progress.empty()

            except requests.exceptions.ConnectionError:
                st.error("❌ Cannot reach the backend. Is it running?")
                st.stop()
            except requests.exceptions.Timeout:
                st.error("⏱️ Request timed out. The audio may be too long or the server is busy.")
                st.stop()
            except Exception as e:
                st.error(f"Error: {e}")
                st.stop()

        # ── Error Check ───────────────────────────────────────────────
        if data.get("error"):
            st.error(f"⚠️ Pipeline Error: {data['error']}")

        # ── Safety Flag ───────────────────────────────────────────────
        safety = data.get("safety_flag", "safe")
        if safety == "unsafe":
            st.markdown(
                '<span class="badge badge-unsafe">🛡️ UNSAFE — Content Blocked</span>',
                unsafe_allow_html=True,
            )
            st.stop()

        # ── Results ───────────────────────────────────────────────────
        st.markdown("---")
        st.markdown("## 📊 Results")

        # Processing time
        proc_time = data.get("processing_time_seconds", 0)
        st.caption(f"⚡ Processed in **{proc_time:.2f} seconds** | Session: `{data.get('session_id', 'N/A')}`")

        # ── Badges Row ────────────────────────────────────────────────
        badge_cols = st.columns(3)
        with badge_cols[0]:
            st.markdown(
                '<span class="badge badge-safe">🛡️ SAFE</span>',
                unsafe_allow_html=True,
            )
        with badge_cols[1]:
            is_imp = data.get("is_important", False)
            if is_imp:
                st.markdown(
                    '<span class="badge badge-important">⭐ IMPORTANT — Stored in Long-Term Memory</span>',
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    '<span class="badge badge-routine">📝 Routine — Short-Term Only</span>',
                    unsafe_allow_html=True,
                )
        with badge_cols[2]:
            extracted = data.get("extracted_data", {})
            sentiment = extracted.get("sentiment", "neutral")
            sent_emoji = {"positive": "😊", "negative": "😟", "mixed": "😐", "neutral": "😐"}.get(
                sentiment, "😐"
            )
            st.markdown(f"**Sentiment:** {sent_emoji} {sentiment.title()}")

        # ── Two-Column Layout ─────────────────────────────────────────
        left, right = st.columns(2)

        with left:
            # Transcript
            st.markdown(
                f"""
                <div class="result-card">
                    <h3>🎤 Transcript</h3>
                    <div class="content">{data.get("transcript", "No transcript generated.")}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # Extracted Data
            st.markdown(
                '<div class="result-card"><h3>📋 Extracted Business Data</h3><div class="content">',
                unsafe_allow_html=True,
            )
            if extracted:
                # Metrics row
                total_earn = extracted.get("total_earnings")
                total_exp = extracted.get("total_expenses")
                net = extracted.get("net_profit")

                if any(v is not None for v in [total_earn, total_exp, net]):
                    st.markdown(
                        f"""
                        <div class="metric-row">
                            <div class="metric-card">
                                <div class="label">Earnings</div>
                                <div class="value value-green">
                                    {'₹' + str(total_earn) if total_earn is not None else '—'}
                                </div>
                            </div>
                            <div class="metric-card">
                                <div class="label">Expenses</div>
                                <div class="value value-red">
                                    {'₹' + str(total_exp) if total_exp is not None else '—'}
                                </div>
                            </div>
                            <div class="metric-card">
                                <div class="label">Net Profit</div>
                                <div class="value value-blue">
                                    {'₹' + str(net) if net is not None else '—'}
                                </div>
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                # Full JSON
                st.json(extracted)
            else:
                st.caption("No data extracted.")
            st.markdown("</div></div>", unsafe_allow_html=True)

        with right:
            # Memory Decision
            if is_imp and data.get("formatted_memory"):
                st.markdown(
                    f"""
                    <div class="result-card">
                        <h3>🧠 Memory Stored</h3>
                        <div class="content">
                            <span class="badge badge-important">⭐ Long-Term Memory</span>
                            <p style="margin-top:12px;">{data["formatted_memory"]}</p>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    """
                    <div class="result-card">
                        <h3>🧠 Memory Decision</h3>
                        <div class="content">
                            <span class="badge badge-routine">📝 Routine</span>
                            <p style="margin-top:12px;">
                                This entry was stored in short-term memory only.
                            </p>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            # Retrieved Memories
            memories = data.get("retrieved_memories", [])
            st.markdown(
                '<div class="result-card"><h3>🔍 Retrieved Past Memories</h3><div class="content">',
                unsafe_allow_html=True,
            )
            if memories:
                for mem in memories:
                    score = mem.get("score", 0)
                    text = mem.get("formatted_memory", "N/A")
                    ts = mem.get("timestamp", "")[:16]
                    st.markdown(
                        f"""
                        <div class="memory-item">
                            <span class="memory-score">Score: {score:.3f} · {ts}</span>
                            <p style="margin:4px 0 0;">{text}</p>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
            else:
                st.caption("No relevant past memories found. Build up memory by using the system!")
            st.markdown("</div></div>", unsafe_allow_html=True)

        # ── Final Response (full width) ───────────────────────────────
        st.markdown(
            f"""
            <div class="result-card" style="border-color: #6366f1; margin-top: 8px;">
                <h3>💡 AI Analysis & Recommendations</h3>
                <div class="content">{data.get("final_response", "No response generated.").replace(chr(10), "<br>")}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

else:
    # ── Empty State ───────────────────────────────────────────────────
    st.markdown(
        """
        <div style="text-align: center; padding: 60px 20px; color: #64748b;">
            <div style="font-size: 4rem; margin-bottom: 16px;">🎙️</div>
            <h3 style="color: #94a3b8;">Upload an audio recording to get started</h3>
            <p>Record your business day — sales, expenses, insights — and let AI do the rest.</p>
            <p style="font-size: 0.85rem; color: #475569;">
                Supported: WAV, MP3, M4A, OGG, FLAC, WebM · Max 3 minutes
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ═══════════════════════════════════════════════════════════════════════
#  Footer
# ═══════════════════════════════════════════════════════════════════════

st.markdown("---")
st.markdown(
    """
    <div style="text-align: center; color: #475569; font-size: 0.8rem; padding: 12px 0;">
        <b>VoiceTrace AI</b> · WhisperX · Groq · LangGraph · Qdrant ·
        SentenceTransformers<br>
        Built for hackathon excellence 🏆
    </div>
    """,
    unsafe_allow_html=True,
)
