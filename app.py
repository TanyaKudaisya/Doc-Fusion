import os
import streamlit as st
import subprocess
import sys
import asyncio

from pymilvus import MilvusClient
from automation import PDFToMilvusAutomation

if os.name == "nt":  # Windows
    VENV_PYTHON = os.path.join(sys.prefix, "Scripts", "python.exe")
else:  # Linux/macOS
    VENV_PYTHON = os.path.join(sys.prefix, "bin", "python")

# Milvus Client Setup
client = MilvusClient(
    uri="http://localhost:19530",
    token="root:Milvus"
)

def run_command(command):
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              text=True, bufsize=1, encoding="utf-8", errors="replace")
    
    output_area = st.empty()  # Placeholder for live output
    error_area = st.empty()   # Placeholder for errors
    
    output_text = []
    error_text = []

    for line in process.stdout:
        output_text.append(line)
        output_area.text_area("Processing Output", "".join(output_text), height=300)

    for line in process.stderr:
        error_text.append(line)
        error_area.text_area("Errors", "".join(error_text), height=300)

    process.wait()

def run_dump(pdfs, output_dir): #upload kr rhe they, khudka folder ban rha tha and so on, and the pdf is stored in milvus
    if not pdfs or not output_dir:
        st.error("Please upload at least one PDF and specify an output directory.")
        return
    
    output_dir = os.path.abspath(output_dir)  # Ensure absolute path
    os.makedirs(output_dir, exist_ok=True)
    
    pdf_paths = []
    for pdf in pdfs:
        pdf_path = os.path.join(output_dir, pdf.name)  # Save full path
        with open(pdf_path, "wb") as f:
            f.write(pdf.getbuffer())
        pdf_paths.append(pdf_path)
    
    command = [VENV_PYTHON, "automation.py", "dump", *pdf_paths, output_dir]
    run_command(command)

def run_search(query): #isme search krlo
    command = [VENV_PYTHON, "automation.py", "search"]
    if query:
        command.append(query)
    
    run_command(command)

st.title("Research Paper Summarizer and Question Paper Generator")

# Sidebar for Milvus Collections
st.sidebar.header("Database Collections")
collections = client.list_collections()
selected_collection = st.sidebar.selectbox("Select a collection to delete", collections, index=None, placeholder="Select a collection...")

if st.sidebar.button("Delete Collection"):
    st.session_state["delete_confirm"] = True  # Set flag to confirm

if st.session_state.get("delete_confirm", False):
    st.sidebar.error(f"Do you really want to delete {selected_collection}?")
    if st.sidebar.button("Yes"):
        client.drop_collection(collection_name=selected_collection)
        st.sidebar.success(f"Collection '{selected_collection}' deleted successfully!")
        del st.session_state["delete_confirm"]  # Reset flag
        st.rerun()  # Refresh the UI
    if st.sidebar.button("Cancel"):
        del st.session_state["delete_confirm"]  # Reset flag
        st.rerun()

st.header("Save Data to Database")
uploaded_pdfs = st.file_uploader("Upload PDFs for Summarization", type=["pdf"], accept_multiple_files=True)
output_directory = st.text_input("Output Directory for Summarization")
if st.button("Process PDFs"):
    run_dump(uploaded_pdfs, output_directory)

st.header("Search and Summarize")
query = st.text_input("Enter Search Query")
if st.button("Summarize"):
    run_search(query)

st.header("Generate Question Paper")
topic = st.text_input("Enter Subject/Topic for Question Paper")
uploaded_materials = st.file_uploader("Upload Syllabus/Study Materials (PDFs)", type=["pdf"], accept_multiple_files=True)
qp_output_directory = st.text_input("Question Paper Output Directory")
if st.button("Generate Question Paper"):
    if not uploaded_materials or not qp_output_directory or not topic:
        st.error("Please upload materials, specify a topic, and provide an output directory.")
    else:
        qp_output_dir = os.path.abspath(qp_output_directory)
        os.makedirs(qp_output_dir, exist_ok=True)
        
        # Save uploaded PDFs
        pdf_paths = []
        for pdf in uploaded_materials:
            pdf_path = os.path.join(qp_output_dir, pdf.name)
            with open(pdf_path, "wb") as f:
                f.write(pdf.getbuffer())
            pdf_paths.append(pdf_path)
        
        # Process PDFs and generate question paper
        automation = PDFToMilvusAutomation(pdf_paths, qp_output_dir)
        automation.process_pdfs_and_dump_to_milvus()
        md_path, pdf_path = asyncio.run(automation.generate_question_paper(topic, qp_output_dir))
        st.success(f"Question Paper generated: {pdf_path}")
        with open(pdf_path, "rb") as f:
            st.download_button("Download Question Paper PDF", f, file_name="question_paper.pdf")