import streamlit as st
from streamlit_quill import st_quill

# --------------------- USERS ---------------------
users = {
    "admin": {"password": "adminpass", "role": "admin", "name": "Admin"},
    "yuvaraj.bhirud": {"password": "pass1", "role": "faculty", "name": "Prof. Dr. Yuvaraj L. Bhirud"},
    "satish.patil": {"password": "pass2", "role": "faculty", "name": "Prof. Dr. Satish B. Patil"},
    "abhijeet.galatage": {"password": "pass3", "role": "faculty", "name": "Prof. Abhijeet A. Galatage"},
    "rajshekhar.rathod": {"password": "pass4", "role": "faculty", "name": "Prof. Dr. Rajshekhar G. Rathod"},
    "avinash.rakh": {"password": "pass5", "role": "faculty", "name": "Prof. Avinash A. Rakh"},
    "achyut.deshmukh": {"password": "pass6", "role": "faculty", "name": "Prof. Achyut A. Deshmukh"},
    "amit.dharnaik": {"password": "pass7", "role": "faculty", "name": "Prof. Dr. Amit S. Dharnaik"},
    "hrishikesh.mulay": {"password": "pass8", "role": "faculty", "name": "Prof. Hrishikesh U Mulay"},
    "gauri.desai": {"password": "pass9", "role": "faculty", "name": "Prof. Gauri S. Desai"},
    "bhagyashri.patil": {"password": "pass10", "role": "faculty", "name": "Prof. Bhagyashri D. Patil"},
    "sagar.sonawane": {"password": "pass11", "role": "faculty", "name": "Prof. Sagar K. Sonawane"},
}

# --------------------- IN-MEMORY DATABASES ---------------------
if 'papers' not in st.session_state:
    st.session_state.papers = []  # Each paper is a dict
if 'reviews' not in st.session_state:
    st.session_state.reviews = []  # Each review is a dict
if 'reviewers' not in st.session_state:
    st.session_state.reviewers = {}  # reviewer_username -> {assigned_paper_id}

# --------------------- AUTH LOGIC ---------------------
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ''
    st.session_state.role = ''
    st.session_state.name = ''

def login():
    st.title("Faculty Research Paper Portal - Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        user = users.get(username)
        if user and user["password"] == password:
            st.session_state.logged_in = True
            st.session_state.username = username
            st.session_state.role = user["role"]
            st.session_state.name = user["name"]
            st.success(f"Welcome, {user['name']} ({user['role']})")
            return
        else:
            st.error("Invalid username or password.")

def logout():
    st.session_state.logged_in = False
    st.session_state.username = ''
    st.session_state.role = ''
    st.session_state.name = ''
    st.success("Logged out!")

if not st.session_state.logged_in:
    login()
    st.stop()

# --------------------- SIDEBAR (logout and font settings) ---------------------
st.sidebar.write(f"Logged in as: {st.session_state.name} ({st.session_state.role})")
if st.sidebar.button("Logout"):
    logout()

# --------------------- FONT SETTINGS SECTION ---------------------
font_options = [
    "Times New Roman", "Georgia", "Arial", "Verdana", "Trebuchet MS", "Courier New", "Tahoma"
]

heading_size = st.sidebar.selectbox("Heading Font Size", [16, 18, 20], index=0)
subheading_size = st.sidebar.selectbox("Sub-heading Font Size", [12, 14, 16], index=1)
content_size = st.sidebar.selectbox("Content Font Size", [10, 11, 12, 13, 14], index=2)

heading_font = st.sidebar.selectbox("Heading Font", font_options, index=0)
subheading_font = st.sidebar.selectbox("Sub-heading Font", font_options, index=0)
content_font = st.sidebar.selectbox("Content Font", font_options, index=0)

st.session_state['heading_font'] = heading_font
st.session_state['subheading_font'] = subheading_font
st.session_state['content_font'] = content_font
st.session_state['heading_size'] = heading_size
st.session_state['subheading_size'] = subheading_size
st.session_state['content_size'] = content_size

# Custom CSS for journal paper styling
st.markdown(f"""
    <style>
        .stApp h1 {{
            font-family: '{st.session_state["heading_font"]}', serif !important;
            font-size: {st.session_state["heading_size"]}pt !important;
            font-weight: bold !important;
            text-align: center;
        }}
        .stApp h2, .stApp h3 {{
            font-family: '{st.session_state["subheading_font"]}', serif !important;
            font-size: {st.session_state["subheading_size"]}pt !important;
            font-weight: bold !important;
        }}
        .stApp p, .stApp li, .stApp div, .stApp span, .stApp label, .stApp input, .stApp textarea {{
            font-family: '{st.session_state["content_font"]}', serif !important;
            font-size: {st.session_state["content_size"]}pt !important;
        }}
        /* For Abstracts, optional: italic */
        .abstract-text {{
            font-style: italic !important;
            font-size: {max(st.session_state["content_size"]-1,10)}pt !important;
        }}
    </style>
""", unsafe_allow_html=True)

# --------------------- COMMON UTILS ---------------------
def get_paper_by_id(paper_id):
    for p in st.session_state.papers:
        if p['id'] == paper_id:
            return p
    return None

def add_review(paper_id, reviewer, suggestions, overall_comment):
    st.session_state.reviews.append({
        "paper_id": paper_id,
        "reviewer": reviewer,
        "suggestions": suggestions,
        "overall_comment": overall_comment
    })

def get_reviews_for_paper(paper_id):
    return [r for r in st.session_state.reviews if r['paper_id'] == paper_id]

def get_papers_for_faculty(username):
    return [p for p in st.session_state.papers if p['faculty_username'] == username]

def get_reviewer_assigned_paper(username):
    reviewer_info = st.session_state.reviewers.get(username)
    if reviewer_info:
        return reviewer_info['assigned_paper_id']
    return None

def next_paper_id():
    if st.session_state.papers:
        return max(p['id'] for p in st.session_state.papers) + 1
    else:
        return 1

# --------------------- ADMIN DASHBOARD ---------------------
if st.session_state.role == "admin":
    st.title("Admin Dashboard")

    st.subheader("All Papers")
    if st.session_state.papers:
        for paper in st.session_state.papers:
            st.markdown(f"**ID:** {paper['id']} | **Title:** {paper['title']} | **By:** {users[paper['faculty_username']]['name']}")
            st.write(f"Status: {paper['status']}")
            st.markdown(f'<div class="abstract-text">Abstract: {paper["abstract"]}</div>', unsafe_allow_html=True)
            st.markdown(paper['content'], unsafe_allow_html=True)
            st.write("---")
            reviews = get_reviews_for_paper(paper['id'])
            if reviews:
                st.write("**Reviews:**")
                for r in reviews:
                    st.info(f"Reviewer: {r['reviewer']}\n\nSuggestions: {r['suggestions']}\n\nOverall: {r['overall_comment']}")
            else:
                st.write("_No reviews yet._")
            st.write("===")
    else:
        st.info("No papers submitted yet.")

    st.subheader("Invite Reviewer")
    reviewer_username = st.text_input("Reviewer Username (e.g., reviewer1)")
    reviewer_password = st.text_input("Reviewer Password")
    paper_id_list = [str(p['id']) for p in st.session_state.papers]
    assigned_paper_id = st.selectbox("Assign to Paper ID", paper_id_list) if paper_id_list else ""
    if st.button("Create Reviewer Account"):
        if not reviewer_username or not reviewer_password or not assigned_paper_id:
            st.warning("All fields are required!")
        elif reviewer_username in users or reviewer_username in st.session_state.reviewers:
            st.warning("Reviewer username already exists.")
        else:
            users[reviewer_username] = {
                "password": reviewer_password,
                "role": "reviewer",
                "name": reviewer_username,
            }
            st.session_state.reviewers[reviewer_username] = {
                "assigned_paper_id": int(assigned_paper_id)
            }
            st.success(f"Reviewer '{reviewer_username}' created and assigned to paper ID {assigned_paper_id}.")

# --------------------- FACULTY DASHBOARD ---------------------
elif st.session_state.role == "faculty":
    st.title("Faculty Dashboard")
    st.write(f"Welcome, {st.session_state.name}")

    # --- Manage which paper is being edited/created ---
    if 'edit_paper_id' not in st.session_state:
        st.session_state.edit_paper_id = None  # None means new paper

    # --- List Existing Papers ---
    papers = get_papers_for_faculty(st.session_state.username)
    st.subheader("My Papers")
    for paper in papers:
        col1, col2, col3 = st.columns([6,2,2])
        with col1:
            st.markdown(f"**ID:** {paper['id']} | **Title:** {paper['title']} | Status: {paper['status']}")
        with col2:
            if st.button("Edit", key=f"edit_{paper['id']}"):
                st.session_state.edit_paper_id = paper['id']
        with col3:
            if st.button("Delete", key=f"delete_{paper['id']}"):
                st.session_state.papers = [p for p in st.session_state.papers if p['id'] != paper['id']]
                st.experimental_rerun()
        st.markdown("---")

    # --- Button for New Paper ---
    if st.button("Start New Paper"):
        st.session_state.edit_paper_id = None  # Switch to new paper form

    # --- Paper Form (for new or editing existing) ---
    st.subheader("Write Paper")
    if st.session_state.edit_paper_id is not None:
        # Editing an existing paper
        paper = next(p for p in papers if p['id'] == st.session_state.edit_paper_id)
        title = st.text_input("Paper Title", value=paper['title'])
        abstract = st.text_area("Abstract", value=paper['abstract'])
        content = st_quill(key=f"content_quill_edit_{paper['id']}", value=paper['content'], html=True)
        submit_label = "Update Paper"
    else:
        # New paper
        title = st.text_input("Paper Title")
        abstract = st.text_area("Abstract")
        content = st_quill(key="content_quill_new", html=True)
        submit_label = "Submit Paper"

    if st.button(submit_label):
        if not title or not content:
            st.warning("Title and content required.")
        else:
            if st.session_state.edit_paper_id is not None:
                # Update existing paper
                for p in st.session_state.papers:
                    if p['id'] == st.session_state.edit_paper_id:
                        p['title'] = title
                        p['abstract'] = abstract
                        p['content'] = content
                        st.success("Paper updated!")
                        break
                st.session_state.edit_paper_id = None
            else:
                # New paper
                new_paper = {
                    "id": next_paper_id(),
                    "faculty_username": st.session_state.username,
                    "title": title,
                    "abstract": abstract,
                    "content": content,
                    "status": "Draft"
                }
                st.session_state.papers.append(new_paper)
                st.success(f"Paper '{title}' submitted!")
            st.experimental_rerun()

    # --- Option to cancel editing ---
    if st.session_state.edit_paper_id is not None:
        if st.button("Cancel Editing"):
            st.session_state.edit_paper_id = None
            st.experimental_rerun()

    # --- Show reviews for each paper ---
    for paper in papers:
        reviews = get_reviews_for_paper(paper['id'])
        if reviews:
            st.write(f"**Reviews for Paper ID {paper['id']} - {paper['title']}:**")
            for r in reviews:
                st.info(f"Reviewer: {r['reviewer']}\n\nSuggestions: {r['suggestions']}\n\nOverall: {r['overall_comment']}")
        st.write("===")

# --------------------- REVIEWER DASHBOARD ---------------------
elif st.session_state.role == "reviewer":
    st.title("Reviewer Dashboard")
    assigned_paper_id = get_reviewer_assigned_paper(st.session_state.username)
    if assigned_paper_id:
        paper = get_paper_by_id(assigned_paper_id)
        if paper:
            st.write(f"**Paper Assigned:** (ID: {paper['id']})")
            st.write(f"Title: {paper['title']}")
            st.write(f"By: {users[paper['faculty_username']]['name']}")
            st.markdown(f'<div class="abstract-text">Abstract: {paper["abstract"]}</div>', unsafe_allow_html=True)
            st.markdown(paper['content'], unsafe_allow_html=True)
            st.subheader("Submit Your Review")
            suggestions = st.text_area("Suggestions and Comments")
            overall_comment = st.text_area("Overall Comment")
            if st.button("Submit Review"):
                add_review(paper['id'], st.session_state.username, suggestions, overall_comment)
                st.success("Review submitted!")
        else:
            st.error("Assigned paper not found.")
    else:
        st.info("No paper assigned.")
