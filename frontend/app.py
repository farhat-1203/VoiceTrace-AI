"""
VoiceTrace AI - Streamlit Frontend
Auth: Supabase Auth (Google OAuth)
All API calls include the user's Supabase access token.
"""
import os
import json
import time
import hashlib
import base64
import secrets
import requests
import streamlit as st
from supabase import create_client, Client
from audio_recorder_streamlit import audio_recorder
from loguru import logger

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "")

# Page Config
st.set_page_config(
    page_title="VoiceTrace AI",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    .stApp { font-family: 'Inter', sans-serif; }

    .hero-title {
        font-size: 2.8rem; font-weight: 700;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        margin-bottom: 0; line-height: 1.2;
    }
    .hero-subtitle { font-size: 1.1rem; color: #94a3b8; margin-top: 4px; margin-bottom: 24px; }

    .auth-card {
        background: linear-gradient(145deg, #1e293b 0%, #0f172a 100%);
        border: 1px solid #334155; border-radius: 20px;
        padding: 48px 40px; margin: 60px auto;
        max-width: 420px; text-align: center;
        box-shadow: 0 8px 32px rgba(0,0,0,0.4);
    }
    .auth-card h2 { color: #e2e8f0; font-size: 1.6rem; margin-bottom: 8px; }
    .auth-card p { color: #94a3b8; font-size: 0.95rem; margin-bottom: 28px; }
    .google-btn {
        display: inline-flex; align-items: center; gap: 12px;
        background: #fff; color: #1a1a1a;
        border: none; border-radius: 10px;
        padding: 12px 28px; font-size: 1rem; font-weight: 600;
        cursor: pointer; text-decoration: none;
        box-shadow: 0 2px 8px rgba(0,0,0,0.2);
        transition: box-shadow 0.2s;
    }
    .google-btn:hover { box-shadow: 0 4px 16px rgba(0,0,0,0.3); }

    .user-badge {
        display: flex; align-items: center; gap: 8px;
        background: rgba(99,102,241,0.12);
        border: 1px solid rgba(99,102,241,0.3);
        border-radius: 10px; padding: 8px 14px;
        font-size: 0.88rem; color: #a5b4fc;
    }

    .result-card {
        background: linear-gradient(145deg, #1e293b 0%, #0f172a 100%);
        border: 1px solid #334155; border-radius: 16px;
        padding: 24px; margin-bottom: 16px;
        box-shadow: 0 4px 24px rgba(0,0,0,0.3);
        animation: fadeIn 0.5s ease-out;
    }
    .result-card h3 { margin-top: 0; font-size: 1.1rem; font-weight: 600; }
    .result-card .content { font-size: 0.95rem; line-height: 1.6; color: #cbd5e1; }

    .badge {
        display: inline-flex; align-items: center; gap: 6px;
        padding: 4px 12px; border-radius: 20px; font-size: 0.8rem; font-weight: 600;
    }
    .badge-safe   { background: rgba(34,197,94,0.15);  color: #22c55e; border: 1px solid rgba(34,197,94,0.3); }
    .badge-unsafe { background: rgba(239,68,68,0.15);  color: #ef4444; border: 1px solid rgba(239,68,68,0.3); }
    .badge-important { background: rgba(234,179,8,0.15); color: #eab308; border: 1px solid rgba(234,179,8,0.3); }
    .badge-routine   { background: rgba(148,163,184,0.15); color: #94a3b8; border: 1px solid rgba(148,163,184,0.3); }

    .metric-row { display: flex; gap: 12px; flex-wrap: wrap; margin-bottom: 16px; }
    .metric-card {
        flex: 1; min-width: 140px;
        background: linear-gradient(145deg, #1e293b 0%, #0f172a 100%);
        border: 1px solid #334155; border-radius: 12px;
        padding: 16px; text-align: center;
    }
    .metric-card .label { font-size: 0.75rem; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.5px; }
    .metric-card .value { font-size: 1.5rem; font-weight: 700; margin-top: 4px; }
    .value-green { color: #22c55e; } .value-red { color: #ef4444; }
    .value-blue  { color: #60a5fa; } .value-purple { color: #a78bfa; }

    .memory-item {
        background: rgba(99,102,241,0.08); border-left: 3px solid #6366f1;
        border-radius: 0 8px 8px 0; padding: 12px 16px;
        margin-bottom: 8px; font-size: 0.9rem; color: #cbd5e1;
    }
    .memory-score { font-size: 0.75rem; color: #818cf8; font-weight: 600; }

    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f172a 0%, #1e1b4b 100%);
    }

    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(12px); }
        to   { opacity: 1; transform: translateY(0); }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# Supabase client
@st.cache_resource
def get_supabase() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

supabase: Client = get_supabase()


# Session helpers
def is_logged_in() -> bool:
    return "access_token" in st.session_state and bool(st.session_state["access_token"])


def get_auth_headers() -> dict:
    return {"Authorization": f"Bearer {st.session_state.get('access_token', '')}"}


def handle_oauth_callback():
    """Handle OAuth callback after Google redirects back."""
    params = st.query_params
    
    if params.get("error"):
        error_desc = params.get("error_description", "Unknown error")
        st.error(f"OAuth error: {error_desc}")
        st.query_params.clear()
        return
    
    code = params.get("code")
    if code and not is_logged_in():
        try:
            response = supabase.auth.exchange_code_for_session({"auth_code": code})
            
            if response and response.user:
                st.session_state["access_token"] = response.session.access_token
                st.session_state["user"] = {
                    "id": response.user.id,
                    "email": response.user.email,
                    "name": (response.user.user_metadata or {}).get("full_name", ""),
                    "avatar": (response.user.user_metadata or {}).get("avatar_url", ""),
                }
                st.query_params.clear()
                st.rerun()
            else:
                st.error("Failed to authenticate with Supabase")
        except Exception as e:
            st.error(f"Login failed: {e}")
            logger.error(f"OAuth exchange error: {e}")
            st.query_params.clear()


def do_login():
    """Start Google OAuth."""
    try:
        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:8501")
        
        result = supabase.auth.sign_in_with_oauth({
            "provider": "google",
            "options": {
                "redirect_to": frontend_url,
                "skip_browser_redirect": False,
            },
        })
        
        if result and hasattr(result, 'url'):
            st.markdown(
                f'<meta http-equiv="refresh" content="0; url={result.url}">',
                unsafe_allow_html=True,
            )
        else:
            st.error("Failed to generate OAuth URL")
    except Exception as e:
        st.error(f"Could not initiate Google login: {e}")
        logger.error(f"OAuth initiation error: {e}")


def do_logout():
    try:
        supabase.auth.sign_out()
    except Exception:
        pass
    for k in ("access_token", "user"):
        st.session_state.pop(k, None)
    st.rerun()


# Handle callback on page load
handle_oauth_callback()


# Auth gate
if not is_logged_in():
    st.markdown('<h1 class="hero-title">🎙️ VoiceTrace AI</h1>', unsafe_allow_html=True)
    st.markdown(
        '<p class="hero-subtitle">Voice-powered business intelligence - speak your day, get insights instantly.</p>',
        unsafe_allow_html=True,
    )
    st.markdown("<br>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown(
            """
            <div class="auth-card">
                <div style="font-size:3.5rem;margin-bottom:12px;">🎙️</div>
                <h2>Welcome to VoiceTrace AI</h2>
                <p>Sign in to start transcribing, extracting insights, and building your voice memory.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("Sign in with Google", type="primary", use_container_width=True):
            do_login()

    st.stop()


# Logged-in user info
user = st.session_state.get("user", {})


# Sidebar
with st.sidebar:
    st.markdown(
        f"""
        <div class="user-badge">
            👤 <span>{user.get("name") or user.get("email", "User")}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.caption(f"📧 {user.get('email', '')}")

    if st.button("Logout", use_container_width=True):
        do_logout()

    st.markdown("---")
    st.markdown("### System Status")

    try:
        r = requests.get(f"{BACKEND_URL}/health", timeout=5)
        health = r.json()
        status = health.get("status", "unknown")
        services = health.get("services", {})
        if status == "healthy":
            st.success("System Online")
        else:
            st.warning(f"System: {status}")
        for svc, svc_status in services.items():
            icon = "✅" if svc_status in ("running", "connected") else "❌"
            st.caption(f"{icon} **{svc.replace('_', ' ').title()}**: {svc_status}")
    except requests.exceptions.ConnectionError:
        st.error("Backend Offline")

    st.markdown("---")
    st.markdown("### Recent Sessions")
    try:
        r = requests.get(
            f"{BACKEND_URL}/transcriptions?limit=5",
            headers=get_auth_headers(),
            timeout=5,
        )
        if r.status_code == 200:
            recent = r.json()
            if recent:
                for mem in recent:
                    ts = mem.get("created_at", "N/A")
                    imp = "⭐" if mem.get("is_important") else "📝"
                    preview = (mem.get("transcript", "") or "")[:60]
                    st.caption(f"{imp} `{ts[:16]}` - {preview}...")
            else:
                st.caption("No sessions yet.")
        else:
            st.caption("Could not load sessions.")
    except Exception:
        st.caption("Unable to load recent sessions.")

    st.markdown("---")
    st.caption("**VoiceTrace AI** · Groq Whisper · LangGraph · Qdrant Cloud · Supabase")


# Main Content
st.markdown('<h1 class="hero-title">🎙️ VoiceTrace AI</h1>', unsafe_allow_html=True)
st.markdown(
    '<p class="hero-subtitle">Voice-powered business intelligence - speak your day, get insights instantly.</p>',
    unsafe_allow_html=True,
)

# Recording / Upload Tabs
tab1, tab2 = st.tabs(["🎙️ Record Audio", "📁 Upload File"])

audio_data = None
audio_source = None

with tab1:
    st.markdown("### Record your voice note")
    st.caption("Click the microphone to start recording. Click again to stop.")
    
    recorded_audio = audio_recorder(
        text="",
        recording_color="#667eea",
        neutral_color="#94a3b8",
        icon_name="microphone",
        icon_size="3x",
    )
    
    if recorded_audio:
        audio_data = recorded_audio
        audio_source = "recording"
        st.success("Recording captured!")
        st.audio(recorded_audio, format="audio/wav")
        
        st.markdown(
            f"""
            <div class="result-card">
                <h3>Recording Info</h3>
                <div class="content">
                    <b>Size:</b> {len(recorded_audio) / 1024:.1f} KB<br>
                    <b>Format:</b> WAV<br>
                    <b>Status:</b> Ready to process
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

with tab2:
    st.markdown("### Upload a pre-recorded file")
    uploaded_file = st.file_uploader(
        "Choose an audio file",
        type=["wav", "mp3", "m4a", "ogg", "flac", "webm"],
        help="Max 3 minutes. Supported: WAV, MP3, M4A, OGG, FLAC, WebM",
    )
    
    if uploaded_file:
        audio_data = uploaded_file.getvalue()
        audio_source = "upload"
        st.audio(uploaded_file, format=uploaded_file.type)
        
        st.markdown(
            f"""
            <div class="result-card">
                <h3>File Info</h3>
                <div class="content">
                    <b>Name:</b> {uploaded_file.name}<br>
                    <b>Size:</b> {uploaded_file.size / 1024:.1f} KB<br>
                    <b>Type:</b> {uploaded_file.type}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

# Process Button
if audio_data:
    if st.button("Process Audio", type="primary", use_container_width=True):

        with st.spinner("Processing your audio through the AI pipeline..."):
            progress = st.progress(0, text="Uploading audio...")
            time.sleep(0.3)
            progress.progress(10, text="Transcribing with Groq Whisper...")

            try:
                if audio_source == "recording":
                    files = {
                        "file": ("recording.wav", audio_data, "audio/wav")
                    }
                else:
                    files = {
                        "file": (uploaded_file.name, audio_data, uploaded_file.type)
                    }
                
                response = requests.post(
                    f"{BACKEND_URL}/process",
                    files=files,
                    headers=get_auth_headers(),
                    timeout=180,
                )

                progress.progress(90, text="Rendering results...")

                if response.status_code == 401:
                    st.error("Session expired. Please log in again.")
                    do_logout()
                    st.stop()

                if response.status_code != 200:
                    st.error(f"Backend error: {response.status_code} - {response.text}")
                    st.stop()

                data = response.json()
                progress.progress(100, text="Done!")
                time.sleep(0.3)
                progress.empty()

            except requests.exceptions.ConnectionError:
                st.error("Cannot reach the backend. Is it running?")
                st.stop()
            except requests.exceptions.Timeout:
                st.error("Request timed out. The audio may be too long or the server is busy.")
                st.stop()
            except Exception as e:
                st.error(f"Error: {e}")
                st.stop()

        if data.get("error"):
            st.error(f"Pipeline Error: {data['error']}")

        safety = data.get("safety_flag", "safe")
        if safety == "unsafe":
            st.markdown(
                '<span class="badge badge-unsafe">UNSAFE - Content Blocked</span>',
                unsafe_allow_html=True,
            )
            st.stop()

        # Show Transcript First
        st.markdown("---")
        st.markdown("## Transcript")
        
        transcript_text = data.get("transcript", "No transcript generated.")
        st.markdown(
            f"""
            <div class="result-card" style="border-color: #667eea;">
                <div class="content" style="font-size: 1.05rem; line-height: 1.8;">
                    {transcript_text}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Results
        st.markdown("---")
        st.markdown("## Analysis Results")

        proc_time = data.get("processing_time_seconds", 0)
        st.caption(f"Processed in **{proc_time:.2f} seconds** | Session: `{data.get('session_id', 'N/A')}`")

        badge_cols = st.columns(3)
        with badge_cols[0]:
            st.markdown('<span class="badge badge-safe">SAFE</span>', unsafe_allow_html=True)
        with badge_cols[1]:
            is_imp = data.get("is_important", False)
            if is_imp:
                st.markdown(
                    '<span class="badge badge-important">IMPORTANT - Stored in Long-Term Memory</span>',
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    '<span class="badge badge-routine">Routine - Stored in Supabase</span>',
                    unsafe_allow_html=True,
                )
        with badge_cols[2]:
            extracted = data.get("extracted_data", {})
            sentiment = extracted.get("sentiment", "neutral")
            sent_emoji = {"positive": "😊", "negative": "😟", "mixed": "😐", "neutral": "😐"}.get(sentiment, "😐")
            st.markdown(f"**Sentiment:** {sent_emoji} {sentiment.title()}")

        left, right = st.columns(2)

        with left:
            st.markdown(
                '<div class="result-card"><h3>Extracted Business Data</h3><div class="content">',
                unsafe_allow_html=True,
            )
            if extracted:
                total_earn = extracted.get("total_earnings")
                total_exp  = extracted.get("total_expenses")
                net        = extracted.get("net_profit")

                if any(v is not None for v in [total_earn, total_exp, net]):
                    st.markdown(
                        f"""
                        <div class="metric-row">
                            <div class="metric-card">
                                <div class="label">Earnings</div>
                                <div class="value value-green">{'₹' + str(total_earn) if total_earn is not None else '-'}</div>
                            </div>
                            <div class="metric-card">
                                <div class="label">Expenses</div>
                                <div class="value value-red">{'₹' + str(total_exp) if total_exp is not None else '-'}</div>
                            </div>
                            <div class="metric-card">
                                <div class="label">Net Profit</div>
                                <div class="value value-blue">{'₹' + str(net) if net is not None else '-'}</div>
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                st.json(extracted)
            else:
                st.caption("No data extracted.")
            st.markdown("</div></div>", unsafe_allow_html=True)

        with right:
            if is_imp and data.get("formatted_memory"):
                st.markdown(
                    f"""
                    <div class="result-card">
                        <h3>Memory Stored in Qdrant Cloud</h3>
                        <div class="content">
                            <span class="badge badge-important">Long-Term Memory</span>
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
                        <h3>Memory Decision</h3>
                        <div class="content">
                            <span class="badge badge-routine">Saved to Supabase</span>
                            <p style="margin-top:12px;">This entry was saved to your Supabase history (not added to vector memory).</p>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            memories = data.get("retrieved_memories", [])
            st.markdown(
                '<div class="result-card"><h3>Retrieved Past Memories</h3><div class="content">',
                unsafe_allow_html=True,
            )
            if memories:
                for mem in memories:
                    score = mem.get("score", 0)
                    text  = mem.get("formatted_memory", "N/A")
                    ts    = mem.get("timestamp", "")[:16]
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

        st.markdown(
            f"""
            <div class="result-card" style="border-color: #6366f1; margin-top: 8px;">
                <h3>AI Analysis & Recommendations</h3>
                <div class="content">{data.get("final_response", "No response generated.").replace(chr(10), "<br>")}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

else:
    st.markdown(
        """
        <div style="text-align: center; padding: 60px 20px; color: #64748b;">
            <div style="font-size: 4rem; margin-bottom: 16px;">🎙️</div>
            <h3 style="color: #94a3b8;">Record your voice or upload an audio file</h3>
            <p>Record your business day - sales, expenses, insights - and let AI do the rest.</p>
            <p style="font-size: 0.85rem; color: #475569;">
                Click the microphone to record live<br>
                Or upload: WAV, MP3, M4A, OGG, FLAC, WebM · Max 3 minutes
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

# Footer
st.markdown("---")
st.markdown(
    """
    <div style="text-align: center; color: #475569; font-size: 0.8rem; padding: 12px 0;">
        <b>VoiceTrace AI</b> · Groq Whisper · LangGraph · Qdrant Cloud · Supabase<br>
        Built for hackathon excellence
    </div>
    """,
    unsafe_allow_html=True,
)
