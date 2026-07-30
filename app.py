import os
import json
import streamlit as st
from dotenv import load_dotenv
from pypdf import PdfReader

# Load environment variables from .env
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="ResuFit — AI Resume Optimizer & Match Evaluator",
    page_icon="🖋️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for modern dark luxury visual design & glassmorphism
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Source+Serif+4:opsz,wght@8..60,400;8..60,600;8..60,700&family=Inter:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500;600;700&display=swap');

    /*
      DESIGN CONCEPT — "The Review Desk"
      This tool simulates a human reviewer + an automated ATS bot marking up
      a resume side by side. Palette and type are chosen to embody that:
        - warm paper backdrop + manila-folder cards, like a document on a desk
        - ink-navy for the reviewer's own writing / structure
        - stamp-green for "approved / matched", pen-red for "flagged / missing",
          gold for "needs verification" — literal reviewer marks, not decoration
        - Source Serif 4 for anything representing YOUR words (headings, CV text)
        - IBM Plex Mono for anything representing the MACHINE's read
          (scores, keyword tags, status lines) — the two faces make it visually
          obvious which parts are human-authored vs. mechanically evaluated
    */

    :root {
        --paper: #f2ede1;
        --paper-deep: #e8e0cd;
        --folder: #ece4d1;
        --folder-edge: #d8cbac;
        --ink: #23201b;
        --ink-soft: #5b5646;
        --stamp-green: #0f6e4f;
        --stamp-green-bg: rgba(15, 110, 79, 0.1);
        --pen-red: #9c2b2b;
        --pen-red-bg: rgba(156, 43, 43, 0.09);
        --gold: #96700a;
        --gold-bg: rgba(150, 112, 10, 0.12);
        --ballpoint: #2c4159;
    }

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    h1, h2, h3, .header-title, .stamp-value {
        font-family: 'Source Serif 4', serif;
    }

    .stApp {
        background-color: var(--paper);
        background-image:
            repeating-linear-gradient(0deg, rgba(35,32,27,0.015) 0px, rgba(35,32,27,0.015) 1px, transparent 1px, transparent 3px),
            radial-gradient(at 15% 0%, rgba(15,110,79,0.05) 0px, transparent 55%);
        color: var(--ink);
    }

    section[data-testid="stSidebar"] {
        background-color: var(--folder);
        border-right: 1px solid var(--folder-edge);
    }
    section[data-testid="stSidebar"] * {
        color: var(--ink) !important;
    }

    /* Letterhead Header */
    .header-box {
        background: var(--paper);
        padding: 2rem 2.4rem;
        border-radius: 4px;
        margin-bottom: 2rem;
        border: 1px solid var(--folder-edge);
        border-top: 4px solid var(--ink);
        position: relative;
    }

    .header-eyebrow {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        font-family: 'IBM Plex Mono', monospace;
        background: transparent;
        border: 1px solid var(--ink-soft);
        color: var(--ink-soft);
        font-size: 0.72rem;
        font-weight: 600;
        padding: 0.25rem 0.7rem;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        margin-bottom: 1rem;
    }

    .header-title {
        font-size: 2.3rem;
        font-weight: 700;
        color: var(--ink);
        letter-spacing: -0.01em;
        margin-bottom: 0.6rem;
    }

    .header-subtitle {
        font-size: 1rem;
        color: var(--ink-soft);
        max-width: 780px;
        line-height: 1.65;
    }

    /* Folder-tab cards for content blocks */
    .glass-card {
        background: var(--folder);
        border: 1px solid var(--folder-edge);
        border-radius: 4px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
    }

    /* Score "Stamp" Cards — the signature element: each score reads like an
       ink stamp on a reviewed document, not a generic dashboard tile. */
    .stamp-card {
        background: var(--paper);
        border: 1.5px solid var(--ink);
        border-radius: 3px;
        padding: 1.3rem 1.2rem;
        text-align: center;
        position: relative;
    }

    .stamp-card::before {
        content: "";
        position: absolute;
        inset: 5px;
        border: 1px dashed var(--folder-edge);
        border-radius: 2px;
        pointer-events: none;
    }

    .stamp-label {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 0.7rem;
        color: var(--ink-soft);
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.09em;
    }

    .stamp-value {
        font-size: 2.6rem;
        font-weight: 700;
        line-height: 1;
        margin: 0.55rem 0 0.3rem 0;
    }

    .stamp-value.before { color: var(--pen-red); }
    .stamp-value.after { color: var(--stamp-green); }

    .stamp-caption {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 0.7rem;
        color: var(--ink-soft);
    }

    .stamp-verdict {
        display: inline-block;
        margin-top: 0.6rem;
        font-family: 'IBM Plex Mono', monospace;
        font-size: 0.68rem;
        font-weight: 700;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        padding: 0.2rem 0.6rem;
        border: 1.5px solid currentColor;
        border-radius: 2px;
        transform: rotate(-2deg);
    }

    /* Keyword tags — styled like circled/underlined words on a marked-up page */
    .keyword-badge {
        display: inline-block;
        font-family: 'IBM Plex Mono', monospace;
        background: var(--pen-red-bg);
        color: var(--pen-red);
        border: 1px solid var(--pen-red);
        border-radius: 3px;
        padding: 0.28rem 0.6rem;
        font-size: 0.78rem;
        font-weight: 600;
        margin: 0.25rem 0.3rem 0.25rem 0;
    }

    .keyword-badge.matched {
        background: var(--stamp-green-bg);
        color: var(--stamp-green);
        border-color: var(--stamp-green);
    }

    /* Bullet transformation cards */
    .bullet-card {
        background: var(--paper);
        border: 1px solid var(--folder-edge);
        border-left: 3px solid var(--ballpoint);
        border-radius: 3px;
        padding: 1.3rem 1.4rem;
        margin-bottom: 1.1rem;
    }

    .before-text {
        color: var(--ink-soft);
        text-decoration: line-through;
        text-decoration-color: var(--pen-red);
        margin-bottom: 0.55rem;
        font-size: 0.94rem;
        line-height: 1.55;
        font-family: 'Source Serif 4', serif;
    }

    .after-text {
        color: var(--ink);
        font-weight: 500;
        font-size: 1rem;
        line-height: 1.55;
        font-family: 'Source Serif 4', serif;
        border-left: 2px solid var(--stamp-green);
        padding-left: 0.7rem;
    }

    .pattern-tag {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 0.68rem;
        font-weight: 600;
        background: transparent;
        color: var(--ballpoint);
        border: 1px solid var(--ballpoint);
        padding: 0.2rem 0.55rem;
        border-radius: 2px;
        float: right;
        text-transform: uppercase;
        letter-spacing: 0.06em;
    }

    /* Elevator Pitch — styled as a typed index card */
    .pitch-card {
        background: var(--paper);
        border: 1px solid var(--folder-edge);
        border-left: 4px solid var(--ink);
        border-radius: 3px;
        padding: 1.6rem 1.8rem;
        margin-top: 1rem;
        font-family: 'Source Serif 4', serif;
    }

    /* Input styling */
    .stTextArea textarea {
        background-color: var(--paper) !important;
        color: var(--ink) !important;
        border-radius: 4px !important;
        border: 1px solid var(--folder-edge) !important;
        font-family: 'Source Serif 4', serif !important;
    }

    .stTextArea textarea:focus {
        border-color: var(--ink) !important;
        box-shadow: 0 0 0 1px var(--ink) !important;
    }

    .stTextInput input {
        background-color: var(--paper) !important;
        color: var(--ink) !important;
        border-radius: 4px !important;
        border: 1px solid var(--folder-edge) !important;
    }

    /* Folder-tab styled tabs — literal to the metaphor: your CV is a folder
       with labeled tabs for each kind of review. */
    .stTabs [data-baseweb="tab-list"] {
        gap: 4px;
        background-color: transparent;
        padding: 0;
        border-bottom: 1.5px solid var(--ink);
    }

    .stTabs [data-baseweb="tab"] {
        height: 42px;
        border-radius: 4px 4px 0 0;
        background: var(--folder);
        border: 1px solid var(--folder-edge);
        border-bottom: none;
        color: var(--ink);
        font-family: 'IBM Plex Mono', monospace;
        font-weight: 700;
        font-size: 0.82rem;
        padding: 0 16px;
    }

    .stTabs [aria-selected="true"] {
        background-color: var(--paper) !important;
        color: #000000 !important;
        border-color: var(--ink) !important;
        border-bottom: 1.5px solid var(--paper) !important;
        margin-bottom: -1.5px;
    }

    /* Primary Action Button — a "submit for review" stamp button */
    div.stButton > button[kind="primary"] {
        background: var(--ink);
        color: var(--paper);
        font-family: 'IBM Plex Mono', monospace;
        font-weight: 600;
        font-size: 0.95rem;
        letter-spacing: 0.03em;
        padding: 0.75rem 1.5rem;
        border-radius: 3px;
        border: none;
        text-transform: uppercase;
        transition: all 0.15s ease;
    }

    div.stButton > button[kind="primary"]:hover {
        background: var(--stamp-green);
        transform: translateY(-1px);
    }

    div.stButton > button:not([kind="primary"]) {
        background: var(--paper);
        color: var(--ink);
        border: 1px solid var(--folder-edge);
        border-radius: 3px;
    }

    /* Warning banner box — a gold sticky-note flag */
    .warning-box {
        background: var(--gold-bg);
        border: 1px solid var(--gold);
        border-left: 3px solid var(--gold);
        color: #6b5108;
        padding: 0.8rem 1.2rem;
        border-radius: 3px;
        font-size: 0.88rem;
        margin-top: 0.5rem;
        line-height: 1.5;
    }

    /* Critical failure banner box — red-pen correction flag */
    .fail-box {
        background: var(--pen-red-bg);
        border: 1px solid var(--pen-red);
        border-left: 3px solid var(--pen-red);
        color: #6e1f1f;
        padding: 0.8rem 1.2rem;
        border-radius: 3px;
        font-size: 0.88rem;
        margin-top: 0.5rem;
        margin-bottom: 1rem;
        line-height: 1.5;
    }

    /* Streamlit native alerts, expanders, download button — brought in line */
    div[data-testid="stAlert"] {
        border-radius: 3px;
        font-family: 'Inter', sans-serif;
    }

    .stDownloadButton button {
        background: var(--paper) !important;
        color: var(--ink) !important;
        border: 1.5px solid var(--ink) !important;
        border-radius: 3px !important;
        font-family: 'IBM Plex Mono', monospace !important;
        font-weight: 600 !important;
    }

    .stDownloadButton button:hover {
        background: var(--ink) !important;
        color: var(--paper) !important;
    }

    div[data-testid="stExpander"] {
        border: 1px solid var(--folder-edge) !important;
        border-radius: 3px !important;
        background: var(--folder) !important;
    }

    .stProgress > div > div > div {
        background-color: var(--stamp-green) !important;
    }

    hr {
        border-color: var(--folder-edge) !important;
    }

    /* ---- Legibility fixes ----
       Streamlit's own widget chrome (button labels, alert text, captions,
       expander headers, form labels) carries its own default text color
       baked into Streamlit's base styles, which does NOT automatically
       inherit the app-level color we set on .stApp — inheritance only
       applies where nothing more specific already set a color. These rules
       force our ink/paper palette onto that native chrome explicitly. */
    div[data-testid="stAlert"] p,
    div[data-testid="stAlert"] span,
    div[data-testid="stAlert"] div,
    div[data-testid="stCaptionContainer"],
    div[data-testid="stCaptionContainer"] p,
    [data-testid="stWidgetLabel"] p,
    [data-testid="stWidgetLabel"] label,
    [data-testid="stExpander"] p,
    [data-testid="stExpander"] summary,
    [data-testid="stExpander"] span,
    [data-testid="stExpander"] div,
    .stMarkdown p, .stMarkdown li, .stMarkdown span,
    label, .stCaption {
        color: var(--ink) !important;
    }

    /* Button label text sits in a nested <p>/<div> that can carry its own
       color independent of the button's own color rule — force it to
       match each button's intended contrast so labels never render
       ink-on-ink or paper-on-paper. */
    div.stButton > button[kind="primary"] p,
    div.stButton > button[kind="primary"] div {
        color: var(--paper) !important;
    }
    div.stButton > button:not([kind="primary"]) p,
    div.stButton > button:not([kind="primary"]) div,
    .stDownloadButton button p,
    .stDownloadButton button div {
        color: var(--ink) !important;
    }

    /* Our own accent-colored components must win over the broader fixes
       above — reassert them with !important so badges/tags/stamps keep
       their intentional reviewer-ink colors instead of collapsing to
       plain --ink like everything else. */
    .keyword-badge { color: var(--pen-red) !important; }
    .keyword-badge.matched { color: var(--stamp-green) !important; }
    .pattern-tag { color: var(--ballpoint) !important; }
    .stamp-value.before { color: var(--pen-red) !important; }
    .stamp-value.after { color: var(--stamp-green) !important; }
    .header-eyebrow { color: var(--ink-soft) !important; }
    .stamp-label, .stamp-caption { color: var(--ink-soft) !important; }
    .before-text { color: var(--ink-soft) !important; }
    /* File uploader — Streamlit's default dropzone ships with its own
       accent color scheme that clashed with the paper palette. */
    [data-testid="stFileUploaderDropzone"] {
        background: var(--folder) !important;
        border: 1.5px dashed var(--folder-edge) !important;
        border-radius: 4px !important;
    }
    [data-testid="stFileUploaderDropzone"] div,
    [data-testid="stFileUploaderDropzone"] span,
    [data-testid="stFileUploaderDropzone"] small,
    [data-testid="stFileUploaderDropzone"] p {
        color: var(--ink-soft) !important;
    }
    [data-testid="stFileUploaderDropzone"] button {
        background: var(--paper) !important;
        color: var(--ink) !important;
        border: 1px solid var(--ink) !important;
    }
    [data-testid="stFileUploaderDropzone"] button p {
        color: var(--ink) !important;
    }
    [data-testid="stFileUploaderFile"] {
        background: var(--paper) !important;
        color: var(--ink) !important;
    }
    [data-testid="stFileUploaderFile"] span,
    [data-testid="stFileUploaderFile"] small {
        color: var(--ink) !important;
    }

    /* Tab labels — use a broad descendant selector since the exact nested
       element Streamlit renders (p, div, or span depending on version)
       isn't guaranteed, and the earlier narrower rule missed it. */
    .stTabs [data-baseweb="tab"] * {
        color: var(--ink) !important;
        font-family: 'IBM Plex Mono', monospace;
        font-weight: 700;
    }
    .stTabs [aria-selected="true"] * {
        color: #000000 !important;
    }

    /* Streamlit's baseweb tab component ships its own red "active tab"
       highlight bar (#FF4B4B, Streamlit's default theme accent) that
       renders underneath the tab list regardless of our other overrides —
       it needs to be targeted directly or it shows through as a stray
       red mark next to the selected tab. */
    .stTabs [data-baseweb="tab-highlight"],
    .stTabs [data-baseweb="tab-border"] {
        background-color: var(--ink) !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# App Header Banner
st.markdown(
    """
    <div class="header-box">
        <span class="header-eyebrow">⌘ TF-IDF Coverage Score + LLM Rewrite</span>
        <div class="header-title">ResuFit</div>
        <div class="header-subtitle">
            An automated first read of your resume, the way an ATS bot and a hiring reviewer would take it:
            transparent keyword-coverage scoring, a full rewrite pass, and a numeric-hallucination audit —
            run on a remote Kaggle GPU.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# Sidebar Configuration
with st.sidebar:
    st.markdown("### ⚙️ Engine Settings")
    
    ngrok_url = st.text_input(
        "🌐 Ngrok Public URL",
        value=os.environ.get("NGROK_URL", ""),
        placeholder="https://xxxx.ngrok-free.app",
        help="Paste the active public Ngrok endpoint URL running on Kaggle GPU.",
    )
    
    ngrok_api_key = st.text_input(
        "🔑 Ngrok API Key",
        type="password",
        value=os.environ.get("NGROK_API_KEY", "secret123"),
        help="Authorization key configured in your Kaggle FastAPI backend.",
    )

    st.markdown("---")
    st.markdown("### 💡 Technical Overview")
    with st.expander("📊 How is the ATS Score calculated?"):
        st.markdown(
            "Uses **TF-IDF (Term Frequency-Inverse Document Frequency)** with compound words & n-grams "
            "to extract top high-weight job keywords and calculate exact keyword coverage over the candidate's entire CV."
        )
    with st.expander("🛡️ Hallucination Defense"):
        st.markdown(
            "Performs post-generation regex metric verification (`extract_numbers`). "
            "Any percentage or dollar metric introduced by the LLM that wasn't in the original text is flagged."
        )


# Helper function to extract text from PDF files
def extract_text_from_pdf(pdf_file) -> str:
    """Extracts plain text from an uploaded PDF file stream using pypdf."""
    reader = PdfReader(pdf_file)
    extracted_pages = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            extracted_pages.append(text)
    return "\n".join(extracted_pages)


# PDF upload — placed above the two-column layout (not inside the CV
# column) so both the CV and JD columns start at the same vertical
# position instead of the CV column being taller because of the uploader.
st.markdown("### Upload CV (optional)")
uploaded_pdf = st.file_uploader(
    "Upload CV as PDF to auto-extract text below",
    type=["pdf"],
    help="Upload your CV as a PDF file to extract text automatically",
    key="pdf_uploader",
    label_visibility="collapsed",
)

if uploaded_pdf is not None:
    try:
        pdf_text = extract_text_from_pdf(uploaded_pdf)
        if pdf_text.strip():
            st.session_state["cv_input"] = pdf_text
            st.toast(f"Extracted text from {uploaded_pdf.name}", icon="📄")
        else:
            st.warning("Could not extract text from PDF (file might be scanned or image-only).")
    except Exception as e:
        st.error(f"Failed to parse PDF: {e}")

st.write("")

# Input Columns Layout — both columns share the same structure (heading,
# one Clear button, equal-height text area) so they stay visually aligned.
col1, col2 = st.columns(2)

with col1:
    st.markdown("### Candidate Resume / CV")
    if st.button("Clear CV"):
        st.session_state["cv_input"] = ""

    cv_text = st.text_area(
        "CV Text Content:",
        value=st.session_state.get("cv_input", ""),
        height=280,
        placeholder="Upload a PDF above or paste candidate CV text here...",
    )

with col2:
    st.markdown("### Target Job Description")
    if st.button("Clear JD"):
        st.session_state["jd_input"] = ""

    jd_text = st.text_area(
        "Job Description Text Content:",
        value=st.session_state.get("jd_input", ""),
        height=280,
        placeholder="e.g. Looking for a Data Analyst proficient in SQL, Python, Docker, PowerBI...",
    )

st.write("")

# Run Pipeline Action
run_btn = st.button("🚀 Evaluate & Optimize Full CV", type="primary", use_container_width=True)

if run_btn:
    if not cv_text.strip() or not jd_text.strip():
        st.warning("⚠️ Please provide both Candidate CV text and Job Description.")
    else:
        # Clear any stale results from a previous run BEFORE attempting the
        # new one. Without this, a failed/erroring run leaves the last
        # successful run's results sitting in session_state, which then
        # keeps rendering below on every subsequent script rerun — making
        # a silently-failing new run look identical to the last real one.
        st.session_state.pop("pipeline_results", None)

        with st.spinner("🤖 Calculating ATS match & generating full optimized CV via Kaggle GPU..."):
            try:
                from chain import run_pipeline
                results = run_pipeline(
                    cv_text=cv_text,
                    job_description=jd_text,
                    ngrok_url=ngrok_url.strip() if ngrok_url.strip() else None,
                    api_key=ngrok_api_key.strip() if ngrok_api_key.strip() else None,
                )
                st.session_state["pipeline_results"] = results
            except Exception as err:
                st.markdown(
                    f'<div class="fail-box">❌ <b>Pipeline Execution Error:</b> {err}<br>'
                    f'No results are shown below because the run failed — this is NOT a cached '
                    f'or stale result.</div>',
                    unsafe_allow_html=True,
                )
                st.stop()

        st.success("Review complete — results below.")

# Results Dashboard
if "pipeline_results" in st.session_state:
    results = st.session_state["pipeline_results"]
    st.markdown("---")

    # Surface pipeline diagnostics prominently, before the pretty dashboard,
    # so a failed/degraded generation is never mistaken for a real result.
    status = results.get("optimization_status")
    if status:
        if status.get("used_original_cv_fallback"):
            st.markdown(
                f"""
                <div class="fail-box">
                    ⚠️ <b>Optimization did not apply — showing your ORIGINAL CV unchanged.</b><br>
                    The AI model's response could not be turned into a usable rewritten CV
                    (parse strategy attempted: <b>{status.get('parse_strategy')}</b>,
                    raw response length: {status.get('raw_llm_response_length_chars')} characters).
                    This is why your scores match — nothing was actually optimized.
                    <br><br>
                    <b>Raw model response preview:</b>
                    <pre style="white-space: pre-wrap; font-size: 0.8rem;">{status.get('raw_llm_response_preview')}</pre>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.caption(f"✅ Parsed successfully via `{status.get('parse_strategy')}` strategy.")

    hallucination_warning = results.get("hallucination_warning")
    if hallucination_warning:
        st.markdown(
            f"""
            <div class="warning-box">
                🛡️ <b>Hallucination check:</b> the following numbers appear in the optimized CV but were
                not found anywhere in your original CV — verify they're accurate before using them:
                <b>{', '.join(hallucination_warning)}</b>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Create Tabbed Dashboard
    tab_overview, tab_cv, tab_bullets, tab_pitch = st.tabs([
        "Overview",
        "Optimized CV",
        "Bullet Transformations",
        "Pitch & Interview Prep",
    ])

    # ----------------------------------------------------
    # Tab 1: Overview & ATS Scores
    # ----------------------------------------------------
    with tab_overview:
        st.markdown("### Full-CV ATS Match Score")

        orig_score = results["original_score"]
        new_score = results["new_score"]
        score_gain = round(new_score - orig_score, 1)
        gain_color = "var(--stamp-green)" if score_gain >= 0 else "var(--pen-red)"
        verdict_text = "STRONG MATCH" if new_score >= 75 else ("NEEDS WORK" if new_score < 50 else "FAIR MATCH")
        verdict_color = "var(--stamp-green)" if new_score >= 75 else ("var(--pen-red)" if new_score < 50 else "var(--gold)")

        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(
                f"""
                <div class="stamp-card">
                    <div class="stamp-label">Before Review</div>
                    <div class="stamp-value before">{orig_score}%</div>
                    <div class="stamp-caption">keyword coverage</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with c2:
            st.markdown(
                f"""
                <div class="stamp-card">
                    <div class="stamp-label">After Rewrite</div>
                    <div class="stamp-value after">{new_score}%</div>
                    <div class="stamp-caption">keyword coverage</div>
                    <div class="stamp-verdict" style="color: {verdict_color};">{verdict_text}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with c3:
            st.markdown(
                f"""
                <div class="stamp-card">
                    <div class="stamp-label">Net Gain</div>
                    <div class="stamp-value" style="color: {gain_color};">
                        {"+" if score_gain > 0 else ""}{score_gain}%
                    </div>
                    <div class="stamp-caption">points added</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.write("")
        st.progress(min(1.0, max(0.0, new_score / 100.0)), text=f"Full CV ATS Alignment: {new_score}%")

        # Keyword Gap Analysis
        st.write("")
        st.markdown("### Keyword Gap Analysis")
        missing_before = results.get("missing_keywords_before_rewrite", [])
        still_missing = results.get("missing_keywords_still_remaining", [])
        still_missing_set = set(still_missing)

        if missing_before:
            st.markdown("**High-value keywords originally missing from your CV:**")
            kw_html = "".join([
                f'<span class="keyword-badge{"" if kw in still_missing_set else " matched"}">'
                f'{"✕ " if kw in still_missing_set else "✓ "}{kw}</span>'
                for kw in missing_before
            ])
            st.markdown(f"<div>{kw_html}</div>", unsafe_allow_html=True)
            
            if still_missing:
                st.markdown(
                    f"""
                    <div class="warning-box">
                        <b>Still open:</b> {len(still_missing)} keyword(s) need specific candidate input or domain
                        details to integrate honestly: <b>{', '.join(still_missing)}</b>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            else:
                st.success("All high-value missing keywords were successfully integrated into your CV.")
        else:
            st.success("No missing high-weight keywords detected in original CV.")

    # ----------------------------------------------------
    # Tab 2: Full Optimized CV
    # ----------------------------------------------------
    with tab_cv:
        st.markdown("### Complete Optimized CV Text")
        full_cv_text = results.get("full_optimized_cv", "")
        
        col_cv_stats1, col_cv_stats2 = st.columns([3, 1])
        with col_cv_stats1:
            st.caption("Includes all keyword integrations, formatted skills section, and enhanced bullet points.")
        with col_cv_stats2:
            st.caption(f"Char count: {len(full_cv_text)} · Words: {len(full_cv_text.split())}")

        st.text_area(
            "Copy & use your upgraded resume:",
            value=full_cv_text,
            height=380,
            help="Copy this complete text directly into your Word or LaTeX resume template.",
        )
        
        st.download_button(
            label="Download optimized CV (.txt)",
            data=full_cv_text,
            file_name="optimized_resume.txt",
            mime="text/plain",
        )

    # ----------------------------------------------------
    # Tab 3: Bullet Transformations
    # ----------------------------------------------------
    with tab_bullets:
        st.markdown("### Bullet Point Transformations")
        st.caption("Demonstrates how raw experience statements were converted into high-impact, ATS-optimized achievement bullets.")
        
        improved_bullets = results.get("improved_bullet_points", [])
        if improved_bullets:
            for idx, bullet in enumerate(improved_bullets, 1):
                pattern = bullet.get("pattern_used") or "skill_and_keyword_integration"
                unverified = bullet.get("unverified_numbers", [])
                
                unverified_warning = ""
                if unverified:
                    unverified_warning = f"""
                    <div class="warning-box">
                        <b>Unverified metrics:</b> the rewrite introduced ({", ".join(unverified)}) which don't appear
                        in your original CV. Verify these reflect your real experience before using them.
                    </div>
                    """

                st.markdown(
                    f"""
                    <div class="bullet-card">
                        <span class="pattern-tag">{pattern.replace('_', ' ')}</span>
                        <div style="font-family: 'IBM Plex Mono', monospace; font-size: 0.7rem; font-weight: 600; color: var(--ink-soft); text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 0.6rem;">Transformation {idx:02d}</div>
                        <div class="before-text">{bullet['before']}</div>
                        <div class="after-text">{bullet['after']}</div>
                        {unverified_warning}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        else:
            st.info("No individual bullet rewrites generated.")

    # ----------------------------------------------------
    # Tab 4: Pitch & Interview Prep
    # ----------------------------------------------------
    with tab_pitch:
        st.markdown("### Elevator Pitch")
        st.markdown(
            f"""
            <div class="pitch-card">
                <div style="font-size: 1.08rem; line-height: 1.7; color: var(--ink); font-weight: 400;">
                    "{results.get('elevator_pitch', 'N/A')}"
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.write("")
        st.markdown("### Likely Interview Questions")
        questions = results.get("likely_interview_questions", [])
        for i, q in enumerate(questions, 1):
            with st.expander(f"Question {i}: {q}"):
                st.markdown(
                    "**Strategy:** connect your answer directly to the key skills and keywords "
                    "highlighted in the gap analysis."
                )