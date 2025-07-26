import streamlit as st
from streamlit_quill import st_quill
import pandas as pd
import datetime
import docx

# --- USERS, SECTION_HEADERS etc (same as before) ---

# --- SESSION STATE INIT ---
if 'papers' not in st.session_state:
    st.session_state.papers = []
if 'edit_paper_id' not in st.session_state:
    st.session_state.edit_paper_id = None
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ''
    st.session_state.role = ''
    st.session_state.name = ''
if "just_started_paper" not in st.session_state:
    st.session_state.just_started_paper = False
if "just_edit_paper" not in st.session_state:
    st.session_state.just_edit_paper = False
if "just_delete_paper" not in st.session_state:
    st.session_state.just_delete_paper = False
if "just_logout" not in st.session_state:
    st.session_state.just_logout = False

# ---- SAFE RERUN HANDLER AT TOP ----
if st.session_state.just_started_paper:
    st.session_state.just_started_paper = False
    st.experimental_rerun()
    st.stop()
if st.session_state.just_edit_paper:
    st.session_state.just_edit_paper = False
    st.experimental_rerun()
    st.stop()
if st.session_state.just_delete_paper:
    st.session_state.just_delete_paper = False
    st.experimental_rerun()
    st.stop()
if st.session_state.just_logout:
    st.session_state.just_logout = False
    st.experimental_rerun()
    st.stop()

# --- login/logout as before ---

def login():
    st.title("Faculty Research Paper Portal - Login")
    username = st.text_input("Username").strip()
    password = st.text_input("Password", type="password")
    st.write("DEBUG - You entered:", repr(username))
    if st.button("Login"):
        user = users.get(username)
        if user and user["password"] == password:
            st.session_state.logged_in = True
            st.session_state.username = username
            st.session_state.role = user["role"]
            st.session_state.name = user["name"]
            st.success(f"Welcome, {user['name']} ({user['role']})")
        else:
            st.error("Invalid username or password.")

def logout():
    st.session_state.logged_in = False
    st.session_state.username = ''
    st.session_state.role = ''
    st.session_state.name = ''
    st.session_state.just_logout = True

if not st.session_state.logged_in:
    login()
    st.stop()

# --- SIDEBAR ---
st.sidebar.write(f"Logged in as: {st.session_state.name} ({st.session_state.role})")
if st.sidebar.button("Logout"):
    logout()
    st.stop()

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
                st.session_state.just_edit_paper = True
                st.stop()
        with col3:
            if st.button("Delete", key=f"delete_{paper['id']}"):
                st.session_state.papers = [p for p in st.session_state.papers if p['id'] != paper['id']]
                st.session_state.just_delete_paper = True
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
        st.session_state.just_started_paper = True
        st.stop()

    # ----- Edit/view a paper -----
    if st.session_state.edit_paper_id is not None:
        paper = next(p for p in papers if p['id'] == st.session_state.edit_paper_id)
        st.header(f"Editing Paper: {paper['sections'].get('title','(untitled)')}")

        # ... rest of your code unchanged ...
