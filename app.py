from __future__ import annotations
import streamlit as st
from pathlib import Path
import time

# Agents
from agents.transcript_cleaner import transcribe_and_clean
from agents.keypoints_extractor import extract_outline
from agents.slide_generator import outline_to_pptx
from agents.retriever import retrieve_context  # ✅ KB retrieval

# Utils
from utils.fs import DATA_IN
from utils import auth

# Lottie
try:
    from streamlit_lottie import st_lottie
    import requests
    LOTTIE_AVAILABLE = True
except ImportError:
    LOTTIE_AVAILABLE = False

st.set_page_config(
    page_title="SlideCraft - Lecture Notes Processor", 
    layout="wide",
    page_icon="🎓"
)

# --------------------------
# SESSION STATE
# --------------------------
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "username" not in st.session_state:
    st.session_state.username = None
if "run_pipeline" not in st.session_state:
    st.session_state.run_pipeline = False

# --------------------------
# LOTTIE ANIMATIONS
# --------------------------
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
    "slides": "https://assets1.lottiefiles.com/packages/lf20_ukwybttx.json"
}

# --------------------------
# LOGIN / SIGNUP SCREEN (SPLIT SCREEN)
# --------------------------
if not st.session_state.authenticated:
    st.markdown(
    """
    <style>
    /* Remove default padding and margins */
    .main .block-container {
        padding: 0;
        max-width: 100%;
    }
    
    /* Split screen container */
    .split-screen {
        display: flex;
        height: 100vh;
    }
    
    /* Left side - Brand section */
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
    
    /* Right side - Login form */
    .form-side {
        flex: 1;
        display: flex;
        justify-content: center;
        align-items: center;
        padding: 2rem;
        background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
    }
    
    /* Login card styling */
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
    
    /* Brand logo and title */
    .brand-logo {
        font-size: 4.5rem;
        margin-bottom: 1.5rem;
        filter: drop-shadow(0 4px 12px rgba(30, 58, 138, 0.2));
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
    
    /* Feature list */
    .feature-list {
        text-align: left;
        max-width: 420px;
        margin: 0 auto;
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
    
    /* Form elements */
    .form-header {
        color: #1e40af;
        margin-bottom: 1.5rem;
        text-align: center;
        font-size: 1.8rem;
        font-weight: 600;
    }
    
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
    
    /* Tab buttons */
    .tab-buttons {
        display: flex;
        gap: 0.5rem;
        margin-bottom: 2rem;
        background: #f1f5f9;
        padding: 0.5rem;
        border-radius: 14px;
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
    </style>
    """,
    unsafe_allow_html=True,
    )

    # Split screen layout
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(
            """
            <div class="brand-side">
                <div class="brand-logo">📚</div>
                <h1 class="brand-title">SlideCraft</h1>
                <p class="brand-subtitle">
                    Transform your lecture notes and recordings into professional 
                    presentation slides with AI-powered processing.
                </p>
                <div class="feature-list">
                    <div class="feature-item">
                        <span class="feature-icon">🎤</span>
                        <span><strong>Audio Transcription</strong> - Convert lectures to text</span>
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
            
            
            # Tab selection
            if "login_tab" not in st.session_state:
                st.session_state.login_tab = "login"
            
            # Tab buttons
            col1, col2 = st.columns(2)
            with col1:
                if st.button(
                    "🔑 Login", 
                    use_container_width=True, 
                    key="login_tab_btn",
                    type="primary" if st.session_state.login_tab == "login" else "secondary"
                ):
                    st.session_state.login_tab = "login"
            with col2:
                if st.button(
                    "✨ Sign Up", 
                    use_container_width=True, 
                    key="signup_tab_btn",
                    type="primary" if st.session_state.login_tab == "signup" else "secondary"
                ):
                    st.session_state.login_tab = "signup"
            
            # Animation
            st.markdown('<div style="text-align: center; margin: 1.5rem 0;">', unsafe_allow_html=True)
            if st.session_state.login_tab == "login":
                lottie_anim = load_lottie_url(LOTTIE_URLS["lecture"])
                if lottie_anim and LOTTIE_AVAILABLE:
                    st_lottie(lottie_anim, height=120, key="login_anim")
                else:
                    st.markdown('<div style="font-size: 4rem;">🎓</div>', unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)
                st.markdown('<h2 class="form-header">Welcome Back</h2>', unsafe_allow_html=True)
            else:
                lottie_anim = load_lottie_url(LOTTIE_URLS["notes"])
                if lottie_anim and LOTTIE_AVAILABLE:
                    st_lottie(lottie_anim, height=120, key="signup_anim")
                else:
                    st.markdown('<div style="font-size: 4rem;">📝</div>', unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)
                st.markdown('<h2 class="form-header">Create Account</h2>', unsafe_allow_html=True)
            
            # Login/Signup forms
            if st.session_state.login_tab == "login":
                uname = st.text_input("👤 Username", key="login_user", placeholder="Enter your username")
                pwd = st.text_input("🔒 Password", type="password", key="login_pass", placeholder="Enter your password")
                
                if st.button("Access SlideCraft", use_container_width=True, type="primary"):
                    if auth.login(uname, pwd):
                        st.session_state.authenticated = True
                        st.session_state.username = uname
                        st.success(f"🎉 Welcome back, {uname}!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("❌ Invalid credentials")
            else:
                uname_new = st.text_input("👤 Choose Username", key="signup_user", placeholder="Create a username")
                pwd_new = st.text_input("🔒 Create Password", type="password", key="signup_pass", placeholder="Choose a secure password")
                
                if st.button("Start Creating Slides", use_container_width=True, type="primary"):
                    if auth.signup(uname_new, pwd_new):
                        st.success("✅ Account created! Please log in.")
                        st.session_state.login_tab = "login"
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("⚠️ Username already exists")
            
            st.markdown("</div>", unsafe_allow_html=True)  # Close login-card
        st.markdown("</div>", unsafe_allow_html=True)  # Close form-side
    
    st.stop()

# --------------------------
# MAIN APPLICATION
# --------------------------

# Custom CSS for main app
st.markdown(
    """
    <style>
    .main-header {
        background: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-size: 2.8rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }
    .pipeline-steps {
        display: flex;
        justify-content: space-between;
        margin: 1rem 0 2rem 0;
        padding: 1rem;
        background: #f8fafc;
        border-radius: 12px;
        border-left: 4px solid #3b82f6;
    }
    .step {
        text-align: center;
        flex: 1;
        padding: 0.5rem;
    }
    .step-icon {
        font-size: 2rem;
        margin-bottom: 0.5rem;
    }
    .step-active {
        color: #1e40af;
        font-weight: 600;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Header
col1, col2 = st.columns([4, 1])
with col1:
    st.markdown('<h1 class="main-header">🎓 SlideCraft - Lecture Notes Processor</h1>', unsafe_allow_html=True)
    st.caption("AI-powered pipeline to transform your lecture materials into professional presentations")
    st.write(f"👤 **Welcome, {st.session_state.username}**")

with col2:
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state.authenticated = False
        st.session_state.username = None
        st.rerun()

# Pipeline Steps
st.markdown(
    """
    <div class="pipeline-steps">
        <div class="step">
            <div class="step-icon">📚</div>
            <div>1. Upload Materials</div>
        </div>
        <div class="step">
            <div class="step-icon">🧠</div>
            <div>2. AI Processing</div>
        </div>
        <div class="step">
            <div class="step-icon">📊</div>
            <div>3. Get Slides</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

# Sidebar - File Management
with st.sidebar:
    st.markdown("### 🗂️ File Management")
    
    st.markdown(
        """
        **Important:** All uploaded content will be automatically deleted after 24 hours, ensuring your privacy. 
        Your materials will not be used for any data collection purposes.
        """,
        unsafe_allow_html=True
)

    
    # File Upload
    st.subheader("📚 Upload New Material")
    up = st.file_uploader(
        "Select lecture file",
        type=["mp3", "wav", "m4a", "mp4", "mov", "pdf", "txt", "md"],
        label_visibility="collapsed",
        help="Supported: Audio recordings, PDF notes, text files"
    )
    st.markdown("**File size limit**: 200MB per file. **Supported file types**: MP3, WAV, PDF, TXT")

    uploaded_path = None
    if up:
        safe_name = f"{st.session_state.username}_{up.name.replace(' ', '_')}"
        dest = DATA_IN / safe_name
        with open(dest, "wb") as f:
            f.write(up.getbuffer())
        uploaded_path = dest
        st.success(f"✅ **{up.name}** uploaded successfully!")
    
    st.markdown("---")
    
    # Existing Files
    st.subheader("🗃️ Existing Materials")
    choices = [p.name for p in DATA_IN.glob(f"{st.session_state.username}_*") if p.is_file()]
    if choices:
        choice = st.selectbox("Select existing file", ["—"] + choices, label_visibility="collapsed")
    else:
        st.info("📝 No files uploaded yet")
        choice = "—"
    
    
    st.markdown("---")
    
    # KB Integration Toggle
    st.markdown("### 🧠 AI Enhancement")
    use_kb = st.checkbox(
        "Use Knowledge Base for better content", 
        value=True,
        help="Leverage existing course materials to enhance slide quality"
    )
    
    st.markdown("---")
    
    # Process Button
    if st.button("🚀 Process Lecture Notes", type="primary", use_container_width=True):
        st.session_state.run_pipeline = True
        st.session_state.use_kb = use_kb

    st.markdown("---")

    # Old Generated Slides Section
    st.subheader("📜 Old Generated Slides")

    slides_dir = Path("outputs/slides")
    old_slides = [p.name for p in slides_dir.glob(f"{st.session_state.username}_*.pptx") if p.is_file()]

    if old_slides:
        selected_slide = st.selectbox("Select slide file", ["—"] + old_slides, label_visibility="collapsed")
        if selected_slide != "—":
            slide_path = slides_dir / selected_slide
            with open(slide_path, "rb") as f:
                st.download_button(
                    "⬇️ Download Selected Slide",
                    data=f.read(),
                    file_name=selected_slide,
                    use_container_width=True,
                    type="primary"
                )
    else:
        st.info("📂 No previously generated slides found")
    

# --------------------------
# PROCESSING PIPELINE
# --------------------------
if st.session_state.get('run_pipeline', False):
    path = uploaded_path or (DATA_IN / choice if choice and choice != "—" else None)

    if path and path.exists():
        # Initialize progress
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            # Step 1: Transcription & Cleaning
            with st.spinner("🎤 Transcribing lecture content..."):
                status_text.text("Step 1/4: Transcribing audio/text content...")
                cleaned, cleaned_path = transcribe_and_clean(str(path))
                progress_bar.progress(25)
                time.sleep(0.5)
            
            # # Step 2: Knowledge Base Retrieval (if enabled)
            # kb_context = ""
            # if st.session_state.get('use_kb', True):
            #     with st.spinner("🧠 Retrieving relevant knowledge..."):
            #         status_text.text("Step 2/4: Enhancing with knowledge base...")
            #         try:
            #             kb_context = retrieve_context(cleaned)
            #             st.info(f"📚 Retrieved {len(kb_context.split())} words of relevant context")
            #         except Exception as kb_error:
            #             st.warning(f"⚠️ Knowledge base retrieval skipped: {str(kb_error)}")
            #             kb_context = ""
            #     progress_bar.progress(50)
            #     time.sleep(0.5)
            # else:
            #     progress_bar.progress(50)  # Skip directly to next step

            # Step 2: Knowledge Base Retrieval (if enabled)
            kb_context = ""
            if st.session_state.get('use_kb', True):
                with st.spinner("🧠 Retrieving relevant knowledge..."):
                    status_text.text("Step 2/4: Enhancing with knowledge base...")
                    try:
                        # Try main retriever first
                        kb_context = retrieve_context(cleaned)
                        if "error" in kb_context.lower() or "not available" in kb_context.lower():
                            st.warning("Using simple retrieval mode")
                            from agents.retriever import simple_retrieve_context
                            kb_context = simple_retrieve_context(cleaned)
                    except Exception as kb_error:
                        st.warning(f"⚠️ Knowledge base retrieval failed: {str(kb_error)}")
                        # Use simple fallback
                        from agents.retriever import simple_retrieve_context
                        kb_context = simple_retrieve_context(cleaned)    

                
            
            # Step 3: Key Points Extraction (with KB context if available)
            with st.spinner("🔍 Extracting key concepts..."):
                status_text.text("Step 3/4: Analyzing content structure...")
                
                # Combine cleaned text with KB context for better extraction
                enhanced_content = cleaned
                if kb_context:
                    enhanced_content = f"{cleaned}\n\nRelevant Context:\n{kb_context}"
                
                outline, outline_path = extract_outline(enhanced_content)
                progress_bar.progress(75)
                time.sleep(0.5)
            
            # Step 4: Slide Generation
            with st.spinner("📊 Creating presentation slides..."):
                status_text.text("Step 4/4: Generating professional slides...")
                pptx_path = outline_to_pptx(outline, filename_stem=Path(path).stem)
                progress_bar.progress(100)
                time.sleep(0.5)
            
            # Success Message
            status_text.success("✅ Lecture processed successfully! Download your presentation below.")
            
            # Show KB usage status
            if st.session_state.get('use_kb', True) and kb_context:
                st.success("🎯 Knowledge Base was used to enhance content quality")
            elif not st.session_state.get('use_kb', True):
                st.info("ℹ️ Knowledge Base was disabled for this processing")
            
            # Success Animation
            if LOTTIE_AVAILABLE:
                success_anim = load_lottie_url(LOTTIE_URLS["success"])
                if success_anim:
                    st_lottie(success_anim, height=150, key="success_anim")
            
        except Exception as e:
            status_text.error(f"❌ Processing error: {str(e)}")
            st.stop()

        # Results Display
        st.markdown("---")
        st.markdown("## 📋 Processing Results")
        
        tab1, tab2, tab3, tab4 = st.tabs(["🎯 Cleaned Content", "📚 KB Context", "📑 Structured Outline", "🎞 Presentation Slides"])
        
        with tab1:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.subheader("Cleaned Lecture Content")
                st.info("✅ Transcription and formatting completed")
            with col2:
                st.download_button(
                    "📥 Download Text",
                    data=cleaned,
                    file_name=f"lecture_content_{Path(path).stem}.txt",
                    use_container_width=True
                )
            
            with st.expander("View cleaned content", expanded=False):
                st.text_area("Content", cleaned, height=300, label_visibility="collapsed")
        
        with tab2:
            if kb_context:
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.subheader("Knowledge Base Context")
                    st.success("✅ Enhanced with relevant course materials")
                with col2:
                    st.download_button(
                        "📥 Download Context",
                        data=kb_context,
                        file_name=f"kb_context_{Path(path).stem}.txt",
                        use_container_width=True
                    )
                
                with st.expander("View KB context", expanded=False):
                    st.text_area("Knowledge Base Content", kb_context, height=200, label_visibility="collapsed")
            else:
                st.info("ℹ️ No knowledge base context was used or available for this content")
        
        with tab3:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.subheader("Content Structure Analysis")
                st.info("✅ Key points and hierarchy identified")
            with col2:
                st.download_button(
                    "📥 Download Outline",
                    data=outline.model_dump_json(indent=2),
                    file_name=f"lecture_outline_{Path(path).stem}.json",
                    use_container_width=True
                )
            
            with st.expander("View content structure", expanded=False):
                st.json(outline.model_dump())
        
        with tab4:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.subheader("Generated Presentation")
                st.success("🎉 Professional slides ready for your lecture!")
                st.markdown(f"**File:** `{Path(pptx_path).name}`")
                if kb_context:
                    st.caption("✅ Enhanced with knowledge base content")
            with col2:
                with open(pptx_path, "rb") as f:
                    st.download_button(
                        "⬇️ Download PowerPoint",
                        data=f.read(),
                        file_name=Path(pptx_path).name,
                        use_container_width=True,
                        type="primary"
                    )
            
            st.markdown("### 🎨 Slide Preview Features")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown("**📚 Academic Design**")
                st.markdown("Professional templates optimized for education")
            with col2:
                st.markdown("**⚡ Smart Layout**")
                st.markdown("Content automatically structured for clarity")
            with col3:
                st.markdown("**🎯 Key Points**")
                st.markdown("Important concepts highlighted effectively")
                
    else:
        st.error("⚠️ Please upload or select a lecture file first.")
    
    st.session_state.run_pipeline = False

# --------------------------
# FEATURES & INFORMATION
# --------------------------
if not st.session_state.get('run_pipeline', False):
    st.markdown("---")
    st.markdown("## 🚀 How It Works")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("### 1. Upload Materials")
        st.markdown("""
        - **Audio Recordings**: Lectures, seminars, podcasts
        - **PDF Documents**: Notes, research papers, articles  
        - **Text Files**: Transcripts, written notes, summaries
        - **Automatic Processing**: AI detects content type
        """)
    
    with col2:
        st.markdown("### 2. Knowledge Enhancement")
        st.markdown("""
        - **Smart Retrieval**: Finds relevant course materials
        - **Context Enrichment**: Enhances with existing knowledge
        - **Quality Boost**: Improves content accuracy
        - **Optional Feature**: Can be toggled on/off
        """)
    
    with col3:
        st.markdown("### 3. AI Analysis")
        st.markdown("""
        - **Smart Transcription**: Convert audio to text
        - **Content Cleaning**: Remove filler words, errors
        - **Key Point Extraction**: Identify main concepts
        - **Structure Detection**: Organize content logically
        """)
    
    with col4:
        st.markdown("### 4. Presentation Ready")
        st.markdown("""
        - **Professional Slides**: Academic templates
        - **Editable Format**: PowerPoint (.pptx) files
        - **Content Optimized**: Perfect for lectures
        - **Download & Present**: Ready to use immediately
        """)

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #64748b; padding: 2rem;'>"
    "🎓 **SlideCraft** - Transforming Lecture Notes into Professional Presentations • "
    "Enhanced with Knowledge Base AI • Perfect for Educators, Students, and Researchers"
    "</div>",
    unsafe_allow_html=True
)