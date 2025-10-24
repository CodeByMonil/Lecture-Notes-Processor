from __future__ import annotations
import streamlit as st
from pathlib import Path
import time
import json
import io
import pandas as pd
from typing import Optional

# -------------------------
# Agents (existing pipeline)
# -------------------------
from agents.transcript_cleaner import transcribe_and_clean
from agents.keypoints_extractor import extract_outline
from agents.slide_generator import outline_to_pptx
from agents.retriever import retrieve_context, simple_retrieve_context

# Guide agent optional (we will try to import)
try:
    from agents.guide_agent import run_guide_agent
    GUIDE_AVAILABLE = True
except Exception:
    GUIDE_AVAILABLE = False

# -------------------------
# Utils
# -------------------------
from utils.fs import DATA_IN
from utils import auth

# -------------------------
# Lottie Animations
# -------------------------
try:
    from streamlit_lottie import st_lottie
    import requests
    LOTTIE_AVAILABLE = True
except ImportError:
    LOTTIE_AVAILABLE = False

def load_lottie_url(url: str):
    """Load Lottie animation from URL"""
    if not LOTTIE_AVAILABLE:
        return None
    try:
        r = requests.get(url)
        if r.status_code == 200:
            return r.json()
    except:
        return None
    return None

# Academic-themed Lottie URLs
LOTTIE_URLS = {
    "lecture": "https://assets1.lottiefiles.com/packages/lf20_gns0bjrc.json",
    "notes": "https://assets1.lottiefiles.com/packages/lf20_5ttqgqgd.json",
    "processing": "https://assets1.lottiefiles.com/packages/lf20_t9gkkiec.json",
    "success": "https://assets1.lottiefiles.com/packages/lf20_yB6n1R.json",
    "slides": "https://assets1.lottiefiles.com/packages/lf20_ukwybttx.json",
    "login": "https://assets1.lottiefiles.com/packages/lf20_khsfqslr.json",
    "upload": "https://assets1.lottiefiles.com/packages/lf20_5ttqgqgd.json"
}

# -------------------------
# Configuration / Paths
# -------------------------
OUT_ROOT = Path("outputs")
SLIDES_DIR = OUT_ROOT / "slides"
GUIDES_DIR = OUT_ROOT / "guides"
USERS_FILE = OUT_ROOT / "users.json"  # store minimal signup metadata (plan)
for p in (SLIDES_DIR, GUIDES_DIR, DATA_IN, OUT_ROOT):
    p.mkdir(parents=True, exist_ok=True)

st.set_page_config(
    page_title="SlideCraft — Lecture Notes Processor", 
    page_icon="🎓", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# -------------------------
# Session state defaults
# -------------------------
if "page" not in st.session_state:
    st.session_state.page = "home"  # home, upload, processing, outputs, account
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "username" not in st.session_state:
    st.session_state.username = None
if "user_plan" not in st.session_state:
    st.session_state.user_plan = None
if "uploaded_path" not in st.session_state:
    st.session_state.uploaded_path = None
if "use_kb" not in st.session_state:
    st.session_state.use_kb = True
if "run_pipeline" not in st.session_state:
    st.session_state.run_pipeline = False
if "pptx_bytes" not in st.session_state:
    st.session_state.pptx_bytes = None
if "pdf_bytes" not in st.session_state:
    st.session_state.pdf_bytes = None
if "pptx_path" not in st.session_state:
    st.session_state.pptx_path = None
if "pdf_path" not in st.session_state:
    st.session_state.pdf_path = None
if "login_tab" not in st.session_state:
    st.session_state.login_tab = "login"
if "processing_step" not in st.session_state:
    st.session_state.processing_step = 0
if "processing_status" not in st.session_state:
    st.session_state.processing_status = ""

# -------------------------
# Helper: users file management
# -------------------------
def load_users():
    if USERS_FILE.exists():
        try:
            return json.loads(USERS_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}

def save_user_meta(username: str, plan: str):
    users = load_users()
    users[username] = {"plan": plan, "created_at": int(time.time())}
    USERS_FILE.write_text(json.dumps(users, indent=2), encoding="utf-8")

def get_user_plan(username: str) -> Optional[str]:
    users = load_users()
    return users.get(username, {}).get("plan")

def is_pro_user():
    """Check if current user is a Pro user"""
    return st.session_state.user_plan == "SlideCraft Pro"

def get_max_upload_size():
    """Get max upload size based on user plan"""
    return 1 * 1024 * 1024 * 1024 if is_pro_user() else 250 * 1024 * 1024  # 1GB for Pro, 250MB for Free

# -------------------------
# Styling: top nav + small helpers
# -------------------------
st.markdown(
    """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .top-nav { 
        display:flex; 
        gap:6px; 
        align-items:center; 
        padding:12px 16px; 
        background: linear-gradient(90deg, #eef2ff, #f8fafc); 
        border-radius:12px;
        margin-bottom: 2rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    .nav-item { 
        padding:10px 16px; 
        border-radius:8px; 
        cursor:pointer;
        transition: all 0.3s ease;
        font-weight: 500;
    }
    .nav-item.active { 
        background: linear-gradient(135deg, #3b82f6, #1e40af); 
        color:white; 
        font-weight:600;
        box-shadow: 0 2px 8px rgba(59, 130, 246, 0.3);
    }
    .nav-item:hover:not(.active) {
        background: rgba(59, 130, 246, 0.1);
    }
    .small-muted { color:#64748b; font-size:0.95rem; }
    .file-card {
        background: linear-gradient(135deg, #f8fafc, #f1f5f9);
        border-radius: 12px;
        padding: 1.5rem;
        border-left: 4px solid #3b82f6;
        margin: 1rem 0;
    }
    .feature-card {
        background: white;
        border-radius: 12px;
        padding: 1.5rem;
        border: 1px solid #e2e8f0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        height: 100%;
    }
    .stats-card {
    background: linear-gradient(135deg, #e8f4f8 0%, #c5e1f6 100%);
    border-radius: 12px;
    padding: 1.5rem;
    text-align: center;
    color: #2c3e50;
    box-shadow: 0 4px 12px rgba(30, 58, 138, 0.15);
    }
    .pro-badge {
        background: linear-gradient(135deg, #f59e0b, #d97706);
        color: white;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    .free-badge {
        background: linear-gradient(135deg, #6b7280, #4b5563);
        color: white;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    
    /* Progress container styling */
    .progress-container {
        margin: 2rem 0;
        padding: 1.5rem;
        background: linear-gradient(135deg, #f8fafc, #f1f5f9);
        border-radius: 12px;
        border: 1px solid #e2e8f0;
    }
    
    /* Blue gradient buttons */
    .stButton button {
        border-radius: 12px;
        transition: all 0.3s ease;
        border: none;
    }
    
    .stButton button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
    }
    
    /* Primary buttons - Blue gradient */
    .stButton button[kind="primary"] {
        background: linear-gradient(135deg, #3b82f6, #1e40af);
        color: white;
    }
    
    .stButton button[kind="primary"]:hover {
        background: linear-gradient(135deg, #2563eb, #1e40af);
        box-shadow: 0 6px 20px rgba(59, 130, 246, 0.4);
    }
    
    /* Secondary buttons */
    .stButton button[kind="secondary"] {
        background: linear-gradient(135deg, #f8fafc, #e2e8f0);
        color: #1e40af;
        border: 1px solid #3b82f6;
    }
    
    .stButton button[kind="secondary"]:hover {
        background: linear-gradient(135deg, #f1f5f9, #dbeafe);
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.2);
    }
    
    /* Pro button styling */
    .stButton button[kind="pro"] {
        background: linear-gradient(135deg, #f59e0b, #d97706);
        color: white;
        border: none;
    }
    
    .stButton button[kind="pro"]:hover {
        background: linear-gradient(135deg, #eab308, #b45309);
        box-shadow: 0 6px 20px rgba(245, 158, 11, 0.4);
    }
    
    /* Error button styling - Blue theme instead of red */
    .stButton button[kind="primary"]:disabled {
        background: linear-gradient(135deg, #9ca3af, #6b7280);
        color: #e5e7eb;
        cursor: not-allowed;
    }
    
    /* Alert styling */
    .stAlert {
        border-radius: 12px;
    }
    
    .stSuccess {
        background: linear-gradient(135deg, #dbeafe, #eff6ff);
        border: 1px solid #60a5fa;
        color: #1e40af;
    }
    
    .stError {
        background: linear-gradient(135deg, #fef2f2, #fecaca);
        border: 1px solid #fca5a5;
        color: #dc2626;
    }
    
    .stInfo {
        background: linear-gradient(135deg, #f0f9ff, #e0f2fe);
        border: 1px solid #7dd3fc;
        color: #0369a1;
    }
    
    .stWarning {
        background: linear-gradient(135deg, #fffbeb, #fed7aa);
        border: 1px solid #fdba74;
        color: #ea580c;
    }
    
    /* Custom file uploader styling */
    .stFileUploader > label > div:first-child {
        display: none !important;
    }
    
    /* Hide the default 'Limit 200MB...' line and add custom message */
    [data-testid="stFileUploader"] section div:nth-child(2) {
        display: none;
    }

    [data-testid="stFileUploader"] section div:nth-child(1)::after {
        content: "Upload a PDF or .TXT file";
        color: gray;
        font-size: 14px;
        display: block;
        margin-top: 4px;
    }

    /* Download button styling - Blue shade */
    .stDownloadButton button {
        background: linear-gradient(135deg, #3b82f6, #1e40af) !important;
        color: white !important;
        border: 1px solid #2563eb !important;
        border-radius: 12px !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
    }

    .stDownloadButton button:hover {
        background: linear-gradient(135deg, #2563eb, #1e40af) !important;
        color: white !important;
        border-color: #1d4ed8 !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4) !important;
    }

    /* Specific styling for slides download button */
    div[data-testid*="DownloadSlides"] button {
        background: linear-gradient(135deg, #3b82f6, #1e40af) !important;
        color: white !important;
        border: 1px solid #2563eb !important;
    }

    /* Specific styling for guide download button */
    div[data-testid*="DownloadGuide"] button {
        background: linear-gradient(135deg, #3b82f6, #1e40af) !important;
        color: white !important;
        border: 1px solid #2563eb !important;
    }
    
    /* Pro pricing badge */
    .pro-price {
        background: linear-gradient(135deg, #f59e0b, #d97706);
        color: white;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.9rem;
        font-weight: 600;
        display: inline-block;
        margin-left: 10px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# -------------------------
# Login/Signup Screen (Split Layout)
# -------------------------
def show_login_signup():
    st.markdown(
        """
        <style>
        .main .block-container {
            padding: 0;
            max-width: 100%;
        }
        .split-screen {
            display: flex;
            height: 100vh;
        }
        .brand-side {
            flex: 1;
            background: linear-gradient(135deg, #e8f4f8 0%, #c5e1f6 100%);
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            padding: 3rem;
            color: #2c3e50;
            text-align: center;
            position: relative;
            overflow: hidden;
        }
        /* Subtle texture overlay */
        .brand-side::before {
            content: "";
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background-image: radial-gradient(#a0c4e0 1px, transparent 1px);
            background-size: 25px 25px;
            opacity: 0.08;
            pointer-events: none;
        }
        .form-side {
            flex: 1;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 2rem;
            background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
        }
        .login-card {
            width: 100%;
            max-width: 420px;
            padding: 2.5rem;
            border-radius: 20px;
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(12px);
            box-shadow: 
                0 8px 32px rgba(30, 58, 138, 0.1),
                0 2px 8px rgba(30, 58, 138, 0.06);
            border: 1px solid rgba(148, 163, 184, 0.2);
        }
        .brand-title {
            font-size: 3.2rem;
            font-weight: 700;
            margin-bottom: 1rem;
            background: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            font-family: 'Georgia', 'Times New Roman', serif;
        }
        .brand-subtitle {
            font-size: 1.3rem;
            color: #475569;
            max-width: 480px;
            line-height: 1.6;
            font-weight: 400;
            margin-bottom: 2.5rem;
            opacity: 0.9;
        }
        .feature-item {
            display: flex;
            align-items: center;
            margin-bottom: 1rem;
            color: #475569;
            font-size: 1.1rem;
            padding: 0.8rem 1rem;
            background: rgba(255, 255, 255, 0.7);
            border-radius: 12px;
            border-left: 4px solid #3b82f6;
        }
        .feature-icon {
            margin-right: 1rem;
            font-size: 1.4rem;
            min-width: 30px;
        }
        .form-header {
            color: #1e40af;
            margin-bottom: 1.5rem;
            text-align: center;
            font-size: 1.8rem;
            font-weight: 600;
        }
        
        /* Tab buttons styling */
        .tab-container {
            display: flex;
            gap: 0.5rem;
            margin-bottom: 2rem;
            background: #f1f5f9;
            padding: 0.5rem;
            border-radius: 14px;
        }
        .tab-button {
            flex: 1;
            padding: 0.75rem 1rem;
            border: none;
            border-radius: 10px;
            background: transparent;
            color: #64748b;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.3s ease;
            text-align: center;
        }
        .tab-button.active {
            background: linear-gradient(135deg, #3b82f6 0%, #1e40af 100%);
            color: white;
            box-shadow: 0 2px 8px rgba(59, 130, 246, 0.3);
        }
        .tab-button:hover:not(.active) {
            background: rgba(59, 130, 246, 0.1);
            color: #1e40af;
        }
        
        /* Improved form elements */
        .stTextInput > div > div > input,
        .stPasswordInput > div > div > input {
            border-radius: 12px;
            padding: 1rem;
            font-size: 1rem;
            border: 2px solid #e2e8f0;
            background: #f8fafc;
            transition: all 0.3s ease;
        }
        
        .stTextInput > div > div > input:focus,
        .stPasswordInput > div > div > input:focus {
            border-color: #3b82f6;
            box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
            background: white;
        }
        
        .stButton button {
            width: 100%;
            border-radius: 12px;
            padding: 1rem;
            font-size: 1.1rem;
            background: linear-gradient(135deg, #3b82f6 0%, #1e40af 100%);
            border: none;
            color: white;
            font-weight: 600;
            transition: all 0.3s ease;
            margin-top: 1rem;
        }
        
        .stButton button:hover {
            transform: translateY(-1px);
            box-shadow: 0 6px 20px rgba(59, 130, 246, 0.3);
        }
        
        /* Hide streamlit elements */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        
        /* Custom input labels */
        .stTextInput label, .stPasswordInput label {
            color: #475569 !important;
            font-weight: 500;
            margin-bottom: 0.3rem;
        }
        
        /* Plan selection styling */
        .plan-option {
            padding: 1.5rem;
            border-radius: 12px;
            margin: 0.5rem 0;
            border: 2px solid #e2e8f0;
            transition: all 0.3s ease;
            cursor: pointer;
            background: white;
        }
        
        .plan-option:hover {
            border-color: #3b82f6;
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(59, 130, 246, 0.15);
        }
        
        .plan-option.selected {
            border-color: #3b82f6;
            background: linear-gradient(135deg, #f0f9ff, #e0f2fe);
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(59, 130, 246, 0.2);
        }
        
        .plan-option.pro {
            border: 2px solid #e2e8f0;
        }
        
        .plan-option.pro.selected {
            border-color: #f59e0b;
            background: linear-gradient(135deg, #fefce8, #fef3c7);
            box-shadow: 0 6px 20px rgba(245, 158, 11, 0.2);
        }
        
        .plan-name {
            font-size: 1.3rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
            color: #1e40af;
        }
        
        .plan-option.pro .plan-name {
            color: #d97706;
        }
        
        .plan-price {
            font-size: 1.2rem;
            font-weight: 700;
            color: #059669;
            margin-bottom: 1rem;
            padding: 0.3rem 0.8rem;
            background: #d1fae5;
            border-radius: 20px;
            display: inline-block;
        }
        
        .pro-price {
            font-size: 1.2rem;
            font-weight: 700;
            color: #d97706;
            margin-bottom: 1rem;
            padding: 0.3rem 0.8rem;
            background: #fef3c7;
            border-radius: 20px;
            display: inline-block;
        }
        
        .plan-features {
            font-size: 0.9rem;
            color: #64748b;
            line-height: 1.5;
        }
        
        .plan-features ul {
            margin: 0;
            padding-left: 1.2rem;
        }
        
        .plan-features li {
            margin-bottom: 0.3rem;
        }
        
        /* Hide radio buttons */
        .stRadio {
            display: none !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(
            """
            <div class="brand-side">
                <div style="font-size: 4.5rem; margin-bottom: 1.5rem; filter: drop-shadow(0 4px 12px rgba(0, 0, 0, 0.2));">📚</div>
                <h1 class="brand-title">SlideCraft</h1>
                <p class="brand-subtitle">
                    Transform your lecture notes and documents into professional 
                    presentation slides with AI-powered processing.
                </p>
                <div style="text-align: left; max-width: 420px; margin: 0 auto;">
                    <div class="feature-item">
                        <span class="feature-icon">📄</span>
                        <span><strong>Document Processing</strong> - Convert PDF and text files</span>
                    </div>
                    <div class="feature-item">
                        <span class="feature-icon">🔍</span>
                        <span><strong>Key Point Extraction</strong> - Identify main concepts</span>
                    </div>
                    <div class="feature-item">
                        <span class="feature-icon">📊</span>
                        <span><strong>Slide Generation</strong> - Create presentation-ready slides</span>
                    </div>
                    <div class="feature-item">
                        <span class="feature-icon">🎨</span>
                        <span><strong>Academic Formatting</strong> - Professional templates</span>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    with col2:
        with st.container():
            # Animation based on tab
            st.markdown('<div style="text-align: center; margin: 1.5rem 0;">', unsafe_allow_html=True)
            if st.session_state.login_tab == "login":
                lottie_anim = load_lottie_url(LOTTIE_URLS["login"])
                if lottie_anim and LOTTIE_AVAILABLE:
                    st_lottie(lottie_anim, height=120, key="login_anim")
                else:
                    st.markdown('<div style="font-size: 4rem;">🔑</div>', unsafe_allow_html=True)
                st.markdown('<h2 class="form-header">Welcome Back</h2>', unsafe_allow_html=True)
            else:
                lottie_anim = load_lottie_url(LOTTIE_URLS["notes"])
                if lottie_anim and LOTTIE_AVAILABLE:
                    st_lottie(lottie_anim, height=120, key="signup_anim")
                else:
                    st.markdown('<div style="font-size: 4rem;">✨</div>', unsafe_allow_html=True)
                st.markdown('<h2 class="form-header">Create Account</h2>', unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
            
            # Single tab switcher - using Streamlit buttons only (no duplicates)
            tab_col1, tab_col2 = st.columns(2)
            with tab_col1:
                if st.button(
                    "🔑 Login", 
                    use_container_width=True, 
                    key="login_tab_btn",
                    type="primary" if st.session_state.login_tab == "login" else "secondary"
                ):
                    st.session_state.login_tab = "login"
                    st.rerun()
            with tab_col2:
                if st.button(
                    "✨ Sign Up", 
                    use_container_width=True, 
                    key="signup_tab_btn",
                    type="primary" if st.session_state.login_tab == "signup" else "secondary"
                ):
                    st.session_state.login_tab = "signup"
                    st.rerun()
            
            # Forms
            if st.session_state.login_tab == "login":
                login_user = st.text_input("👤 Username", key="login_username", placeholder="Enter your username")
                login_pass = st.text_input("🔒 Password", type="password", key="login_password", placeholder="Enter your password")
                
                if st.button("Access SlideCraft", use_container_width=True, type="primary", key="btn_login"):
                    try:
                        ok = auth.login(login_user, login_pass)
                    except Exception:
                        ok = False
                    if ok:
                        st.session_state.authenticated = True
                        st.session_state.username = login_user
                        st.session_state.user_plan = get_user_plan(login_user) or "SlideCraft Free"
                        st.success(f"🎉 Welcome back, {login_user}!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("❌ Invalid credentials")
            else:
                signup_user = st.text_input("👤 Choose Username", key="signup_username", placeholder="Create a username")
                signup_pass = st.text_input("🔒 Create Password", type="password", key="signup_password", placeholder="Choose a secure password")
                
                # Plan selection with clickable boxes (no radio buttons)
                st.markdown("### 📦 Choose Your Plan")
                
                # Initialize selected_plan in session state if not exists
                if "selected_plan" not in st.session_state:
                    st.session_state.selected_plan = "SlideCraft Free"
                
                # Display plan options as clickable boxes
                col1, col2 = st.columns(2)
                
                with col1:
                    is_free_selected = st.session_state.selected_plan == "SlideCraft Free"
                    free_class = "plan-option selected" if is_free_selected else "plan-option"
                    
                    # Free plan box
                    if st.button(
                        "Select Free Plan", 
                        key="free_plan_btn",
                        use_container_width=True,
                        type="primary" if is_free_selected else "secondary"
                    ):
                        st.session_state.selected_plan = "SlideCraft Free"
                        st.rerun()
                    
                    st.markdown(
                        f"""
                        <div class="{free_class}">
                            <div class="plan-name">SlideCraft Free</div>
                            <div class="plan-price">Free Forever</div>
                            <div class="plan-features">
                                <ul>
                                    <li>250MB file uploads</li>
                                    <li>Basic slide generation</li>
                                    <li>Standard processing</li>
                                    <li>Community support</li>
                                </ul>
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                    
                with col2:
                    is_pro_selected = st.session_state.selected_plan == "SlideCraft Pro"
                    pro_class = f"plan-option pro {'selected' if is_pro_selected else ''}"
                    
                    # Pro plan box
                    if st.button(
                        "Select Pro Plan", 
                        key="pro_plan_btn",
                        use_container_width=True,
                        type="primary" if is_pro_selected else "secondary"
                    ):
                        st.session_state.selected_plan = "SlideCraft Pro"
                        st.rerun()
                    
                    st.markdown(
                        f"""
                        <div class="{pro_class}">
                            <div class="plan-name">SlideCraft Pro</div>
                            <div class="pro-price">999 LKR / Month</div>
                            <div class="plan-features">
                                <ul>
                                    <li>1GB file uploads</li>
                                    <li>Knowledge Base integration</li>
                                    <li>Priority processing</li>
                                    <li>Advanced formatting</li>
                                    <li>Premium support</li>
                                </ul>
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                
                # Show selected plan confirmation
                st.info(f"**Selected Plan:** {st.session_state.selected_plan}")
                
                if st.button("Start Creating Slides", use_container_width=True, type="primary", key="btn_signup"):
                    if not signup_user or not signup_pass:
                        st.error("⚠️ Please fill in all fields")
                    else:
                        try:
                            created = auth.signup(signup_user, signup_pass)
                        except Exception:
                            created = True
                        if created:
                            plan_short = st.session_state.selected_plan
                            save_user_meta(signup_user, plan_short)
                            
                            if plan_short == "SlideCraft Pro":
                                st.info("🚀 Welcome to SlideCraft Pro! This would redirect to our secure payment portal.")
                                st.markdown("**SlideCraft Pro - 999 LKR / Month**")
                                time.sleep(3)
                            else:
                                st.success("✅ Free account created successfully!")
                                time.sleep(2)
                                
                            st.session_state.login_tab = "login"
                            st.rerun()
                        else:
                            st.error("⚠️ Signup failed — username may already exist.")

# -------------------------
# Top navigation bar component
# -------------------------
def top_nav():
    nav_col = st.container()
    with nav_col:

        cols = st.columns([2, 6, 1])
        with cols[0]:
            st.markdown(
                "<div style='display:flex;align-items:center;gap:10px'>"
                "<div style='font-size:1.8rem'>🎓</div>"
                "<div style='font-weight:700; font-size:1.3rem'>SlideCraft</div>"
                "</div>", 
                unsafe_allow_html=True
            )
        with cols[1]:
            nav_items = ["home", "upload", "outputs", "account"]
            labels = ["🏠 Home", "📤 Upload", "📁 Outputs", "👤 Account"]
            nav_cols = st.columns(len(nav_items))
            for i, key in enumerate(nav_items):
                is_active = (st.session_state.page == key)
                if nav_cols[i].button(labels[i], key=f"nav_{key}", use_container_width=True):
                    st.session_state.page = key
                    if key == "home":
                        st.session_state.run_pipeline = False
        with cols[2]:
            if st.session_state.authenticated and st.session_state.username:
                plan_badge = "pro-badge" if is_pro_user() else "free-badge"
                plan_text = "PRO" if is_pro_user() else "FREE"
                st.markdown(
                    f"<div style='text-align:right'>👤 <strong>{st.session_state.username}</strong><br>"
                    f"<span class='{plan_badge}'>{plan_text}</span></div>",
                    unsafe_allow_html=True
                )
        st.markdown('</div>', unsafe_allow_html=True)

# -------------------------
# Page: Account (Login / Signup) - Simple version when authenticated
# -------------------------
def account_page():
    st.markdown("## 👤 Account Settings")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### Your Account")
        
        # Plan info with badge
        plan_badge = "🟢 PRO" if is_pro_user() else "⚪ FREE"
        plan_color = "#10b981" if is_pro_user() else "#6b7280"
        
        st.info(f"**Username:** {st.session_state.username}  \n"
                f"**Plan:** {st.session_state.user_plan} {plan_badge}  \n"
                f"**Status:** Active  \n"
                f"**Max Upload Size:** {get_max_upload_size() / (1024 * 1024)}MB  \n"
                f"**Knowledge Base:** {'✅ Available' if is_pro_user() else '❌ Pro Only'}")
        
        if st.button("🔄 Refresh Account Data", use_container_width=True):
            st.rerun()
            
    with col2:
        st.markdown("### Quick Actions")
        if st.button("🚪 Logout", use_container_width=True, type="primary"):
            st.session_state.authenticated = False
            st.session_state.username = None
            st.session_state.user_plan = None
            st.session_state.page = "home"
            st.rerun()
        
        # Upgrade button for free users
        if not is_pro_user():
            st.markdown("---")
            st.markdown("### 🚀 Upgrade to Pro")
            st.markdown("""
            **SlideCraft Pro Benefits:**
            - ✅ **1GB** file uploads (vs 250MB Free)
            - ✅ **Knowledge Base** integration
            - ✅ **Priority** processing
            - ✅ **Advanced** formatting options
            - ✅ **Unlimited** slide generation
            - ✅ **Premium** support
            """)
            
            st.markdown("### 💰 Pricing")
            st.markdown("""
            **SlideCraft Pro:** 999 LKR / Month
            """)
            
            if st.button("⭐ Upgrade to SlideCraft Pro", use_container_width=True, type="primary", key="upgrade_btn"):
                st.info("🚀 Upgrade feature coming soon! This would redirect to our secure payment portal.")

# -------------------------
# Page: Home
# -------------------------
def home_page():
    st.markdown("## 🎓 Welcome to SlideCraft")
    
    # Hero section with animation
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown("""
        ### Transform Your Documents into Professional Presentations
        
        SlideCraft uses AI to automatically convert your PDF and text documents into 
        beautifully formatted presentation slides and comprehensive instructor guides.
        
        **Get started in 3 simple steps:**
        1. **Upload** your PDF or text files
        2. **Process** with AI-enhanced knowledge base
        3. **Download** ready-to-use slides and guides
        """)
        
        if st.button("🚀 Get Started → Upload Files", use_container_width=True, type="primary"):
            st.session_state.page = "upload"
            
    with col2:
        lottie_anim = load_lottie_url(LOTTIE_URLS["slides"])
        if lottie_anim and LOTTIE_AVAILABLE:
            st_lottie(lottie_anim, height=200, key="home_anim")
        else:
            st.markdown('<div style="font-size: 8rem; text-align: center;">📊</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Features grid
    st.markdown("## ✨ Why Choose SlideCraft?")
    cols = st.columns(3)
    
    features = [
        {"icon": "📄", "title": "Document Processing", "desc": "Convert PDF and text files to clean content"},
        {"icon": "🔍", "title": "Key Point Extraction", "desc": "Automatically identify main concepts and structure"},
        {"icon": "📊", "title": "Professional Slides", "desc": "Academic templates with proper formatting"},
        {"icon": "🧠", "title": "Knowledge Enhanced", "desc": "Leverage course materials for better content"},
        {"icon": "📝", "title": "Instructor Guides", "desc": "Comprehensive teaching notes and resources"},
        {"icon": "⚡", "title": "Fast Processing", "desc": "Quick turnaround for your documents"}
    ]
    
    for i, feature in enumerate(features):
        with cols[i % 3]:
            st.markdown(
                f"""
                <div class="feature-card">
                    <div style="font-size: 2.5rem; margin-bottom: 1rem;">{feature['icon']}</div>
                    <h3 style="margin-bottom: 0.5rem;">{feature['title']}</h3>
                    <p style="color: #64748b; margin: 0;">{feature['desc']}</p>
                </div>
                """,
                unsafe_allow_html=True
            )
    
    # Stats section
    st.markdown("---")
    st.markdown("## 📈 Your SlideCraft Stats")
    
    try:
        slide_files = list(SLIDES_DIR.glob(f"*{st.session_state.username}*"))
        guide_files = list(GUIDES_DIR.glob(f"*{st.session_state.username}*"))
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(
                f"""
                <div class="stats-card">
                    <div style="font-size: 2rem;">📊</div>
                    <h3>{len(slide_files)}</h3>
                    <p>Slides Generated</p>
                </div>
                """,
                unsafe_allow_html=True
            )
        
        with col2:
            st.markdown(
                f"""
                <div class="stats-card">
                    <div style="font-size: 2rem;">📝</div>
                    <h3>{len(guide_files)}</h3>
                    <p>Guides Created</p>
                </div>
                """,
                unsafe_allow_html=True
            )
            
        with col3:
            st.markdown(
                f"""
                <div class="stats-card">
                    <div style="font-size: 2rem;">⚡</div>
                    <h3>{(len(slide_files) + len(guide_files)) * 5}</h3>
                    <p>Minutes Saved</p>
                </div>
                """,
                unsafe_allow_html=True
            )
            
        with col4:
            plan_badge = "🟢 PRO" if is_pro_user() else "⚪ FREE"
            st.markdown(
                f"""
                <div class="stats-card">
                    <div style="font-size: 2rem;">🎯</div>
                    <h3>{plan_badge}</h3>
                    <p>Current Plan</p>
                </div>
                """,
                unsafe_allow_html=True
            )
    except:
        pass

# -------------------------
# Page: Upload
# -------------------------
def upload_page():
    st.markdown("## 📤 Upload Document")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        max_size_mb = get_max_upload_size() / (1024 * 1024)
        st.markdown(f"""
        **Supported Formats:**
        - 📄 **PDF Documents**: Lecture notes, research papers, articles
        - 📝 **Text Files**: TXT documents, markdown files
        
        **File size limit**: {max_size_mb}MB per file ({'Pro' if is_pro_user() else 'Free'} plan)
        """)
        
        # File uploader with custom styling
        up = st.file_uploader(
            "Drag and drop file here",
            type=["pdf", "txt"],
            label_visibility="collapsed",
            help=f"Upload your PDF or text documents (max {max_size_mb}MB)"
        )

        if up:
            # Check file size against plan limits
            if up.size > get_max_upload_size():
                max_size_mb = get_max_upload_size() / (1024 * 1024)
                file_size_mb = up.size / (1024 * 1024)
                st.error(f"❌ File too large! Your {max_size_mb}MB {'Pro' if is_pro_user() else 'Free'} plan limit exceeded. File size: {file_size_mb:.1f}MB")
                if not is_pro_user():
                    st.info("💡 Upgrade to SlideCraft Pro for 1GB file uploads!")
            else:
                username = st.session_state.username or "anonymous"
                safe_name = f"{username}_{up.name.replace(' ', '_')}"
                dest = DATA_IN / safe_name
                with open(dest, "wb") as f:
                    f.write(up.getbuffer())
                st.session_state.uploaded_path = dest
                
                st.markdown(
                    f"""
                    <div class="file-card">
                        <div style="display: flex; align-items: center; gap: 10px;">
                            <div style="font-size: 2rem;">📄</div>
                            <div>
                                <strong style="font-size: 1.1rem;">{up.name}</strong><br>
                                <span class="small-muted">Type: {up.type} | Size: {up.size / 1024 / 1024:.1f} MB</span>
                            </div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                st.success("✅ File uploaded successfully!")
    
    with col2:
        lottie_anim = load_lottie_url(LOTTIE_URLS["upload"])
        if lottie_anim and LOTTIE_AVAILABLE:
            st_lottie(lottie_anim, height=200, key="upload_anim")
        else:
            st.markdown('<div style="font-size: 6rem; text-align: center;">📤</div>', unsafe_allow_html=True)
        
        st.markdown("### Processing Options")
        
        # KB checkbox - disabled for free users
        if is_pro_user():
            st.checkbox("Use Knowledge Base (recommended)", value=st.session_state.use_kb, key="ui_use_kb")
            st.session_state.use_kb = st.session_state.get("ui_use_kb", True)
        else:
            st.checkbox("Use Knowledge Base (Pro feature)", value=False, key="ui_use_kb_disabled", disabled=True)
            st.session_state.use_kb = False
            st.info("💡 Knowledge Base requires SlideCraft Pro")

    st.markdown("---")
    
    start_disabled = not bool(st.session_state.uploaded_path)
    if st.button("🚀 Start Processing", disabled=start_disabled, use_container_width=True, type="primary"):
        st.session_state.run_pipeline = True
        st.session_state.page = "processing"
        st.session_state.pptx_bytes = None
        st.session_state.pdf_bytes = None
        st.session_state.processing_step = 0
        st.rerun()

# -------------------------
# Simple Progress Bar using Streamlit Native Components
# -------------------------
def render_progress_bar(current_step: int, total_steps: int, step_labels: list[str]):
    """Render progress using Streamlit's native components"""
    
    # Progress bar - ensure value is between 0 and 1
    progress = min((current_step + 1) / total_steps, 1.0)
    st.progress(progress)
    
    # Step indicators using columns
    cols = st.columns(total_steps)
    for i, label in enumerate(step_labels):
        with cols[i]:
            # Extract emoji and text
            parts = label.split(' ', 1)
            emoji = parts[0]
            text = parts[1] if len(parts) > 1 else label
            
            # Display step
            if i <= current_step:
                # Active step
                st.markdown(f"<div style='text-align: center; font-size: 1.5rem;'>{emoji}</div>", unsafe_allow_html=True)
                st.markdown(f"<div style='text-align: center; color: #1e40af; font-weight: bold;'>{text}</div>", unsafe_allow_html=True)
            else:
                # Inactive step
                st.markdown(f"<div style='text-align: center; font-size: 1.5rem; opacity: 0.5;'>{emoji}</div>", unsafe_allow_html=True)
                st.markdown(f"<div style='text-align: center; color: #94a3b8;'>{text}</div>", unsafe_allow_html=True)

# -------------------------
# Page: Processing
# -------------------------
def processing_page():
    st.markdown("## ⚙️ Processing")
    
    if not st.session_state.uploaded_path:
        st.error("❌ No uploaded file found. Please upload a file on the Upload page first.")
        if st.button("← Back to Upload", use_container_width=True, type="primary"):
            st.session_state.page = "upload"
        return

    path = st.session_state.uploaded_path
    steps = ["🧹 Cleaning", "🔍 Extracting", "🖼️ Slides", "📚 Guide", "✅ Done"]
    total_steps = len(steps)

    # Show file being processed
    kb_status = "Enabled" if (st.session_state.use_kb and is_pro_user()) else "Disabled"
    st.markdown(
        f"""
        <div class="file-card">
            <strong>Processing:</strong> {path.name}<br>
            <span class="small-muted">Knowledge Base: {kb_status}</span>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Create a single progress container
    progress_placeholder = st.empty()
    status_placeholder = st.empty()
    
    # Run pipeline (only once)
    if st.session_state.get("run_pipeline", False):
        try:
            # Initial progress
            with progress_placeholder.container():
                render_progress_bar(0, total_steps, steps)
            status_placeholder.info("🚀 Starting processing pipeline...")
            
            # Step 1: cleaning / transcription
            with st.spinner("🧹 Transcribing & cleaning content..."):
                cleaned, cleaned_path = transcribe_and_clean(str(path))
                st.session_state.processing_step = 1
                with progress_placeholder.container():
                    render_progress_bar(1, total_steps, steps)
                status_placeholder.success("✅ Content cleaned successfully")
                time.sleep(0.5)

            # Step 2: KB retrieval (optional - only for Pro users with KB enabled)
            kb_context = ""
            if st.session_state.get("use_kb", True) and is_pro_user():
                status_placeholder.info("🧠 Enhancing with knowledge base...")
                try:
                    kb_context = retrieve_context(cleaned, k=8)
                    if not kb_context:
                        kb_context = simple_retrieve_context(cleaned)
                except Exception:
                    kb_context = simple_retrieve_context(cleaned)
                st.session_state.processing_step = 2
                with progress_placeholder.container():
                    render_progress_bar(2, total_steps, steps)
                status_placeholder.success("✅ Knowledge base enhanced")
                time.sleep(0.5)
            else:
                # Skip KB step for free users or when KB is disabled
                st.session_state.processing_step = 2
                with progress_placeholder.container():
                    render_progress_bar(2, total_steps, steps)
                if not is_pro_user():
                    status_placeholder.info("ℹ️ Knowledge base skipped (Pro feature)")
                else:
                    status_placeholder.info("ℹ️ Knowledge base step skipped")
                time.sleep(0.5)

            # Step 3: keypoint extraction
            status_placeholder.info("🔍 Extracting key concepts and structure...")
            enhanced_content = cleaned
            if kb_context:
                enhanced_content = f"{cleaned}\n\nRelevant Context:\n{kb_context}"
            outline, outline_path = extract_outline(enhanced_content)
            st.session_state.processing_step = 3
            with progress_placeholder.container():
                render_progress_bar(3, total_steps, steps)
            status_placeholder.success("✅ Key concepts extracted")
            time.sleep(0.5)

            # Step 4: guide (PDF)
            pdf_bytes = None
            pdf_path = None
            status_placeholder.info("📚 Generating instructor guide...")
            if GUIDE_AVAILABLE:
                try:
                    lecture_metadata = {"title": Path(path).stem, "audience": "Students", "duration": "--"}
                    maybe_pdf_path = run_guide_agent(lecture_metadata=lecture_metadata, extracted_outline=outline, style="detailed")
                    if maybe_pdf_path and Path(maybe_pdf_path).exists():
                        dest = GUIDES_DIR / f"{st.session_state.username}_{Path(path).stem}_{int(time.time())}.pdf"
                        Path(maybe_pdf_path).replace(dest)
                        pdf_path = dest
                        with open(pdf_path, "rb") as f:
                            pdf_bytes = f.read()
                except Exception as e:
                    status_placeholder.warning(f"Guide generation skipped: {str(e)}")
            else:
                status_placeholder.info("Guide generator not available in this environment.")
            st.session_state.processing_step = 4
            with progress_placeholder.container():
                render_progress_bar(4, total_steps, steps)
            status_placeholder.success("✅ Guide generated")
            time.sleep(0.5)

            # Step 5: slides (PPTX)
            status_placeholder.info("🖼️ Creating professional slides...")
            pptx_bytes = None
            pptx_path = None
            maybe_pptx = outline_to_pptx(outline, filename_stem=Path(path).stem)
            if maybe_pptx and Path(maybe_pptx).exists():
                dest = SLIDES_DIR / f"{st.session_state.username}_{Path(path).stem}_{int(time.time())}.pptx"
                Path(maybe_pptx).replace(dest)
                pptx_path = dest
                with open(pptx_path, "rb") as f:
                    pptx_bytes = f.read()
            else:
                status_placeholder.error("Slide generation failed.")
            st.session_state.processing_step = 5
            with progress_placeholder.container():
                render_progress_bar(5, total_steps, steps)
            status_placeholder.success("✅ Slides created successfully")
            time.sleep(0.5)

            # Save to session state for Downloads
            st.session_state.pptx_bytes = pptx_bytes
            st.session_state.pdf_bytes = pdf_bytes
            st.session_state.pptx_path = str(pptx_path) if pptx_path else None
            st.session_state.pdf_path = str(pdf_path) if pdf_path else None

            # Final success message
            with progress_placeholder.container():
                render_progress_bar(5, total_steps, steps)
            status_placeholder.empty()
            lottie_anim = load_lottie_url(LOTTIE_URLS["success"])
            if lottie_anim and LOTTIE_AVAILABLE:
                st_lottie(lottie_anim, height=150, key="success_anim")
            st.success("🎉 Processing completed successfully!")

        except Exception as e:
            st.error(f"❌ Processing failed: {str(e)}")
        finally:
            st.session_state.run_pipeline = False
    else:
        # Show initial progress bar when not running
        render_progress_bar(st.session_state.processing_step, total_steps, steps)
        if st.session_state.processing_step == 0:
            st.info("👆 Click 'Start Processing' on the Upload page to begin")

    # Show downloads section
    st.markdown("---")
    st.markdown("## 📥 Download Results")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📊 Presentation Slides")
        if st.session_state.pptx_bytes and st.session_state.pptx_path:
            st.success("✅ Slides ready for download")
            st.markdown(f"**File:** `{Path(st.session_state.pptx_path).name}`")
            st.download_button(
                "📥 Download Slides (.pptx)", 
                data=st.session_state.pptx_bytes,
                file_name=Path(st.session_state.pptx_path).name, 
                use_container_width=True,
                type="primary"
            )
        else:
            st.info("📋 Slides will appear here after processing")
            
    with col2:
        st.markdown("### 📝 Instructor Guide")
        if st.session_state.pdf_bytes and st.session_state.pdf_path:
            st.success("✅ Guide ready for download")
            st.markdown(f"**File:** `{Path(st.session_state.pdf_path).name}`")
            st.download_button(
                "📥 Download Guide (.pdf)", 
                data=st.session_state.pdf_bytes,
                file_name=Path(st.session_state.pdf_path).name, 
                mime="application/pdf", 
                use_container_width=True,
                type="secondary"
            )
        else:
            st.info("📋 Guide will appear here if available")

# -------------------------
# Page: Outputs (organized file manager)
# -------------------------
def outputs_page():
    st.markdown("## 📁 Your Generated Files")
    
    # Build file lists
    slide_files = sorted(SLIDES_DIR.glob(f"*{st.session_state.username}*"), key=lambda p: p.stat().st_mtime, reverse=True)
    guide_files = sorted(GUIDES_DIR.glob(f"*{st.session_state.username}*"), key=lambda p: p.stat().st_mtime, reverse=True)

    # Stats
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(
            f"""
            <div class="stats-card">
                <div style="font-size: 1.5rem;">📊</div>
                <h3>{len(slide_files)}</h3>
                <p>Slide Decks</p>
            </div>
            """,
            unsafe_allow_html=True
        )
    with col2:
        st.markdown(
            f"""
            <div class="stats-card">
                <div style="font-size: 1.5rem;">📝</div>
                <h3>{len(guide_files)}</h3>
                <p>Instructor Guides</p>
            </div>
            """,
            unsafe_allow_html=True
        )
    with col3:
        total_size = sum(f.stat().st_size for f in slide_files + guide_files) / (1024 * 1024)
        st.markdown(
            f"""
            <div class="stats-card">
                <div style="font-size: 1.5rem;">💾</div>
                <h3>{total_size:.1f}</h3>
                <p>MB Storage</p>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown("---")
    
    # File lists
    tabs = st.tabs(["📊 Presentation Slides", "📝 Instructor Guides"])
    
    with tabs[0]:
        if slide_files:
            for file_path in slide_files:
                col1, col2, col3 = st.columns([4, 2, 1])
                with col1:
                    st.markdown(f"**{file_path.name}**")
                with col2:
                    st.markdown(f"*{time.strftime('%Y-%m-%d %H:%M', time.localtime(file_path.stat().st_mtime))}*")
                with col3:
                    with open(file_path, "rb") as f:
                        st.download_button(
                            "⬇️", 
                            data=f.read(), 
                            file_name=file_path.name,
                            use_container_width=True
                        )
        else:
            st.info("No slide files found. Process some documents to see them here!")
    
    with tabs[1]:
        if guide_files:
            for file_path in guide_files:
                col1, col2, col3 = st.columns([4, 2, 1])
                with col1:
                    st.markdown(f"**{file_path.name}**")
                with col2:
                    st.markdown(f"*{time.strftime('%Y-%m-%d %H:%M', time.localtime(file_path.stat().st_mtime))}*")
                with col3:
                    with open(file_path, "rb") as f:
                        st.download_button(
                            "⬇️", 
                            data=f.read(), 
                            file_name=file_path.name,
                            use_container_width=True
                        )
        else:
            st.info("No guide files found. Process some documents to see them here!")


# -------------------------
# Main App Logic
# -------------------------
if not st.session_state.authenticated:
    show_login_signup()
else:
    top_nav()
    
    if st.session_state.page == "account":
        account_page()
    elif st.session_state.page == "upload":
        upload_page()
    elif st.session_state.page == "processing":
        processing_page()
    elif st.session_state.page == "outputs":
        outputs_page()
    else:
        home_page()

    # Footer
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; color: #64748b; padding: 2rem;'>"
        "🎓 SlideCraft - AI-Powered Document Processing • "
        "Transform Your Teaching Materials • "
        "Built for Educators and Students"
        "</div>",
        unsafe_allow_html=True
    )