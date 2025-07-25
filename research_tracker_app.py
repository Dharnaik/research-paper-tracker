import streamlit as st

# --------------------- USERS ---------------------
users = {
    "admin": {
        "password": "adminpass",
        "role": "admin",
        "name": "Admin"
    },
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
    # Reviewers added at runtime
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
            return  # Let Streamlit naturally rerun
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
    return len(st.session_state.papers) + 1

st.sidebar.write(f"Logged in as: {st.session_state.name} ({st.session_state.role})")
if st.sidebar.button("Logout"):
    logout()
    st.experimental_rerun()

# --------------------- ADMIN DASHBOARD ---------------------
if st.session_state.role == "admin":
    st.title("Admin Dashboard")

    st.subheader("All Papers")
    if st.session_state.papers:
        for paper in st.session_state.papers:
            st.markdown(f"**ID:** {paper['id']} | **Title:** {paper['title']} | **By:** {users[paper['faculty_username']]['name']}")
            st.write(f"Status: {paper['status']}")
            st.write(f"Abstract: {paper['abstract']}")
            st.write(f"Content: {paper['content']}")
            st.write("---")
            # Show reviews for this paper
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
            # Create reviewer
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

    # Submit a new paper
    st.subheader("Submit New Paper")
    with st.form("paper_form", clear_on_submit=True):
        title = st.text_input("Paper Title")
        abstract = st.text_area("Abstract")
        content = st.text_area("Content", height=200)
        submit_paper = st.form_submit_button("Submit Paper")
        if submit_paper:
            paper = {
                "id": next_paper_id(),
                "faculty_username": st.session_state.username,
                "title": title,
                "abstract": abstract,
                "content": content,
                "status": "Draft"
            }
            st.session_state.papers.append(paper)
            st.success(f"Paper '{title}' submitted!")

    # Show papers by this faculty
    st.subheader("My Papers")
    papers = get_papers_for_faculty(st.session_state.username)
    for paper in papers:
        st.markdown(f"**ID:** {paper['id']} | **Title:** {paper['title']}")
        st.write(f"Status: {paper['status']}")
        st.write(f"Abstract: {paper['abstract']}")
        st.write(f"Content: {paper['content']}")
        # Update status
        new_status = st.selectbox(f"Update Status for Paper ID {paper['id']}", ["Draft", "In Progress", "Under Review", "Completed", "Submitted", "Accepted", "Rejected"], index=["Draft", "In Progress", "Under Review", "Completed", "Submitted", "Accepted", "Rejected"].index(paper['status']), key=f"status_{paper['id']}")
        if new_status != paper['status']:
            paper['status'] = new_status
            st.success(f"Status updated to {new_status}")
        # Show reviews
        reviews = get_reviews_for_paper(paper['id'])
        if reviews:
            st.write("**Reviews for this paper:**")
            for r in reviews:
                st.info(f"Reviewer: {r['reviewer']}\n\nSuggestions: {r['suggestions']}\n\nOverall: {r['overall_comment']}")
        else:
            st.write("_No reviews yet._")
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
            st.write(f"Abstract: {paper['abstract']}")
            st.write(f"Content: {paper['content']}")
            # Submit review
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
