import streamlit as st
from streamlit_quill import st_quill
import pandas as pd
import base64
from io import BytesIO

# --- USERS ---
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

# --- IN-MEMORY DATABASES ---
if 'papers' not in st.session_state:
    st.session_state.papers = []
if 'reviews' not in st.session_state:
    st.session_state.reviews = []
if 'reviewers' not in st.session_state:
    st.session_state.reviewers = {}
if "paper_attachments" not in st.session_state:
    st.session_state.paper_attachments = {}

# --- AUTH LOGIC ---
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

# --- SIDEBAR ---
st.sidebar.write(f"Logged in as: {st.session_state.name} ({st.session_state.role})")
if st.sidebar.button("Logout"):
    logout()

# --- FIXED FONT/SIZE STYLING ---
st.markdown("""
    <style>
        .stApp h1 {
            font-family: 'Times New Roman', serif !important;
            font-size: 18pt !important;
            font-weight: bold !important;
            text-align: center;
        }
        .stApp h2, .stApp h3 {
            font-family: 'Times New Roman', serif !important;
            font-size: 14pt !important;
            font-weight: bold !important;
        }
        .stApp p, .stApp li, .stApp div, .stApp span, .stApp label, .stApp input, .stApp textarea {
            font-family: 'Times New Roman', serif !important;
            font-size: 12pt !important;
        }
        .abstract-text {
            font-style: italic !important;
            font-size: 11pt !important;
        }
    </style>
""", unsafe_allow_html=True)

# --- UTILS ---
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

def get_attachment_dict(paper_id):
    if paper_id not in st.session_state.paper_attachments:
        st.session_state.paper_attachments[paper_id] = {"images": [], "tables": []}
    return st.session_state.paper_attachments[paper_id]

def add_uploaded_images(uploaded_images, attachments):
    for img in uploaded_images:
        img.seek(0)
        img_bytes = img.read()
        img_b64 = base64.b64encode(img_bytes).decode()
        if img_b64 not in attachments["images"]:
            attachments["images"].append(img_b64)

def add_uploaded_table_from_excel(uploaded_excel, attachments):
    df = pd.read_excel(uploaded_excel)
    html = df.to_html(index=False, border=1)
    if html not in attachments["tables"]:
        attachments["tables"].append(html)
    return df

def add_custom_table(n_rows, n_cols, attachments):
    df = pd.DataFrame([[""] * n_cols for _ in range(n_rows)],
                      columns=[f"Col{i+1}" for i in range(n_cols)])
    html = df.to_html(index=False, border=1)
    attachments["tables"].append(html)

def replace_placeholders_with_attachments(content_html, attachments):
    for idx, img_b64 in enumerate(attachments.get("images", [])):
        img_tag = f'<img src="data:image/png;base64,{img_b64}" style="max-width:100%;">'
        content_html = content_html.replace(f'{{image{idx+1}}}', img_tag)
    for idx, table_html in enumerate(attachments.get("tables", [])):
        content_html = content_html.replace(f'{{table{idx+1}}}', table_html)
    return content_html

# --- ADMIN DASHBOARD ---
if st.session_state.role == "admin":
    st.title("Admin Dashboard")
    st.subheader("All Papers")
    if st.session_state.papers:
        for paper in st.session_state.papers:
            st.markdown(f"**ID:** {paper['id']} | **Title:** {paper['title']} | **By:** {users[paper['faculty_username']]['name']}")
            st.write(f"Status: {paper['status']}")
            st.markdown(f'<div class="abstract-text">Abstract: {paper["abstract"]}</div>', unsafe_allow_html=True)
            attachments = get_attachment_dict(paper['id'])
            display_html = replace_placeholders_with_attachments(paper['content'], attachments)
            st.markdown(display_html, unsafe_allow_html=True)
            left_imgs = len([t for t in range(len(attachments["images"])) if f'{{image{t+1}}}' not in paper['content']])
            left_tbls = len([t for t in range(len(attachments["tables"])) if f'{{table{t+1}}}' not in paper['content']])
            if left_imgs or left_tbls:
                st.markdown("---")
            for idx, img_b64 in enumerate(attachments["images"]):
                if f'{{image{idx+1}}}' not in paper['content']:
                    st.write(f"Unplaced Image {idx+1}:")
                    st.image(BytesIO(base64.b64decode(img_b64)), caption=f"image{idx+1}")
            for idx, table_html in enumerate(attachments["tables"]):
                if f'{{table{idx+1}}}' not in paper['content']:
                    st.write(f"Unplaced Table {idx+1}:")
                    st.markdown(table_html, unsafe_allow_html=True)
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

# --- FACULTY DASHBOARD ---
elif st.session_state.role == "faculty":
    st.title("Faculty Dashboard")
    st.write(f"Welcome, {st.session_state.name}")

    if 'edit_paper_id' not in st.session_state:
        st.session_state.edit_paper_id = None

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
                if paper['id'] in st.session_state.paper_attachments:
                    del st.session_state.paper_attachments[paper['id']]
                st.experimental_rerun()
        st.markdown("---")

    if st.button("Start New Paper"):
        st.session_state.edit_paper_id = None

    # --- Attachments UI ---
    st.subheader("Attach to This Paper")
    if st.session_state.edit_paper_id is not None:
        working_paper_id = st.session_state.edit_paper_id
    else:
        working_paper_id = -1
    attachments = get_attachment_dict(working_paper_id)
    st.info("To insert an image or table in your content, use tags like `{image1}`, `{table1}` at the desired place in your text below.")

    # Images
    uploaded_images = st.file_uploader("Upload Image(s)", type=["png", "jpg", "jpeg"], accept_multiple_files=True, key=f"img_{working_paper_id}")
    if uploaded_images:
        add_uploaded_images(uploaded_images, attachments)

    # Excel table
    uploaded_excel = st.file_uploader("Upload Excel for Table/Graph", type=["xls", "xlsx"], key=f"excel_{working_paper_id}")
    if uploaded_excel:
        df = add_uploaded_table_from_excel(uploaded_excel, attachments)
        st.write("Excel Data Table Preview:")
        st.dataframe(df)
        st.write("Quick Bar Graph:")
        st.bar_chart(df.select_dtypes(include=['number']))

    # Create custom table
    n_rows = st.number_input("Rows", min_value=1, max_value=10, value=2, key=f"create_table_rows_{working_paper_id}")
    n_cols = st.number_input("Columns", min_value=1, max_value=10, value=2, key=f"create_table_cols_{working_paper_id}")
    if st.button("Create Table", key=f"create_table_{working_paper_id}"):
        add_custom_table(int(n_rows), int(n_cols), attachments)
        st.success("Table created and attached!")

    st.markdown("---")
    if attachments["images"]:
        st.write("Attached Images:")
        for idx, img_b64 in enumerate(attachments["images"]):
            st.image(BytesIO(base64.b64decode(img_b64)), caption=f"image{idx+1}")
    if attachments["tables"]:
        st.write("Attached Tables:")
        for t_idx, table_html in enumerate(attachments["tables"]):
            st.markdown(table_html, unsafe_allow_html=True)
    st.markdown("---")

    # --- Paper Form (for new or editing existing) ---
    st.subheader("Write Paper")
    if st.session_state.edit_paper_id is not None:
        paper = next(p for p in papers if p['id'] == st.session_state.edit_paper_id)
        title = st.text_input("Paper Title", value=paper['title'])
        abstract = st.text_area("Abstract", value=paper['abstract'])
        content = st_quill(key=f"content_quill_edit_{paper['id']}", value=paper['content'], html=True)
        submit_label = "Update Paper"
    else:
        title = st.text_input("Paper Title")
        abstract = st.text_area("Abstract")
        content = st_quill(key="content_quill_new", html=True)
        submit_label = "Submit Paper"

    if st.button(submit_label):
        if not title or not content:
            st.warning("Title and content required.")
        else:
            if st.session_state.edit_paper_id is not None:
                for p in st.session_state.papers:
                    if p['id'] == st.session_state.edit_paper_id:
                        p['title'] = title
                        p['abstract'] = abstract
                        p['content'] = content
                        if -1 in st.session_state.paper_attachments and not st.session_state.paper_attachments[p['id']]["images"] and not st.session_state.paper_attachments[p['id']]["tables"]:
                            st.session_state.paper_attachments[p['id']] = st.session_state.paper_attachments[-1]
                            del st.session_state.paper_attachments[-1]
                        st.success("Paper updated!")
                        break
                st.session_state.edit_paper_id = None
            else:
                new_paper_id = next_paper_id()
                new_paper = {
                    "id": new_paper_id,
                    "faculty_username": st.session_state.username,
                    "title": title,
                    "abstract": abstract,
                    "content": content,
                    "status": "Draft"
                }
                st.session_state.papers.append(new_paper)
                if -1 in st.session_state.paper_attachments:
                    st.session_state.paper_attachments[new_paper_id] = st.session_state.paper_attachments[-1]
                    del st.session_state.paper_attachments[-1]
                st.success(f"Paper '{title}' submitted!")
            st.experimental_rerun()

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

# --- REVIEWER DASHBOARD ---
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
            attachments = get_attachment_dict(paper['id'])
            display_html = replace_placeholders_with_attachments(paper['content'], attachments)
            st.markdown(display_html, unsafe_allow_html=True)
            left_imgs = len([t for t in range(len(attachments["images"])) if f'{{image{t+1}}}' not in paper['content']])
            left_tbls = len([t for t in range(len(attachments["tables"])) if f'{{table{t+1}}}' not in paper['content']])
            if left_imgs or left_tbls:
                st.markdown("---")
            for idx, img_b64 in enumerate(attachments["images"]):
                if f'{{image{idx+1}}}' not in paper['content']:
                    st.write(f"Unplaced Image {idx+1}:")
                    st.image(BytesIO(base64.b64decode(img_b64)), caption=f"image{idx+1}")
            for idx, table_html in enumerate(attachments["tables"]):
                if f'{{table{idx+1}}}' not in paper['content']:
                    st.write(f"Unplaced Table {idx+1}:")
                    st.markdown(table_html, unsafe_allow_html=True)
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
