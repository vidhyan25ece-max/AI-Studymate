import streamlit as st
import re
from pypdf import PdfReader
from groq import Groq

# =========================================================
# PAGE SETTINGS
# =========================================================

st.set_page_config(
    page_title="AI StudyMate",
    page_icon="🎓",
    layout="wide"
)

# =========================================================
# CUSTOM CSS
# =========================================================

st.markdown("""
<style>

/* ===== GLOBAL DARK THEME ===== */

.stApp {
    background: #0b0f14;
    color: #f5f5f5;
}

.main .block-container {
    padding-top: 2rem;
    padding-bottom: 3rem;
}

/* ===== HERO ===== */

.hero {
    background: linear-gradient(135deg, #151b25, #10151d);
    padding: 35px;
    border-radius: 24px;
    margin-bottom: 35px;
    border: 1px solid #252d3a;
}

.hero h1 {
    color: #ffffff !important;
    font-size: 42px;
    margin-bottom: 10px;
}

.hero p {
    color: #b8c0cc !important;
    font-size: 18px;
}

/* ===== HEADINGS ===== */

h1, h2, h3, h4 {
    color: #ffffff !important;
}

/* ===== NORMAL TEXT ===== */

p {
    color: #d1d5db !important;
}

label {
    color: #e5e7eb !important;
}

/* ===== DASHBOARD CARDS ===== */

.card {
    background: #151a22;
    padding: 28px;
    border-radius: 20px;
    border: 1px solid #29313d;
    box-shadow: 0 4px 20px rgba(0,0,0,0.25);
    min-height: 160px;
}

.card h3 {
    color: #ffffff !important;
    margin-bottom: 12px;
}

.card p {
    color: #b9c0ca !important;
}

/* ===== BUTTONS ===== */

.stButton > button {
    width: 100%;
    border-radius: 12px;
    border: 1px solid #343d4a;
    padding: 12px 18px;
    font-weight: 600;
    background: #171d26;
    color: #ffffff !important;
}

.stButton > button:hover {
    border-color: #7c83ff;
    background: #202735;
    color: #ffffff !important;
}

/* ===== SIDEBAR ===== */

section[data-testid="stSidebar"] {
    background: #090d12;
}

section[data-testid="stSidebar"] * {
    color: #f5f5f5 !important;
}

/* ===== INPUT BOXES ===== */

input,
textarea {
    color: #ffffff !important;
    background: #151a22 !important;
    border: 1px solid #343d4a !important;
}

/* ===== SELECT BOX ===== */

div[data-baseweb="select"] {
    background: #151a22 !important;
    color: #ffffff !important;
}

div[data-baseweb="select"] * {
    color: #ffffff !important;
}

/* ===== NUMBER INPUT ===== */

div[data-testid="stNumberInput"] input {
    background: #151a22 !important;
    color: #ffffff !important;
}

/* ===== FILE UPLOADER ===== */

section[data-testid="stFileUploader"] {
    background: #151a22;
    border: 1px solid #343d4a;
    border-radius: 15px;
}

section[data-testid="stFileUploader"] * {
    color: #e5e7eb !important;
}

/* ===== TEXT AREA ===== */

textarea {
    background: #151a22 !important;
    color: #ffffff !important;
}

/* ===== ALERTS ===== */

.stAlert {
    border-radius: 12px;
}

/* ===== DIVIDERS ===== */

hr {
    border-color: #29313d;
}

/* ===== FOOTER ===== */

.footer {
    text-align: center;
    color: #7f8793 !important;
    padding: 30px;
    margin-top: 40px;
}
/* ===== SIDEBAR NAVIGATION BUTTONS ===== */

section[data-testid="stSidebar"] .stButton > button {
    width: 100%;
    text-align: left;
    background: #11161d;
    color: #e5e7eb !important;
    border: 1px solid #252d38;
    border-radius: 12px;
    padding: 12px 16px;
    margin-bottom: 8px;
    font-size: 15px;
    font-weight: 600;
}

section[data-testid="stSidebar"] .stButton > button:hover {
    background: #1c2430;
    border-color: #6366f1;
    color: #ffffff !important;
}

</style>
""", unsafe_allow_html=True)


# =========================================================
# GROQ CONNECTION
# =========================================================

try:

    client = Groq(
        api_key=st.secrets["GROQ_API_KEY"]
    )

except Exception:

    st.error(
        "⚠️ GROQ_API_KEY is not configured yet."
    )

    st.stop()


MODEL = "openai/gpt-oss-20b"


# =========================================================
# SESSION STATE
# =========================================================

if "pdf_text" not in st.session_state:
    st.session_state.pdf_text = ""

if "file_name" not in st.session_state:
    st.session_state.file_name = ""

if "ai_response" not in st.session_state:
    st.session_state.ai_response = ""


# =========================================================
# AI FUNCTION
# =========================================================

def ask_groq(prompt):

    try:

        response = client.chat.completions.create(

            model=MODEL,

            messages=[

                {
                    "role": "system",
                    "content": """
You are AI StudyMate, a personal AI tutor
for college students.

Be:
- Simple
- Clear
- Accurate
- Student-friendly
- Well structured

Use headings and bullet points when useful.
"""
                },

                {
                    "role": "user",
                    "content": prompt
                }

            ],

            temperature=0.3,

            max_tokens=1200
        )

        return response.choices[0].message.content

    except Exception as e:

        return f"⚠️ AI Error: {e}"


# =========================================================
# GET RELEVANT TEXT
# =========================================================

def get_relevant_text(question="", max_chars=6000):

    text = st.session_state.pdf_text

    if not text:
        return ""

    chunks = [
        text[i:i+1000]
        for i in range(0, len(text), 1000)
    ]

    if not question:

        return "\n\n".join(chunks[:6])[:max_chars]

    words = set(
        word.lower()
        for word in re.findall(
            r"[A-Za-z]{3,}",
            question
        )
    )

    scored = []

    for chunk in chunks:

        chunk_words = set(
            word.lower()
            for word in re.findall(
                r"[A-Za-z]{3,}",
                chunk
            )
        )

        score = len(
            words.intersection(chunk_words)
        )

        scored.append(
            (score, chunk)
        )

    scored.sort(
        key=lambda x: x[0],
        reverse=True
    )

    selected = [
        chunk
        for score, chunk in scored[:6]
    ]

    return "\n\n".join(selected)[:max_chars]


# =========================================================
# LOAD PDF
# =========================================================

def process_pdf(uploaded_file):

    if uploaded_file is None:

        return False

    try:

        reader = PdfReader(
            uploaded_file
        )

        text = ""

        for page in reader.pages:

            text += (
                page.extract_text() or ""
            ) + "\n"

        if not text.strip():

            return False

        st.session_state.pdf_text = text
        st.session_state.file_name = uploaded_file.name

        return True

    except Exception:

        return False


# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    st.markdown(
        """
        # 🎓 AI StudyMate

        Your personal AI learning companion.
        """
    )

    st.divider()

st.sidebar.markdown("### Navigation")

pages = [
    "🏠 Dashboard",
    "📚 Study Material",
    "🤖 AI Tutor",
    "❓ Quiz",
    "📅 Smart Timetable",
    "📊 Study Report"
]

if "page" not in st.session_state:
    st.session_state.page = "🏠 Dashboard"

for p in pages:
    if st.sidebar.button(
        p,
        key="nav_" + p,
        use_container_width=True
    ):
        st.session_state.page = p

page = st.session_state.page

st.divider()

if st.session_state.pdf_text:
    st.success("📄 Material loaded")
    st.caption(st.session_state.file_name)
else:
    st.info("Upload study material to begin.")


# =========================================================
# HEADER
# =========================================================


# =========================================================
# HEADER
# =========================================================

st.markdown("""
<div class="hero">

<div class="hero-title">
🎓 AI StudyMate
</div>

<div class="hero-subtitle">
Your personal AI learning companion — understand,
practice, plan and revise smarter.
</div>

</div>
""", unsafe_allow_html=True)


# =========================================================
# DASHBOARD
# =========================================================

if page == "🏠 Dashboard":

    st.markdown(
        '<div class="section-title">🏠 Student Dashboard</div>',
        unsafe_allow_html=True
    )

    col1, col2, col3 = st.columns(3)

    with col1:

        st.markdown("""
        <div class="card">

        <h3>📚 Study Material</h3>

        <p>
        Upload your notes or textbook PDF
        and let AI understand it.
        </p>

        </div>
        """, unsafe_allow_html=True)

    with col2:

        st.markdown("""
        <div class="card">

        <h3>🤖 AI Tutor</h3>

        <p>
        Ask questions and get
        simple explanations.
        </p>

        </div>
        """, unsafe_allow_html=True)

    with col3:

        st.markdown("""
        <div class="card">

        <h3>📅 Smart Planning</h3>

        <p>
        Create a personalized
        study timetable.
        </p>

        </div>
        """, unsafe_allow_html=True)

    st.markdown(
        "### ⚡ Quick Study Actions"
    )

    c1, c2, c3 = st.columns(3)

    with c1:

        if st.button(
            "📖 Explain Material",
            use_container_width=True
        ):

            if st.session_state.pdf_text:

                material = get_relevant_text()

                st.session_state.ai_response = ask_groq(
                    f"""
STUDY MATERIAL:

{material}

Explain the important concepts
in simple language for a college student.

Include:
- Important concepts
- Definitions
- Small examples
- Key points
"""
                )

            else:

                st.warning(
                    "Upload study material first."
                )

    with c2:

        if st.button(
            "📝 Summarize",
            use_container_width=True
        ):

            if st.session_state.pdf_text:

                material = get_relevant_text()

                st.session_state.ai_response = ask_groq(
                    f"""
STUDY MATERIAL:

{material}

Create an exam-oriented summary.

Include:
- Main concepts
- Important definitions
- Key points
- Exam revision points
"""
                )

            else:

                st.warning(
                    "Upload study material first."
                )

    with c3:

        if st.button(
            "💡 Give Examples",
            use_container_width=True
        ):

            if st.session_state.pdf_text:

                material = get_relevant_text()

                st.session_state.ai_response = ask_groq(
                    f"""
STUDY MATERIAL:

{material}

Give simple examples for the
important concepts.

If programming concepts are present,
include simple Python examples.
"""
                )

            else:

                st.warning(
                    "Upload study material first."
                )

    if st.session_state.ai_response:

        st.markdown("### 🤖 AI Response")

        st.markdown(
            st.session_state.ai_response
        )


# =========================================================
# STUDY MATERIAL
# =========================================================

elif page == "📚 Study Material":

    st.markdown(
        '<div class="section-title">📚 My Study Material</div>',
        unsafe_allow_html=True
    )

    st.write(
        "Upload your study material and StudyMate will use it to answer questions."
    )

    uploaded_file = st.file_uploader(
        "📄 Upload PDF",
        type=["pdf"]
    )

    if uploaded_file:

        if st.button(
            "📥 Load Study Material",
            type="primary"
        ):

            success = process_pdf(
                uploaded_file
            )

            if success:

                st.success(
                    f"✅ {uploaded_file.name} loaded successfully!"
                )

                st.info(
                    f"📄 Characters extracted: "
                    f"{len(st.session_state.pdf_text):,}"
                )

            else:

                st.error(
                    "❌ Could not extract text from this PDF."
                )

    if st.session_state.pdf_text:

        st.markdown("### 📄 Current Material")

        st.write(
            f"**File:** {st.session_state.file_name}"
        )

        st.write(
            f"**Characters:** "
            f"{len(st.session_state.pdf_text):,}"
        )


# =========================================================
# AI TUTOR
# =========================================================

elif page == "🤖 AI Tutor":

    st.markdown(
        '<div class="section-title">🤖 AI Tutor</div>',
        unsafe_allow_html=True
    )

    st.write(
        "Ask questions about your uploaded study material."
    )

    question = st.text_area(
        "💬 Your Question",
        placeholder=(
            "Example: What are string literals? "
            "Explain with an example."
        ),
        height=120
    )

    if st.button(
        "✨ Ask AI",
        type="primary"
    ):

        if not st.session_state.pdf_text:

            st.warning(
                "📚 Please upload study material first."
            )

        elif not question.strip():

            st.warning(
                "✏️ Please enter a question."
            )

        else:

            material = get_relevant_text(
                question
            )

            st.session_state.ai_response = ask_groq(
                f"""
STUDY MATERIAL:

{material}

STUDENT QUESTION:

{question}

Answer using the study material.

Explain simply.
Do not invent information.

If the answer cannot be found
in the material, say so clearly.
"""
            )

    if st.session_state.ai_response:

        st.markdown("### 💡 Answer")

        st.markdown(
            st.session_state.ai_response
        )


# =========================================================
# QUIZ
# =========================================================

elif page == "❓ Quiz":

    st.markdown(
        '<div class="section-title">❓ Quiz Generator</div>',
        unsafe_allow_html=True
    )

    st.write(
        "Test your understanding of the uploaded material."
    )

    number = st.slider(
        "Number of questions",
        3,
        10,
        5
    )

    difficulty = st.selectbox(
        "Difficulty",
        [
            "Easy",
            "Medium",
            "Mixed",
            "Hard"
        ]
    )

    if st.button(
        "🎯 Generate Quiz",
        type="primary"
    ):

        if not st.session_state.pdf_text:

            st.warning(
                "Upload study material first."
            )

        else:

            material = get_relevant_text()

            result = ask_groq(
                f"""
STUDY MATERIAL:

{material}

Create {number} multiple-choice questions.

Difficulty:
{difficulty}

For every question provide:

Question

A. Option
B. Option
C. Option
D. Option

Correct Answer:
Explanation:

Questions must be based on the study material.
"""
            )

            st.markdown(result)


# =========================================================
# SMART TIMETABLE
# =========================================================

elif page == "📅 Smart Timetable":

    st.markdown(
        '<div class="section-title">📅 Smart Study Planner</div>',
        unsafe_allow_html=True
    )

    st.write(
        "Tell StudyMate how much time you have and it will build a realistic timetable."
    )

    col1, col2 = st.columns(2)

    with col1:

        days = st.number_input(
            "📆 How many days are left?",
            min_value=1,
            max_value=365,
            value=7
        )

        hours = st.number_input(
            "⏱️ How many hours can you study each day?",
            min_value=0.5,
            max_value=24.0,
            value=3.0,
            step=0.5
        )

        subjects = st.text_area(
            "📚 Subjects / Topics",
            placeholder=(
                "Example:\n"
                "Python\n"
                "Strings\n"
                "Files\n"
                "Functions"
            )
        )

    with col2:

        priorities = st.text_area(
            "⭐ Difficult / High-Priority Topics",
            placeholder=(
                "Example:\n"
                "Files\n"
                "Functions"
            )
        )

        exam_type = st.selectbox(
            "🎯 What are you preparing for?",
            [
                "Semester Exam",
                "Internal Exam",
                "Quiz",
                "Assignment",
                "Competitive Exam",
                "General Revision"
            ]
        )

    total_hours = days * hours

    st.info(
        f"⏳ You have approximately "
        f"**{total_hours:.1f} study hours** available."
    )

    if st.button(
        "✨ Create My Study Plan",
        type="primary"
    ):

        if not st.session_state.pdf_text:

            st.warning(
                "Upload your study material first."
            )

        elif not subjects.strip():

            st.warning(
                "Enter your subjects/topics."
            )

        else:

            material = get_relevant_text(
                "",
                6000
            )

            result = ask_groq(
                f"""
Create a personalized study timetable.

STUDY MATERIAL:
{material}

STUDENT INFORMATION:

Days remaining:
{days}

Study hours per day:
{hours}

Total available hours:
{total_hours}

Subjects/topics:
{subjects}

High-priority topics:
{priorities}

Exam type:
{exam_type}

Create:

# 📅 STUDY TIMETABLE

Create a day-by-day plan.

For each day include:

| Session | Topic | Activity | Duration |

Balance:
- Learning
- Practice
- Revision
- Quiz/Test

Do not exceed the student's
available daily study hours.

# 📊 STUDY REPORT

Include:

Total days:
Total available hours:
Learning hours:
Practice hours:
Revision hours:
Quiz/Test hours:

# 🎯 PRIORITY ANALYSIS

High priority:
Medium priority:
Needs more revision:

# 💡 RECOMMENDATIONS

Give 4 useful study tips.
"""
            )

            st.markdown(result)


# =========================================================
# STUDY REPORT
# =========================================================

elif page == "📊 Study Report":

    st.markdown(
        '<div class="section-title">📊 Study Report</div>',
        unsafe_allow_html=True
    )

    st.write(
        "Generate an overall study analysis from your material."
    )

    if st.button(
        "📊 Generate Study Report",
        type="primary"
    ):

        if not st.session_state.pdf_text:

            st.warning(
                "Upload study material first."
            )

        else:

            material = get_relevant_text(
                "",
                6000
            )

            report = ask_groq(
                f"""
Analyze the following study material.

STUDY MATERIAL:

{material}

Create a student study report.

Include:

# 📚 MATERIAL OVERVIEW

What topics are covered?

# ⭐ IMPORTANT TOPICS

List the most important concepts.

# ⚠️ DIFFICULT AREAS

Identify concepts students may find difficult.

# 📝 EXAM PREPARATION

What should the student focus on?

# 🔄 REVISION STRATEGY

How should the student revise?

# 🎯 RECOMMENDED ACTIONS

Give 5 practical next steps.
"""
            )

            st.markdown(report)


# =========================================================
# FOOTER
# =========================================================

st.divider()

st.caption(
    "🎓 AI StudyMate • Learn smarter • Practice better • Plan effectively"
)
