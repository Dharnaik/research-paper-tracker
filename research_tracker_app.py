import streamlit as st
import datetime
import os
import smtplib
from email.message import EmailMessage

# --- USERS (all faculty, admin, reviewers created by admin) ---
users = {
    "admin": {"password": "adminpass", "role": "admin", "name": "Admin"},
    "amit.dharnaik": {"password": "pass7", "role": "faculty", "name": "Prof. Dr. Amit S. Dharnaik"},
    "satish.patil": {"password": "pass8", "role": "faculty", "name": "Prof. Dr. Satish B. Patil"},
    "abhijeet.galatage": {"password": "pass9", "role": "faculty", "name": "Prof. Abhijeet A. Galatage"},
    "rajshekhar.rathod": {"password": "pass10", "role": "faculty", "name": "Prof. Dr. Rajshekhar G. Rathod"},
    "avinash.rakh": {"password": "pass11", "role": "faculty", "name": "Prof. Avinash A. Rakh"},
    "achyut.deshmukh": {"password": "pass12", "role": "faculty", "name": "Prof. Achyut A. Deshmukh"},
    "hrishikesh.mulay": {"password": "pass13", "role": "faculty", "name": "Prof. Hrishikesh U Mulay"},
    "gauri.desai": {"password": "pass14", "role": "faculty", "name": "Prof. Gauri S. Desai"},
    "bhagyashri.patil": {"password": "pass15", "role": "faculty", "name": "Prof. Bhagyashri D. Patil"},
    "sagar.sonawane": {"password": "pass16", "role": "faculty", "name": "Prof. Sagar K. Sonawane"},
    # Reviewers will be added dynamically by admin
}

PAPER_STATUS = [
    "Draft", "Submitted", "Under Review", "Review Completed",
    "Minor Revision Required", "Major Revision Required", "Accepted", "Rejected"
]

RECOMMEND_OPTIONS = [
    "Accept", "Minor Revision", "Major Revision", "Reject"
]

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

if 'papers' not in st.session_state: st.session_state.papers = []
if 'reviews' not in st.session_state: st.session_state.reviews = []
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ''
    st.session_state.role = ''
    st.session_state.name = ''
if 'assignments' not in st.session_state: st.session_state.assignments = {}  # paper_id -> [reviewer usernames]

def next_paper_id():
    if st.session_state.papers:
        return max(p['id'] for p in st.session_state.papers) + 1
    else:
        return 1

def login():
    st.title("Research Paper Portal - Login")
    username = st.text_input("Username").strip()
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        user = users.get(username)
        if user and user["password"] == password:
            st.session_state.logged_in = True
            st.session_state.username = username
            st.session_state.role = user["role"]
            st.session_state.name = user["name"]
        else:
            st.error("Invalid username or password.")

def logout():
    st.session_state.logged_in = False
    st.session_state.username = ''
    st.session_state.role = ''
    st.session_state.name = ''
    st.experimental_rerun()
    st.stop()

if not st.session_state.logged_in:
    login()
    st.stop()

st.sidebar.write(f"Logged in as: {st.session_state.name} ({st.session_state.role})")
if st.sidebar.button("Logout"):
    logout()

# --- Global Paper Dashboard in Sidebar ---
st.sidebar.markdown("## 📊 Paper Status Dashboard")
if not st.session_state.papers:
    st.sidebar.info("No papers submitted yet.")
else:
    for paper in st.session_state.papers:
        faculty_name = users[paper["faculty_username"]]["name"]
        reviewers = st.session_state.assignments.get(paper['id'], [])
        assigned_reviewers = ", ".join([users[r]['name'] for r in reviewers]) if reviewers else "-"
        st.sidebar.write(
            f"**ID:** {paper['id']} | **Title:** {paper['title']}\n\n"
            f"**By:** {faculty_name}\n"
            f"**Status:** {paper['status']}\n"
            f"**Reviewer(s):** {assigned_reviewers}"
        )
        if "filepath" in paper:
            with open(paper["filepath"], "rb") as f:
                st.sidebar.download_button("⬇️ Download", f, file_name=paper["filepath"].split("/")[-1], key=f"sidebar_down_{paper['id']}")
        st.sidebar.markdown("---")

def get_papers_for_faculty(username):
    return [p for p in st.session_state.papers if p['faculty_username'] == username]

def get_papers_for_reviewer(username):
    assigned = []
    for paper_id, reviewers in st.session_state.assignments.items():
        if username in reviewers:
            paper = next((p for p in st.session_state.papers if p["id"] == paper_id), None)
            if paper and paper['status'] not in ("Draft",):
                assigned.append(paper)
    return assigned

def save_uploaded_file(uploaded_file, paper_id):
    ext = uploaded_file.name.split('.')[-1]
    filename = f"paper_{paper_id}.{ext}"
    filepath = os.path.join(UPLOAD_DIR, filename)
    with open(filepath, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return filepath

def send_assignment_email(to_email, reviewer_name, paper_title, faculty_name, admin_email="youradmin@email.com"):
    # Replace with actual SMTP for real email sending!
    EMAIL_ADDRESS = "youradmin@email.com"
    EMAIL_PASSWORD = "yourpassword"
    msg = EmailMessage()
    msg["Subject"] = f"Paper Assignment: {paper_title}"
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = to_email
    msg.set_content(
        f"Dear {reviewer_name},\n\n"
        f"You have been assigned to review the paper titled '{paper_title}' submitted by {faculty_name}.\n"
        f"Please login to the portal to download and review the paper.\n\n"
        f"Regards,\nAdmin"
    )
    # For demo, display in Streamlit instead of sending
    st.info(f"""
    [Demo] Would send email:
    **To:** {to_email}
    **Subject:** Paper Assignment: {paper_title}
    **Message:**  
    Dear {reviewer_name},  
    You have been assigned to review the paper titled '{paper_title}' submitted by {faculty_name}.
    """)
    # Uncomment and use actual SMTP server for production:
    # with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
    #     smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
    #     smtp.send_message(msg)

# ----- FACULTY DASHBOARD -----
if st.session_state.role == "faculty":
    st.title("Author Dashboard")
    st.write(f"Welcome, {st.session_state.name}")

    papers = get_papers_for_faculty(st.session_state.username)

    st.subheader("Submit or Update Paper")
    with st.form("paper_upload_form"):
        paper_title = st.text_input("Paper Title")
        uploaded_file = st.file_uploader("Upload your full paper (DOCX or PDF)", type=["pdf", "docx"])
        submit_btn = st.form_submit_button("Submit/Update Paper")

        if submit_btn:
            if not paper_title or not uploaded_file:
                st.warning("Both title and file required.")
            else:
                # If paper with same title exists, update it
                existing = next((p for p in papers if p['title'].lower() == paper_title.lower()), None)
                if existing:
                    filepath = save_uploaded_file(uploaded_file, existing["id"])
                    existing["filepath"] = filepath
                    existing["updated"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                    existing["status"] = "Submitted"
                    st.success("Paper updated and resubmitted!")
                else:
                    new_paper_id = next_paper_id()
                    filepath = save_uploaded_file(uploaded_file, new_paper_id)
                    paper = {
                        "id": new_paper_id,
                        "faculty_username": st.session_state.username,
                        "title": paper_title,
                        "filepath": filepath,
                        "submitted": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "updated": "",
                        "status": "Submitted"
                    }
                    st.session_state.papers.append(paper)
                    st.success("Paper submitted!")

    st.subheader("My Papers and Reviews")
    for paper in papers:
        st.write(f"**Title:** {paper['title']} | **Status:** {paper['status']}")
        if "filepath" in paper:
            with open(paper["filepath"], "rb") as f:
                st.download_button("Download My Paper", f, file_name=paper["filepath"].split("/")[-1])
        my_reviews = [r for r in st.session_state.reviews if r["paper_id"] == paper["id"]]
        if my_reviews:
            for rev in my_reviews:
                st.info(f"Reviewer: {rev['reviewer']}\n"
                        f"Recommendation: {rev['recommendation']}\n"
                        f"Strengths: {rev['strengths']}\n"
                        f"Weaknesses: {rev['weaknesses']}\n"
                        f"Suggestions: {rev['suggestions']}")
        st.write("---")

# ----- REVIEWER DASHBOARD -----
elif st.session_state.role == "reviewer":
    st.title("Reviewer Dashboard")
    st.write(f"Welcome, {st.session_state.name}")

    papers = get_papers_for_reviewer(st.session_state.username)
    st.subheader("Papers Assigned/Available for Review")
    for paper in papers:
        st.write(f"**Title:** {paper['title']}")
        if "filepath" in paper:
            with open(paper["filepath"], "rb") as f:
                st.download_button("Download Paper", f, file_name=paper["filepath"].split("/")[-1], key=f"down_{paper['id']}")
        st.write(f"Status: {paper['status']}")
        st.write("Review this paper:")

        # Show existing review or review form
        review = next((r for r in st.session_state.reviews if r["paper_id"] == paper["id"] and r["reviewer"] == st.session_state.username), None)
        if review:
            st.success(f"You already reviewed this paper: {review['recommendation']}")
        else:
            with st.form(f"review_form_{paper['id']}"):
                recommendation = st.selectbox("Recommendation", RECOMMEND_OPTIONS)
                strengths = st.text_area("Strengths (what is good in this paper?)")
                weaknesses = st.text_area("Weaknesses (what needs improvement?)")
                suggestions = st.text_area("Suggestions for Improvement")
                submitted = st.form_submit_button("Submit Review")
                if submitted:
                    st.session_state.reviews.append({
                        "paper_id": paper["id"],
                        "reviewer": st.session_state.username,
                        "recommendation": recommendation,
                        "strengths": strengths,
                        "weaknesses": weaknesses,
                        "suggestions": suggestions,
                        "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                    })
                    for p in st.session_state.papers:
                        if p["id"] == paper["id"]:
                            if recommendation == "Accept":
                                p["status"] = "Accepted"
                            elif recommendation == "Minor Revision":
                                p["status"] = "Minor Revision Required"
                            elif recommendation == "Major Revision":
                                p["status"] = "Major Revision Required"
                            elif recommendation == "Reject":
                                p["status"] = "Rejected"
                    st.success("Review submitted!")
                    st.experimental_rerun()
        st.write("---")

# ----- ADMIN DASHBOARD -----
elif st.session_state.role == "admin":
    st.title("Admin Dashboard")

    # --- Reviewer Account Creation/Deletion Section ---
    st.subheader("Create/Delete Reviewer Account (Max 6)")
    existing_reviewers = [uname for uname, uinfo in users.items() if uinfo['role'] == 'reviewer']
    if len(existing_reviewers) < 6:
        with st.form("create_reviewer_form"):
            new_reviewer_username = st.text_input("Reviewer Username")
            new_reviewer_password = st.text_input("Reviewer Password", type="password")
            new_reviewer_name = st.text_input("Reviewer Full Name")
            reviewer_submit = st.form_submit_button("Create Reviewer")
            if reviewer_submit:
                if not new_reviewer_username or not new_reviewer_password or not new_reviewer_name:
                    st.warning("All fields are required!")
                elif new_reviewer_username in users:
                    st.warning("Username already exists.")
                else:
                    users[new_reviewer_username] = {
                        "password": new_reviewer_password,
                        "role": "reviewer",
                        "name": new_reviewer_name
                    }
                    st.success(f"Reviewer {new_reviewer_name} created with username '{new_reviewer_username}'.")
    else:
        st.info("Maximum of 6 reviewer accounts reached. Delete a reviewer to add more.")

    st.write("**Existing Reviewers:**")
    for uname in existing_reviewers:
        st.write(f"- {uname} ({users[uname]['name']})")
    if st.button("Delete a Reviewer Account"):
        reviewer_to_delete = st.selectbox("Select reviewer to delete", existing_reviewers, key="del_reviewer_select")
        if reviewer_to_delete:
            del users[reviewer_to_delete]
            # Also remove assignments
            for pid in st.session_state.assignments:
                if reviewer_to_delete in st.session_state.assignments[pid]:
                    st.session_state.assignments[pid].remove(reviewer_to_delete)
            st.success(f"Reviewer '{reviewer_to_delete}' deleted.")
            st.experimental_rerun()

    # --- Assign Reviewer to Paper Section ---
    st.subheader("Assign Reviewers to Papers")
    paper_titles = [f"{p['id']} - {p['title']}" for p in st.session_state.papers]
    if paper_titles and existing_reviewers:
        selected_paper_str = st.selectbox("Select Paper", paper_titles, key="assign_paper_select")
        selected_reviewer = st.selectbox("Select Reviewer", existing_reviewers, key="assign_reviewer_select")
        assign_btn = st.button("Assign Reviewer")
        if assign_btn:
            selected_paper_id = int(selected_paper_str.split(" - ")[0])
            st.session_state.assignments.setdefault(selected_paper_id, [])
            if selected_reviewer not in st.session_state.assignments[selected_paper_id]:
                st.session_state.assignments[selected_paper_id].append(selected_reviewer)
                # Optional: email to reviewer
                paper = next(p for p in st.session_state.papers if p["id"] == selected_paper_id)
                faculty_name = users[paper["faculty_username"]]["name"]
                send_assignment_email(
                    to_email=f"{selected_reviewer}@example.com",
                    reviewer_name=users[selected_reviewer]["name"],
                    paper_title=paper["title"],
                    faculty_name=faculty_name
                )
                st.success(f"Assigned {users[selected_reviewer]['name']} to review '{paper['title']}'.")
            else:
                st.info("Reviewer already assigned to this paper.")

    # --- Paper and Review Status Dashboard (main page for admin) ---
    st.subheader("All Faculty Papers and Status")
    for paper in st.session_state.papers:
        faculty_name = users[paper["faculty_username"]]["name"]
        st.write(f"**Title:** {paper['title']} | **By:** {faculty_name} | **Status:** {paper['status']}")
        reviewers = st.session_state.assignments.get(paper['id'], [])
        if reviewers:
            st.write(f"Assigned Reviewer(s): {', '.join([users[r]['name'] for r in reviewers])}")
        if "filepath" in paper:
            with open(paper["filepath"], "rb") as f:
                st.download_button("Download Paper", f, file_name=paper["filepath"].split("/")[-1], key=f"down_{paper['id']}")
        reviews = [r for r in st.session_state.reviews if r["paper_id"] == paper["id"]]
        if reviews:
            for rev in reviews:
                st.info(f"Reviewer: {rev['reviewer']}\n"
                        f"Recommendation: {rev['recommendation']}\n"
                        f"Strengths: {rev['strengths']}\n"
                        f"Weaknesses: {rev['weaknesses']}\n"
                        f"Suggestions: {rev['suggestions']}")
        st.write("---")
