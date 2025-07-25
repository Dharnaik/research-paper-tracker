import streamlit as st
from datetime import datetime
import sqlite3

# ---------- Database Setup ----------
conn = sqlite3.connect('faculty_research.db', check_same_thread=False)
c = conn.cursor()
c.execute('''
    CREATE TABLE IF NOT EXISTS papers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        faculty_name TEXT,
        title TEXT,
        abstract TEXT,
        content TEXT,
        status TEXT,
        created_at TEXT,
        last_updated TEXT
    )
''')
c.execute('''
    CREATE TABLE IF NOT EXISTS reviews (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        paper_id INTEGER,
        reviewer TEXT,
        comments TEXT,
        status TEXT,
        reviewed_at TEXT
    )
''')
conn.commit()

# ---------- Helper Functions ----------
def add_paper(faculty_name, title, abstract, content, status):
    now = datetime.now().isoformat()
    c.execute('INSERT INTO papers (faculty_name, title, abstract, content, status, created_at, last_updated) VALUES (?, ?, ?, ?, ?, ?, ?)',
              (faculty_name, title, abstract, content, status, now, now))
    conn.commit()

def get_papers():
    c.execute('SELECT * FROM papers')
    return c.fetchall()

def update_paper_status(paper_id, status):
    now = datetime.now().isoformat()
    c.execute('UPDATE papers SET status=?, last_updated=? WHERE id=?', (status, now, paper_id))
    conn.commit()

def add_review(paper_id, reviewer, comments, status):
    now = datetime.now().isoformat()
    c.execute('INSERT INTO reviews (paper_id, reviewer, comments, status, reviewed_at) VALUES (?, ?, ?, ?, ?)',
              (paper_id, reviewer, comments, status, now))
    conn.commit()

def get_reviews(paper_id):
    c.execute('SELECT * FROM reviews WHERE paper_id=?', (paper_id,))
    return c.fetchall()

# ---------- Streamlit UI ----------
st.set_page_config(page_title="Faculty Research Paper Tracker")

st.title("Faculty Research Paper Writing & Tracking App")

menu = st.sidebar.selectbox("Menu", ["Create New Paper", "View My Papers", "Review Papers"])

if menu == "Create New Paper":
    st.header("Start a New Research Paper")
    faculty_name = st.text_input("Faculty Name")
    title = st.text_input("Paper Title")
    abstract = st.text_area("Abstract")
    content = st.text_area("Paper Content", height=300)
    if st.button("Save Paper"):
        add_paper(faculty_name, title, abstract, content, "Draft")
        st.success("Paper saved as draft!")

elif menu == "View My Papers":
    st.header("My Research Papers")
    papers = get_papers()
    for paper in papers:
        st.subheader(paper[2])
        st.write(f"Faculty: {paper[1]}, Status: {paper[5]}, Last Updated: {paper[7][:19]}")
        with st.expander("View/Edit Paper"):
            st.write("**Abstract**")
            st.write(paper[3])
            st.write("**Content**")
            st.write(paper[4])
            status = st.selectbox("Update Status", ["Draft", "In Progress", "Under Review", "Completed", "Submitted", "Accepted", "Rejected"], index=["Draft", "In Progress", "Under Review", "Completed", "Submitted", "Accepted", "Rejected"].index(paper[5]))
            if st.button("Update Status", key=paper[0]):
                update_paper_status(paper[0], status)
                st.success("Status updated.")

elif menu == "Review Papers":
    st.header("Review Research Papers")
    papers = get_papers()
    for paper in papers:
        st.subheader(paper[2])
        st.write(f"Faculty: {paper[1]}, Status: {paper[5]}")
        with st.expander("Review/Comments"):
            reviews = get_reviews(paper[0])
            st.write("**Past Reviews:**")
            for review in reviews:
                st.write(f"Reviewer: {review[2]}, Status: {review[4]}, Comments: {review[3]}")
            reviewer = st.text_input("Your Name", key=f"rev_{paper[0]}")
            comments = st.text_area("Your Review/Comments", key=f"comments_{paper[0]}")
            review_status = st.selectbox("Set Review Status", ["Needs Revision", "Accepted", "Rejected"], key=f"status_{paper[0]}")
            if st.button("Submit Review", key=f"submit_{paper[0]}"):
                add_review(paper[0], reviewer, comments, review_status)
                st.success("Review submitted!")


