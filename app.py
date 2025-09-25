from __future__ import annotations
import streamlit as st
from pathlib import Path

# Agents
from agents.transcript_cleaner import transcribe_and_clean
from agents.keypoints_extractor import extract_outline
from agents.slide_generator import outline_to_pptx

# Utils
from utils.fs import DATA_IN
from utils import auth   # 🔥 auth utils

st.set_page_config(page_title="Lecture Notes Processor", layout="wide")

# --------------------------
# SESSION STATE
# --------------------------
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "username" not in st.session_state:
    st.session_state.username = None

# --------------------------
# LOGIN / SIGNUP SCREEN
# --------------------------
if not st.session_state.authenticated:
    st.markdown(
    """
    <style>
    /* Center container */
    .main .block-container {
        display: flex;
        justify-content: center;
        align-items: center;
        min-height: 100vh;
        padding: 0;
    }

    /* Card */
    .login-card {
        width: 100%;
        max-width: 350px;  /* smaller width */
        padding: 1.8rem 1.2rem;
        border-radius: 12px;
        background-color: #fff;
        box-shadow: 0 6px 18px rgba(0,0,0,0.15);
        text-align: center;
    }

    /* Title */
    .login-card h2 {
        font-size: 1.4rem;
        margin-bottom: 1rem;
    }

    /* Streamlit inputs inside login-card */
    .login-card .stTextInput,
    .login-card .stPasswordInput,
    .login-card .stButton {
        margin-top: 0.6rem;
    }

    /* Force inputs to not stretch full width of page */
    .stTextInput > div > div > input,
    .stPasswordInput > div > div > input {
        width: 100% !important;
        border-radius: 8px;
        padding: 0.6rem;
        font-size: 0.95rem;
    }

    /* Buttons full width only inside the card */
    .login-card .stButton button {
        width: 100% !important;
        border-radius: 8px;
        padding: 0.6rem;
    }

    /* Fix columns so login/signup buttons don't stretch */
    .login-card .stColumns {
        display: flex;
        gap: 0.5rem;
    }
    .login-card .stColumns > div {
        flex: 1;
    }
    </style>
    """,
    unsafe_allow_html=True,
    )
    
   


    with st.container():
        
        st.image("https://img.icons8.com/fluency/96/brain.png", width=80)
        st.markdown("## 🧠 Lecture Notes Processor")

        # Fake tabs via session_state
        if "login_tab" not in st.session_state:
            st.session_state.login_tab = "login"

        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔑 Login", use_container_width=True):
                st.session_state.login_tab = "login"
        with col2:
            if st.button("🆕 Signup", use_container_width=True):
                st.session_state.login_tab = "signup"

        if st.session_state.login_tab == "login":
            uname = st.text_input("Username", key="login_user")
            pwd = st.text_input("Password", type="password", key="login_pass")
            if st.button("Login", use_container_width=True):
                if auth.login(uname, pwd):
                    st.session_state.authenticated = True
                    st.session_state.username = uname
                    st.success(f"✅ Welcome back, {uname}!")
                    st.rerun()
                else:
                    st.error("❌ Invalid credentials")
        else:
            uname_new = st.text_input("New Username", key="signup_user")
            pwd_new = st.text_input("New Password", type="password", key="signup_pass")
            if st.button("Signup", use_container_width=True):
                if auth.signup(uname_new, pwd_new):
                    st.success("🎉 Account created! Please log in.")
                    st.session_state.login_tab = "login"
                else:
                    st.error("⚠️ Username already exists")

        st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# --------------------------
# MAIN APP (pipeline)
# --------------------------
col1, col2 = st.columns([4, 1])
with col1:
    st.title("🧠 Lecture Notes Processor")
    st.caption("Transcript Cleaner → Key Points Extractor → Slide Generator")
    st.write(f"👤 Logged in as: **{st.session_state.username}**")
with col2:
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state.authenticated = False
        st.session_state.username = None
        st.rerun()

with st.sidebar:
    st.header("📂 Upload or Select a File")
    up = st.file_uploader(
        "Upload Audio / Video / PDF / TXT",
        type=["mp3", "wav", "m4a", "mp4", "mov", "pdf", "txt", "md"],
    )
    uploaded_path = None
    if up:
        safe_name = f"{st.session_state.username}_{up.name.replace(' ', '_')}"
        dest = DATA_IN / safe_name
        with open(dest, "wb") as f:
            f.write(up.getbuffer())
        uploaded_path = dest
        st.success(f"✅ File saved: {dest.name}")

    st.header("📑 Choose Existing File")
    choices = [p.name for p in DATA_IN.glob(f"{st.session_state.username}_*") if p.is_file()]
    choice = st.selectbox("Available files", ["—"] + choices)

    st.divider()
    run_btn = st.button("🚀 Run Pipeline", type="primary", use_container_width=True)

# --------------------------
# PIPELINE EXECUTION
# --------------------------
if run_btn:
    path = uploaded_path or (DATA_IN / choice if choice and choice != "—" else None)

    if path and path.exists():
        with st.spinner("🧹 Cleaning transcript / transcribing..."):
            cleaned, cleaned_path = transcribe_and_clean(str(path))

        with st.spinner("🔑 Extracting key points (structured JSON)..."):
            outline, outline_path = extract_outline(cleaned)

        with st.spinner("🖼️ Generating slides (.pptx)..."):
            pptx_path = outline_to_pptx(outline, filename_stem=Path(path).stem)

        tab1, tab2, tab3 = st.tabs(["📜 Transcript", "🗂 JSON Outline", "🎞 Slides"])

        with tab1:
            st.subheader("Cleaned Transcript")
            st.code(
                cleaned[:5000] + ("..." if len(cleaned) > 5000 else ""),
                language="markdown",
            )
            st.caption(f"Saved: {cleaned_path}")

        with tab2:
            st.subheader("Outline (JSON)")
            st.code(
                outline.model_dump_json(indent=2)[:5000]
                + ("..." if len(outline.model_dump_json()) > 5000 else ""),
                language="json",
            )
            st.caption(f"Saved: {outline_path}")

        with tab3:
            st.subheader("Generated Slides")
            st.success(f"✅ Slides saved: {pptx_path}")
            st.download_button(
                "⬇️ Download PPTX",
                data=open(pptx_path, "rb").read(),
                file_name=Path(pptx_path).name,
                use_container_width=True,
            )
    else:
        st.error("⚠️ Please upload or pick a valid file first.")

# --------------------------
# STORAGE INFO
# --------------------------
with st.expander("📂 Where files are stored"):
    st.markdown(
        """
        - **Uploads** → `data/input/` (prefixed by username)  
        - **Cleaned transcript** → `data/processed/cleaned_*.txt`  
        - **Outline JSON** → `data/processed/outline_*.json`  
        - **Slides** → `outputs/slides/*.pptx`  
        - **Run logs** → `runs/`
        """
    )
