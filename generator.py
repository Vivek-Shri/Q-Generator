import streamlit as st
import groq
import re
import json

# Initialize Groq Client - REPLACE WITH YOUR ACTUAL API KEY
api_key = "your_groq_api"
client = groq.Client(api_key=api_key)

# Define topics and subtopics
topics = {
    "Aptitude": [
        "All", "Basic Arithmetic", "Algebra", "Geometry", "Trigonometry",
        "Probability and Statistics", "Time and Work", "Speed, Distance, and Time",
        "Profit and Loss", "Ratios and Proportions", "Permutations and Combinations"
    ],
    "Logical Reasoning": [
        "All", "Analogies", "Coding-Decoding", "Blood Relations", "Syllogism",
        "Seating Arrangement", "Puzzles", "Statement and Assumptions", "Direction Sense"
    ],
    "Code": ["All", "Data Structures", "Algorithms", "Database Queries", "OOP Concepts"],
    "Verbal": ["All", "Synonyms & Antonyms", "Reading Comprehension", "Grammar", "Sentence Correction"]
}

# Function to generate MCQs
def generate_mcq(category, subtopics, difficulty, num_questions):
    subtopics_text = ", ".join(subtopics) if "All" not in subtopics else "All subtopics"
    prompt = f"""SYSTEM ROLE: You are a strict multiple-choice question generator with exceptional technical accuracy. 
    Generate EXACTLY {num_questions} unique MCQs combining {category} ({subtopics_text}) with {difficulty} difficulty.

    FORMAT TEMPLATE - REPEAT THIS STRUCTURE {num_questions} TIMES:
    ---
    [NUMBER]. [Question stem CLEARLY requiring single correct answer]?
    a) [Distinct option 1]
    b) [Plausible option 2]
    c) [Best answer]
    d) [Common misconception]
    Answer: [LOWERCASE LETTER a-d]

    RULES:
    1. STRICT FORMAT: No variations in numbering, spacing, or punctuation
    2. ANSWER VALIDATION: Exactly 1 correct answer per question
    3. DISTRACTORS: Wrong answers must be plausible for the difficulty
    4. CATEGORY ADHERENCE: Technical accuracy for {category} domain ({subtopics_text})
    5. OUTPUT CONTROL: No explanations, markdown, or extra text
    6. ERROR PREVENTION: If unsure about any question, regenerate it

    WARNING: ANY FORMAT DEVIATION WILL CAUSE SYSTEM ERRORS. DOUBLE-CHECK BEFORE RESPONDING."""

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

# Parse generated MCQs
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

# Save questions to backend file
def save_questions_to_file(questions, category, subtopics):
    filename = f"questions_{category}_{'_'.join(subtopics)}.json"
    with open(filename, "w") as f:
        json.dump(questions, f, indent=4)

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

# Topic selection
category = st.sidebar.selectbox("Category", list(topics.keys()))

# Subtopic selection with scrollbar
subtopics = st.sidebar.multiselect(
    "Subtopics (Choose at least one)", topics[category], default=["All"]
)

difficulty = st.sidebar.selectbox("Difficulty", ['Beginner-level', 'Mid-level', 'Hard-level'])
num_questions = st.sidebar.selectbox("Number of Questions", [10, 20, 30, 40, 50])

if st.sidebar.button("Generate New Test"):
    test_content = generate_mcq(category, subtopics, difficulty, num_questions)
    parsed_questions = parse_questions(test_content)
    
    # Save questions to backend
    save_questions_to_file(parsed_questions, category, subtopics)
    
    st.session_state.questions = parsed_questions
    st.session_state.current_question = 0
    st.session_state.answers = {}
    st.session_state.submitted = False

# Main test interface
st.title("WebMobi 360 Question Generator")

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
        score = sum(1 for i, q in enumerate(st.session_state.questions) if 
                    st.session_state.answers.get(i, "No answer")[0].lower() == q['answer'])
        
        st.subheader(f"Your Score: {score} out of {len(st.session_state.questions)}")
        
        with st.expander("Review Questions", expanded=True):
            for i, q in enumerate(st.session_state.questions):
                st.markdown(f"**Question {i+1}**: {q['question']}")
                user_answer = st.session_state.answers.get(i, "No answer")
                correct = user_answer[0].lower() == q['answer']
                st.markdown(f"<p style='color:{'#2ECC40' if correct else '#FF4136'}; font-weight:bold'>Your answer: {user_answer}</p>", unsafe_allow_html=True)
                st.markdown(f"<p style='color:#0074D9; font-weight:bold'>Correct answer: {q['answer']}) {q['options'][ord(q['answer']) - ord('a')]}</p>", unsafe_allow_html=True)
                st.markdown("---")

        if st.button("Take New Test"):
            st.session_state.questions = []
            st.session_state.submitted = False
            st.rerun()
else:
    st.info("Select your test settings and click 'Generate New Test' to begin")
