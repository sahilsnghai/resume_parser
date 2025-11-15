import os
import requests
import streamlit as st
from typing import Dict, Any, Optional

st.set_page_config(
    page_title="Resume Parser",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded",
)

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
MAX_FILE_SIZE = 10 * 1024 * 1024
ALLOWED_FILE_TYPES = ["pdf", "docx"]


def init_session_state():
    if "uploaded_file" not in st.session_state:
        st.session_state.uploaded_file = None
    if "processing_result" not in st.session_state:
        st.session_state.processing_result = None
    if "document_id" not in st.session_state:
        st.session_state.document_id = None
    if "error_message" not in st.session_state:
        st.session_state.error_message = None


def validate_file(uploaded_file) -> tuple[bool, str]:
    if not uploaded_file:
        return False, "No file uploaded"

    file_size = len(uploaded_file.getvalue())
    if file_size > MAX_FILE_SIZE:
        return False, f"File too large. Maximum size: {MAX_FILE_SIZE // (1024*1024)} MB"

    file_extension = uploaded_file.name.split(".")[-1].lower()
    if file_extension not in ALLOWED_FILE_TYPES:
        return False, f"Unsupported file type. Allowed: {', '.join(ALLOWED_FILE_TYPES)}"

    return True, ""


def upload_resume(file) -> tuple[bool, Dict[str, Any], Optional[str]]:
    try:
        files = {"file": (file.name, file, file.type)}
        response = requests.post(f"{API_BASE_URL}/api/upload", files=files, timeout=120)

        if response.status_code == 201:
            return True, response.json(), None
        else:
            error_detail = response.json().get("detail", "Unknown error")
            return False, {}, error_detail

    except requests.exceptions.Timeout:
        return False, {}, "Request timed out."
    except requests.exceptions.ConnectionError:
        return False, {}, f"Cannot connect to API at {API_BASE_URL}."
    except Exception as e:
        return False, {}, str(e)


def get_resume(document_id: str) -> tuple[bool, Dict[str, Any], Optional[str]]:
    try:
        response = requests.get(f"{API_BASE_URL}/api/resume/{document_id}", timeout=30)
        if response.status_code == 200:
            return True, response.json(), None
        else:
            error_detail = response.json().get("detail", "Unknown error")
            return False, {}, error_detail
    except Exception as e:
        return False, {}, str(e)


def display_contact_info(contact_info: Dict[str, Any]):
    st.subheader("Contact Information")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if contact_info.get("name"):
            st.write(f"Name: {contact_info['name']}")
    with col2:
        if contact_info.get("email"):
            st.write(f"Email: {contact_info['email']}")
    with col3:
        if contact_info.get("phone"):
            st.write(f"Phone: {contact_info['phone']}")
    with col4:
        if contact_info.get("location"):
            st.write(f"Location: {contact_info['location']}")


def display_summary(summary: str):
    if summary:
        st.subheader("Summary")
        st.write(summary)


def display_work_experience(work_experience: list):
    if not work_experience:
        return

    st.subheader("Work Experience")

    for exp in work_experience:
        with st.expander(f"{exp.get('role', '')} at {exp.get('company', '')}"):
            col1, col2 = st.columns([2, 1])
            with col1:
                if exp.get("duration"):
                    st.write(f"Duration: {exp['duration']}")

                if exp.get("responsibilities"):
                    st.write("Responsibilities:")
                    responsibilities = exp["responsibilities"]

                    if isinstance(responsibilities, str):
                        if "\n" in responsibilities:
                            items = responsibilities.split("\n")
                        elif "; " in responsibilities:
                            items = responsibilities.split("; ")
                        else:
                            items = [responsibilities]
                    else:
                        items = responsibilities

                    for item in items:
                        if item.strip():
                            st.write(f"- {item.strip()}")


def display_education(education: list):
    if not education:
        return

    st.subheader("Education")

    for edu in education:
        col1, col2 = st.columns([2, 1])
        with col1:
            if edu.get("degree"):
                st.write(edu["degree"])
            if edu.get("institution"):
                st.write(edu["institution"])
        with col2:
            if edu.get("year"):
                st.write(f"Year: {edu['year']}")


def display_skills(skills: Dict[str, Any]):
    if not skills:
        return

    st.subheader("Skills")

    if skills.get("technical_skills"):
        st.write("Technical Skills:")
        tech_html = ""
        for skill in skills["technical_skills"]:
            tech_html += (
                f'<span style="background-color:#f0f8ff;color:#000;border:1px solid #ccc;'
                f'padding:5px 10px;border-radius:5px;margin:5px;display:inline-block;">{skill}</span>'
            )
        st.markdown(tech_html, unsafe_allow_html=True)

    if skills.get("soft_skills"):
        st.write("Soft Skills:")
        soft_html = ""
        for skill in skills["soft_skills"]:
            soft_html += (
                f'<span style="background-color:#f3e5f5;color:#000;border:1px solid #ccc;'
                f'padding:5px 10px;border-radius:5px;margin:5px;display:inline-block;">{skill}</span>'
            )
        st.markdown(soft_html, unsafe_allow_html=True)


def display_certifications(certifications: list):
    if not certifications:
        return

    st.subheader("Certifications")

    for cert in certifications:
        col1, col2 = st.columns([2, 1])
        with col1:
            if cert.get("name"):
                st.write(cert["name"])
            if cert.get("issuing_organization"):
                st.write(cert["issuing_organization"])
        with col2:
            if cert.get("year"):
                st.write(f"Year: {cert['year']}")


def main():
    init_session_state()

    st.title("Resume Parser Application")
    st.write(
        "Upload a resume to extract structured information, or fetch an existing resume by Document ID."
    )

    with st.sidebar:
        st.header("Application Info")
        st.write(f"API Server: {API_BASE_URL}")
        st.write(f"Max File Size: {MAX_FILE_SIZE // (1024*1024)} MB")
        st.write(f"Supported Formats: {', '.join(ALLOWED_FILE_TYPES).upper()}")

        if st.button("Test API Connection"):
            try:
                response = requests.get(f"{API_BASE_URL}/health", timeout=10)
                if response.status_code == 200:
                    st.success("API Connection Successful")
                    health_data = response.json()
                    st.write(f"Status: {health_data.get('status')}")
                    st.write(f"Version: {health_data.get('version')}")
                else:
                    st.error(f"API returned status {response.status_code}")
            except Exception as e:
                st.error(f"Connection failed: {str(e)}")

    st.subheader("Upload and Parse Resume")

    uploaded_file = st.file_uploader(
        "Choose a resume file",
        type=ALLOWED_FILE_TYPES,
        help=f"Supported: {', '.join(ALLOWED_FILE_TYPES)}. Max size {MAX_FILE_SIZE // (1024*1024)} MB",
    )

    col1, col2 = st.columns([1, 4])
    with col1:
        process_button = st.button(
            "Parse Resume", type="primary", disabled=uploaded_file is None
        )

    if uploaded_file and uploaded_file != st.session_state.uploaded_file:
        st.session_state.uploaded_file = uploaded_file
        st.session_state.processing_result = None
        st.session_state.document_id = None
        st.session_state.error_message = None

    if process_button and uploaded_file:
        is_valid, error_msg = validate_file(uploaded_file)
        if not is_valid:
            st.error(error_msg)
        else:
            with st.spinner("Processing resume..."):
                success, result, error = upload_resume(uploaded_file)
                if success:
                    st.session_state.processing_result = result
                    st.session_state.document_id = str(result.get("document_id"))
                    st.session_state.error_message = None
                    st.success("Resume processed successfully.")
                else:
                    st.session_state.processing_result = None
                    st.session_state.document_id = None
                    st.session_state.error_message = error
                    st.error(error)

    st.divider()

    st.subheader("Fetch Resume by Document ID")

    fetch_col1, fetch_col2 = st.columns([3, 1])

    with fetch_col1:
        existing_doc_id = st.text_input(
            "Enter Document ID",
            value=st.session_state.document_id or "",
        )

    with fetch_col2:
        fetch_button = st.button("Fetch", disabled=not existing_doc_id.strip())

    if fetch_button and existing_doc_id.strip():
        with st.spinner("Fetching resume..."):
            success, result, error = get_resume(existing_doc_id.strip())
            if success:
                if "extracted_resume_data" in result:
                    unified = result
                    document_id = str(result.get("document_id"))
                else:
                    unified = {
                        "document_id": str(result.get("id")),
                        "extracted_resume_data": result.get("extracted_data", {}),
                        "processing_time": result.get("processing_time", 0),
                    }
                    document_id = unified["document_id"]

                st.session_state.processing_result = unified
                st.session_state.document_id = document_id
                st.session_state.error_message = None
                st.success("Resume fetched successfully.")
            else:
                st.session_state.processing_result = None
                st.session_state.document_id = None
                st.session_state.error_message = error
                st.error(error)

    if st.session_state.processing_result:
        result = st.session_state.processing_result
        extracted_data = result.get("extracted_resume_data", {})

        st.write(f"Document ID: {st.session_state.document_id}")
        processing_time = result.get("processing_time", 0)
        if processing_time:
            st.write(f"Processing Time: {processing_time:.2f} seconds")

        st.divider()

        display_contact_info(extracted_data.get("contact_info", {}))
        display_summary(extracted_data.get("summary"))
        display_work_experience(extracted_data.get("work_experience", []))
        display_education(extracted_data.get("education", []))
        display_skills(extracted_data.get("skills", {}))
        display_certifications(extracted_data.get("certifications", []))

        with st.expander("Raw Extracted Data"):
            st.json(extracted_data)

    elif st.session_state.error_message:
        st.error(st.session_state.error_message)


if __name__ == "__main__":
    main()
