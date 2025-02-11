import streamlit as st
import groq
import re

# Initialize Groq Client - REPLACE WITH YOUR ACTUAL API KEY
api_key = "YOUR API KEY"
client = groq.Client(api_key=api_key)

# Dictionary for categories and subtopics
subtopic_dict = {
    "Aptitude": [
        "All", "Basic Arithmetic", "Algebra", "Geometry", "Trigonometry", 
        "Probability and Statistics", "Time and Work", "Speed, Distance, and Time", 
        "Profit and Loss", "Ratios and Proportions", "Permutations and Combinations"
    ],
    "Logical Reasoning": [
        "All", "Blood Relations", "Coding-Decoding", "Syllogisms", "Seating Arrangement",
        "Data Sufficiency", "Direction Sense", "Puzzles", "Statement & Assumption"
    ],
    "Code": [
        "All", "Data Structures", "Algorithms", "Programming Basics", "OOP Concepts",
        "Database Queries", "Operating Systems", "Networking", "Web Development"
    ],
    "Verbal": [
        "All", "Reading Comprehension", "Grammar", "Vocabulary", "Sentence Correction",
        "Para Jumbles", "One-word Substitution", "Synonyms & Antonyms"
    ]
}

def generate_mcq(category, subtopics, difficulty, num_questions):
    # Format subtopics properly
    subtopics_str = ", ".join(subtopics) if "All" not in subtopics else "All subtopics of " + category
    
    prompt = f"""SYSTEM ROLE: You are a strict multiple-choice question generator with exceptional technical accuracy.
    Generate EXACTLY {num_questions} unique MCQs covering {subtopics_str} under {category} with {difficulty} difficulty.

    FORMAT TEMPLATE - REPEAT THIS STRUCTURE {num_questions} TIMES:
    ---
    [NUMBER]. [Question stem CLEARLY requiring a single correct answer]?
    a) [Distinct option 1]
    b) [Plausible option 2]
    c) [Best answer]
    d) [Common misconception]
    Answer: [LOWERCASE LETTER a-d]

    RULES:
    1. STRICT FORMAT: No variations in numbering, spacing, or punctuation
    2. ANSWER VALIDATION: Exactly 1 correct answer per question
    3. DISTRACTORS: Wrong answers must be plausible for the difficulty
    4. CATEGORY ADHERENCE: Technical accuracy for {category} and chosen subtopics
    5. OUTPUT CONTROL: No explanations, markdown, or extra text
    6. ERROR PREVENTION: If unsure about any question, regenerate it"""

    response = client.chat.completions.create(
        messages=[
            {"role": "system", "content": "You are an expert MCQ generator for technical assessments."},
            {"role": "user", "content": prompt}
        ],
        model="llama3-70b-8192",
        temperature=0.3,
        max_tokens=4096,
        top_p=0.9,
        frequency_penalty=0.5,
        presence_penalty=0.5,
    )
    return response.choices[0].message.content

def parse_questions(text):
    questions = []
    pattern = r"(\d+)\.\s*(.*?)\?\s*a\)\s*(.*?)\s*b\)\s*(.*?)\s*c\)\s*(.*?)\s*d\)\s*(.*?)\s*Answer:\s*([a-d])"
    matches = re.findall(pattern, text, re.DOTALL)

    for match in matches:
        question_text = match[1].strip()
        options = [opt.strip() for opt in match[2:6]]
        answer = match[6].strip().lower()

        if answer not in ['a', 'b', 'c', 'd']:
            continue

        questions.append({
            "question": question_text,
            "options": options,
            "answer": answer
        })

    return questions

# Initialize session state
if 'questions' not in st.session_state:
    st.session_state.questions = []
if 'current_question' not in st.session_state:
    st.session_state.current_question = 0
if 'answers' not in st.session_state:
    st.session_state.answers = {}
if 'submitted' not in st.session_state:
    st.session_state.submitted = False

# Sidebar controls
st.sidebar.header("Test Settings")
category = st.sidebar.selectbox("Category", list(subtopic_dict.keys()))

# Multi-select subtopics with a scrollable list
subtopics = st.sidebar.multiselect(
    "Select Subtopics", subtopic_dict[category], default="All", help="Scroll to see more options"
)

difficulty = st.sidebar.selectbox("Difficulty", ['Beginner-level', 'Mid-level', 'Hard-level'])
num_questions = st.sidebar.selectbox("Number of Questions", [10, 20, 30, 40, 50])

if st.sidebar.button("Generate New Test"):
    test_content = generate_mcq(category, subtopics, difficulty, num_questions)
    st.session_state.questions = parse_questions(test_content)
    st.session_state.current_question = 0
    st.session_state.answers = {}
    st.session_state.submitted = False

# Main test interface
st.title("Interactive MCQ Test")

if st.session_state.questions:
    if not st.session_state.submitted:
        q = st.session_state.questions[st.session_state.current_question]
        st.subheader(f"Question {st.session_state.current_question + 1}")
        st.write(q['question'])

        options = [f"{chr(97+i)}) {option}" for i, option in enumerate(q['options'])]
        selected_option = st.session_state.answers.get(st.session_state.current_question, None)

        answer = st.radio(
            "Select your answer:",
            options,
            index=options.index(selected_option) if selected_option in options else None,
            key=f"question_{st.session_state.current_question}"
        )

        if answer:
            st.session_state.answers[st.session_state.current_question] = answer

        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            if st.button("Previous") and st.session_state.current_question > 0:
                st.session_state.current_question -= 1
                st.rerun()
        with col2:
            st.write(f"Question {st.session_state.current_question + 1} of {len(st.session_state.questions)}")
        with col3:
            if st.button("Next") and st.session_state.current_question < len(st.session_state.questions) - 1:
                st.session_state.current_question += 1
                st.rerun()

        if st.button("Submit Test"):
            st.session_state.submitted = True
            st.rerun()
    else:
        score = sum(1 for q in st.session_state.questions if st.session_state.answers.get(st.session_state.current_question, "").startswith(q['answer']))
        st.subheader(f"Your Score: {score} out of {len(st.session_state.questions)}")

        if st.button("Take New Test"):
            st.session_state.questions = []
            st.session_state.submitted = False
            st.rerun()
else:
    st.info("Select your test settings and click 'Generate New Test' to begin")
