import streamlit as st
from streamlit_quill import st_quill
import datetime
import docx
import re
import base64
import pandas as pd
from io import BytesIO

# --- USERS ---
users = {
    "admin": {"password": "adminpass", "role": "admin", "name": "Admin"},
    "amit.dharnaik": {"password": "pass7", "role": "faculty", "name": "Prof. Dr. Amit S. Dharnaik"},
    # Add more users as needed
}

# --- SECTION PATTERNS FOR FUZZY SPLIT ---
SECTION_PATTERNS = {
    "title": r"^(title)[:\s]*$",
    "abstract": r"^(abstract)[:\s]*$",
    "introduction": r"^(introduction|intro)[:\s]*$",
    "materials and methods": r"^(materials? and methods?|methodology|methods?)[:\s]*$",
    "results and discussion": r"^(results and discussion|results & discussion|result and discussion|results|discussion|findings)[:\s]*$",
    "conclusion": r"^(conclusion[s]?)[:\s]*$",
    "references": r"^((\d+\.?|[ivxlc]+\.)?\s*)?(references|bibliography)[:\s]*$",
}
SECTION_HEADERS = list(SECTION_PATTERNS.keys())

def fuzzy_section_match(text):
    text_lc = text.strip().lower()
    for sec, pattern in SECTION_PATTERNS.items():
        if re.match(pattern, text_lc):
            return sec
    return None

# --- NEW: Section splitting with automatic image extraction/tagging ---
def split_docx_sections_and_images(docx_file):
    doc = docx.Document(docx_file)
    text_sections = {}
    current_section = "title"
    buffer = []
    image_bytes_list = []
    para_images = {}
    img_counter = 1

    def flush_buffer():
        nonlocal buffer, current_section
        if buffer:
            joined = "\n".join(buffer).strip()
            if joined:
                if current_section not in text_sections:
                    text_sections[current_section] = ""
                text_sections[current_section] += joined + "\n"
            buffer.clear()

    for para_idx, para in enumerate(doc.paragraphs):
        para_text = para.text.strip()
        found_img = False
        img_this_para = []
        for run in para.runs:
            # This is the robust way to check for images in a run:
            if "graphic" in run._element.xml:
                # For each relationship in the part (usually only one per image)
                for rel in run.part.rels.values():
                    if "image" in rel.target_ref:
                        image_bytes = rel.target_part.blob
                        if image_bytes not in image_bytes_list:
                            image_bytes_list.append(image_bytes)
                            img_num = len(image_bytes_list)
                        else:
                            img_num = image_bytes_list.index(image_bytes) + 1
                        img_this_para.append(img_num)
                        found_img = True
        found_header = fuzzy_section_match(para_text)
        if found_header:
            flush_buffer()
            current_section = found_header
            if re.match(SECTION_PATTERNS[found_header], para_text.strip().lower()):
                para_text = ""  # skip the heading line
            else:
                para_text = re.sub(SECTION_PATTERNS[found_header], '', para_text, flags=re.I).strip()
        # If image(s) in paragraph and NO text, just insert tag(s)
        if found_img and not para_text:
            for img_num in img_this_para:
                buffer.append(f'{{image{img_num}}}')
            continue
        # If text and image(s), insert tags at the end of the paragraph
        if para_text:
            buffer.append(para_text)
            for img_num in img_this_para:
                buffer.append(f'{{image{img_num}}}')
    flush_buffer()
    return text_sections, image_bytes_list

# --- SESSION STATE INIT ---
if 'papers' not in st.session_state: st.session_state.papers = []
if 'edit_paper_id' not in st.session_state: st.session_state.edit_paper_id = None
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ''
    st.session_state.role = ''
    st.session_state.name = ''
if "paper_attachments" not in st.session_state:
    st.session_state.paper_attachments = {}

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
        else:
            st.error("Invalid username or password.")

def logout():
    st.session_state.logged_in = False
    st.session_state.username = ''
    st.session_state.role = ''
    st.session_state.name = ''
    st.session_state.edit_paper_id = None
    st.experimental_rerun()
    st.stop()

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

def get_papers_for_faculty(username):
    return [p for p in st.session_state.papers if p['faculty_username'] == username]

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

# --- Custom CSS for fonts ---
st.markdown("""
    <style>
    .stApp h4 {
        font-size: 22px !important;
        font-weight: bold !important;
        font-family: 'Times New Roman', serif !important;
    }
    .stApp .ql-editor {
        font-size: 15px;
        font-family: 'Times New Roman', serif;
    }
    </style>
""", unsafe_allow_html=True)

if not st.session_state.logged_in:
    login()
    st.stop()

st.sidebar.write(f"Logged in as: {st.session_state.name} ({st.session_state.role})")
if st.sidebar.button("Logout"):
    logout()

# ----- FACULTY DASHBOARD -----
if st.session_state.role == "faculty":
    st.title("Faculty Dashboard")
    st.write(f"Welcome, {st.session_state.name}")

    st.info("**Tip:** Upload DOCX with images and/or text. Images will be auto-extracted and placed in the section content as `{image1}`, `{image2}`, etc. To include more images or tables, upload them below and use `{imageN}`, `{tableN}` in your text.")

    papers = get_papers_for_faculty(st.session_state.username)

    # If author just logged in and has no papers, auto-start a new paper
    if not papers and st.session_state.edit_paper_id is None:
        new_paper = {
            "id": next_paper_id(),
            "faculty_username": st.session_state.username,
            "sections": {h:"" for h in SECTION_HEADERS},
            "status": "Draft",
            "history": []
        }
        st.session_state.papers.append(new_paper)
        st.session_state.edit_paper_id = new_paper['id']

    # If author just started new paper (from button), show editor
    if st.session_state.edit_paper_id is not None:
        paper = next(p for p in st.session_state.papers if p['id'] == st.session_state.edit_paper_id)
        st.header(f"Editing Paper: {paper['sections'].get('title','(untitled)')}")

        attachments = get_attachment_dict(paper['id'])

        uploaded_docx = st.file_uploader("Upload DOCX to Auto-Split/Update Sections (text and images)", type=["docx"])
        if uploaded_docx:
            new_sections, image_bytes_list = split_docx_sections_and_images(uploaded_docx)
            # Save images to attachments for this paper:
            for img_bytes in image_bytes_list:
                img_b64 = base64.b64encode(img_bytes).decode()
                if img_b64 not in attachments["images"]:
                    attachments["images"].append(img_b64)
            updated = versioned_update(paper, new_sections, who=st.session_state.name, note="DOCX upload")
            if updated:
                st.success("Sections updated from DOCX. All changes tracked below (and images auto-inserted).")
            else:
                st.info("No changes detected from upload.")

        st.markdown("#### Attach Images and Tables (for reviewer to see and comment)")
        uploaded_images = st.file_uploader("Upload Image(s)", type=["png", "jpg", "jpeg"], accept_multiple_files=True, key=f"img_{paper['id']}")
        if uploaded_images:
            add_uploaded_images(uploaded_images, attachments)

        uploaded_excel = st.file_uploader("Upload Excel for Table/Graph", type=["xls", "xlsx"], key=f"excel_{paper['id']}")
        if uploaded_excel:
            df = add_uploaded_table_from_excel(uploaded_excel, attachments)
            st.write("Excel Data Table Preview:")
            st.dataframe(df)
            st.write("Quick Bar Graph:")
            st.bar_chart(df.select_dtypes(include=['number']))

        n_rows = st.number_input("Rows", min_value=1, max_value=10, value=2, key=f"create_table_rows_{paper['id']}")
        n_cols = st.number_input("Columns", min_value=1, max_value=10, value=2, key=f"create_table_cols_{paper['id']}")
        if st.button("Create Table", key=f"create_table_{paper['id']}"):
            add_custom_table(int(n_rows), int(n_cols), attachments)
            st.success("Table created and attached!")

        st.markdown("---")
        if attachments["images"]:
            st.write("Attached Images (auto and manual):")
            for idx, img_b64 in enumerate(attachments["images"]):
                st.image(BytesIO(base64.b64decode(img_b64)), caption=f"image{idx+1}")
        if attachments["tables"]:
            st.write("Attached Tables:")
            for t_idx, table_html in enumerate(attachments["tables"]):
                st.markdown(table_html, unsafe_allow_html=True)
        st.markdown("---")

        with st.form("edit_sections_form"):
            changed = False
            for section in SECTION_HEADERS:
                st.markdown(f"#### {section.title()}")
                # Replace placeholders for display
                section_html = replace_placeholders_with_attachments(paper["sections"].get(section, ""), attachments)
                val = st_quill(
                    key=f"q_{section}_{paper['id']}",
                    value=paper["sections"].get(section, ""),
                    html=True
                )
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
                # Show images/tables in context after each section
                if section_html.strip():
                    st.markdown("---")
                    st.markdown("##### Preview with images/tables:")
                    st.markdown(replace_placeholders_with_attachments(section_html, attachments), unsafe_allow_html=True)
            if st.form_submit_button("Save Changes") and changed:
                st.success("Changes saved and tracked.")

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

    else:
        st.subheader("My Papers")
        for paper in papers:
            col1, col2, col3 = st.columns([6,2,2])
            with col1:
                st.markdown(f"**ID:** {paper['id']} | **Title:** {paper['sections'].get('title','(untitled)')} | Status: {paper['status']}")
            with col2:
                if st.button("Edit", key=f"edit_{paper['id']}"):
                    st.session_state.edit_paper_id = paper['id']
            with col3:
                if st.button("Delete", key=f"delete_{paper['id']}"):
                    st.session_state.papers = [p for p in st.session_state.papers if p['id'] != paper['id']]
                    if paper['id'] == st.session_state.edit_paper_id:
                        st.session_state.edit_paper_id = None
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
