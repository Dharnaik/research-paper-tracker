import streamlit as st
from streamlit_quill import st_quill
import datetime
import docx

# --- USERS ---
users = {
    "admin": {"password": "adminpass", "role": "admin", "name": "Admin"},
    "amit.dharnaik": {"password": "pass7", "role": "faculty", "name": "Prof. Dr. Amit S. Dharnaik"},
    # ... other users
}

SECTION_HEADERS = [
    "title", "abstract", "introduction", "methods", "results", "discussion", "conclusion", "references"
]

# --- SESSION STATE INIT (MUST BE FIRST) ---
if 'papers' not in st.session_state:
    st.session_state.papers = []
if 'edit_paper_id' not in st.session_state:
    st.session_state.edit_paper_id = None
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ''
    st.session_state.role = ''
    st.session_state.name = ''
if 'rerun_flag' not in st.session_state:
    st.session_state.rerun_flag = None
if 'ready' not in st.session_state:
    st.session_state.ready = True  # Only set this after session state has initialized once!

# ---- SAFE RERUN HANDLER (GUARDED) ----
# Only allow rerun after session state is definitely initialized!
if st.session_state.ready and st.session_state.rerun_flag:
    flag = st.session_state.rerun_flag
    st.session_state.rerun_flag = None
    st.experimental_rerun()
    st.stop()

# ---- Rest of your functions (as before) ----

def split_docx_sections(docx_file):
    doc = docx.Document(docx_file)
    text_sections = {}
    current_section = "title"
    text_sections[current_section] = ""
    for para in doc.paragraphs:
        para_text = para.text.strip()
        if not para_text:
            continue
        found_header = None
        for h in SECTION_HEADERS:
            if para_text.lower().startswith(h):
                found_header = h
                break
        if found_header:
            current_section = found_header
            if current_section not in text_sections:
                text_sections[current_section] = ""
            if para_text.lower() == found_header:
                continue
            else:
                para_text = para_text[len(found_header):].strip()
        if current_section not in text_sections:
            text_sections[current_section] = ""
        if para_text:
            text_sections[current_section] += para_text + "\n"
    return text_sections

def versioned_update(paper, new_sections, who="Author", note="DOCX upload"):
    updated = False
    for section, new_content in new_sections.items():
        old_content = paper['sections'].get(section, "")
        if new_content.strip() != old_content.strip():
            paper['history'].append({
                "who": who,
                "when": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "section": section,
                "old": old_content,
                "new": new_content,
                "note": note
            })
            paper['sections'][section] = new_content
            updated = True
    return updated

def next_paper_id():
    if st.session_state.papers:
        return max(p['id'] for p in st.session_state.papers) + 1
    else:
        return 1

def login():
    st.title("Faculty Research Paper Portal - Login")
    username = st.text_input("Username").strip()
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        user = users.get(username)
        if user and user["password"] == password:
            st.session_state.logged_in = True
            st.session_state.username = username
            st.session_state.role = user["role"]
            st.session_state.name = user["name"]
            st.session_state.rerun_flag = "login"
            st.stop()
        else:
            st.error("Invalid username or password.")

def logout():
    st.session_state.logged_in = False
    st.session_state.username = ''
    st.session_state.role = ''
    st.session_state.name = ''
    st.session_state.edit_paper_id = None
    st.session_state.rerun_flag = "logout"
    st.stop()

if not st.session_state.logged_in:
    login()
    st.stop()

# --- SIDEBAR ---
st.sidebar.write(f"Logged in as: {st.session_state.name} ({st.session_state.role})")
if st.sidebar.button("Logout"):
    logout()

# --- FACULTY DASHBOARD ---
if st.session_state.role == "faculty":
    st.title("Faculty Dashboard")
    st.write(f"Welcome, {st.session_state.name}")

    def get_papers_for_faculty(username):
        return [p for p in st.session_state.papers if p['faculty_username'] == username]

    papers = get_papers_for_faculty(st.session_state.username)
    st.subheader("My Papers")
    for paper in papers:
        col1, col2, col3 = st.columns([6,2,2])
        with col1:
            st.markdown(f"**ID:** {paper['id']} | **Title:** {paper['sections'].get('title','(untitled)')} | Status: {paper['status']}")
        with col2:
            if st.button("Edit", key=f"edit_{paper['id']}"):
                st.session_state.edit_paper_id = paper['id']
                st.session_state.rerun_flag = "edit"
                st.stop()
        with col3:
            if st.button("Delete", key=f"delete_{paper['id']}"):
                st.session_state.papers = [p for p in st.session_state.papers if p['id'] != paper['id']]
                st.session_state.rerun_flag = "delete"
                st.stop()
        st.markdown("---")

    if st.button("Start New Paper"):
        new_paper = {
            "id": next_paper_id(),
            "faculty_username": st.session_state.username,
            "sections": {h:"" for h in SECTION_HEADERS},
            "status": "Draft",
            "history": []
        }
        st.session_state.papers.append(new_paper)
        st.session_state.edit_paper_id = new_paper['id']
        st.session_state.rerun_flag = "start"
        st.stop()

    # ----- Edit/view a paper -----
    if st.session_state.edit_paper_id is not None:
        paper = next(p for p in papers if p['id'] == st.session_state.edit_paper_id)
        st.header(f"Editing Paper: {paper['sections'].get('title','(untitled)')}")

        # Upload DOCX for bulk update
        uploaded_docx = st.file_uploader("Upload DOCX to Auto-Split/Update Sections", type=["docx"])
        if uploaded_docx:
            new_sections = split_docx_sections(uploaded_docx)
            updated = versioned_update(paper, new_sections, who=st.session_state.name, note="DOCX upload")
            if updated:
                st.success("Sections updated from DOCX. All changes tracked below.")
            else:
                st.info("No changes detected from upload.")

        # Edit each section manually (version tracked)
        with st.form("edit_sections_form"):
            changed = False
            for section in SECTION_HEADERS:
                val = st_quill(key=f"q_{section}_{paper['id']}", value=paper["sections"].get(section, ""), html=True)
                if val != paper["sections"].get(section, ""):
                    paper["history"].append({
                        "who": st.session_state.name,
                        "when": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "section": section,
                        "old": paper["sections"][section],
                        "new": val,
                        "note": "Manual edit"
                    })
                    paper["sections"][section] = val
                    changed = True
            if st.form_submit_button("Save Changes") and changed:
                st.success("Changes saved and tracked.")
                st.session_state.rerun_flag = "save"
                st.stop()

        # Show change history
        st.markdown("### Change History")
        if paper["history"]:
            for h in reversed(paper["history"]):
                with st.expander(f"{h['when']} - {h['section'].title()} - {h['note']}"):
                    st.write(f"Who: {h['who']}")
                    st.write(f"Old Value:\n{h['old']}")
                    st.write(f"New Value:\n{h['new']}")
        else:
            st.write("No changes yet.")

        if st.button("Back to My Papers"):
            st.session_state.edit_paper_id = None
            st.session_state.rerun_flag = "back"
            st.stop()
