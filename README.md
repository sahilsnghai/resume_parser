# Resume Parser Application

A resume parsing application built with FastAPI, LangChain, LangGraph, and OpenAI GPT-4. This application extracts structured information from PDF and DOCX resumes with high accuracy.

## Features

### 🤖 LLM-Powered Extraction
- Uses OpenAI GPT-4 with LangChain and LangGraph for intelligent parsing
- Structured output using Pydantic v2 models for consistent data format
- Automatic retry logic for improved reliability
- Handles long resumes by intelligent chunking

### 📄 File Support
- PDF files (using PyMuPDF)
- DOCX files (using python-docx)
- Automatic text cleaning and preprocessing

### 🚀 FastAPI Backend
- RESTful API endpoints for file upload and resume retrieval
- PostgreSQL database with SQLAlchemy ORM
- Async database operations for high performance
- Comprehensive error handling and validation

### 🎨 Streamlit UI
- Clean, modern user interface
- Drag-and-drop file upload
- Real-time processing status
- Structured display of extracted information

## Tech Stack

### Backend
- **FastAPI** - Modern web framework
- **SQLAlchemy 2.0** - Async ORM
- **PostgreSQL** - Database
- **LangChain + LangGraph** - LLM orchestration
- **OpenAI GPT-4** - Language model
- **Pydantic v2** - Data validation

### Frontend
- **Streamlit** - Web UI framework

### Utilities
- **PyMuPDF** - PDF text extraction
- **python-docx** - DOCX text extraction
- **Loguru** - Structured logging

## Installation

1. Clone the repository
```bash
git clone <repository-url>
cd resume-parser
```

2. Create and activate virtual environment
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies
```bash
pip install -r requirements.txt
```

4. Set up environment variables
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. Create required directories
```bash
mkdir -p data/uploads
```

## Configuration

Copy `.env.example` to `.env` and configure the following:

```bash
# Database Configuration
DATABASE_URL=postgresql+asyncpg://username:password@localhost:5432/resume_parser

# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4

# Server Configuration
HOST=0.0.0.0
PORT=8000
```

## Usage

### Running the FastAPI Backend

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
# or
python run_app.py
```

### Running the Streamlit UI

```bash
streamlit run ui/streamlit_app.py
```

### API Endpoints

#### Upload Resume
```http
POST /api/upload
Content-Type: multipart/form-data

# Response:
{
  "document_id": "uuid",
  "extracted_resume_data": {
    "contact_info": {...},
    "summary": "...",
    "work_experience": [...],
    "education": [...],
    "skills": [...],
    "certifications": [...]
  }
}
```

#### Get Resume
```http
GET /api/resume/{document_id}

# Response:
{
  "document_id": "uuid",
  "filename": "resume.pdf",
  "extracted_data": {...},
  "created_at": "2023-11-15T10:30:00"
}
```

## Project Structure

```
├── app/
│   ├── main.py                 # FastAPI application entry point
│   ├── database.py             # Database configuration
│   ├── models.py               # SQLAlchemy ORM models
│   ├── schemas.py              # Pydantic schemas
│   │
│   ├── core/
│   │   └── config.py           # Configuration management
│   │
│   ├── routes/
│   │   └── resume_routes.py    # API route handlers
│   │
│   ├── services/
│   │   ├── parser_service.py   # LangGraph parsing orchestration
│   │   ├── llm_service.py      # LLM extraction service
│   │   └── file_service.py     # File handling service
│   │
│   └── utils/
│       ├── extractor.py        # PDF/DOCX text extraction
│       └── logger.py           # Logging configuration
│
├── ui/
│   └── streamlit_app.py        # Streamlit web interface
│
└── data/
    └── uploads/                # Uploaded files storage
```

## Data Models

### Resume Schema
The extracted resume data follows this structured format:

```json
{
  "contact_info": {
    "name": "John Doe",
    "email": "john.doe@email.com",
    "phone": "+1-555-0123",
    "location": "New York, NY"
  },
  "summary": "Experienced software engineer...",
  "work_experience": [
    {
      "role": "Senior Developer",
      "company": "Tech Corp",
      "duration": "2020-2023",
      "responsibilities": "Lead development team..."
    }
  ],
  "education": [
    {
      "degree": "BSc Computer Science",
      "institution": "University of Technology",
      "year": "2019"
    }
  ],
  "skills": ["Python", "FastAPI", "PostgreSQL"],
  "certifications": ["AWS Certified Developer"]
}
```

### Environment Variables for Production
- Set `DEBUG=False`
- Use production database URL
- Configure proper OpenAI API key

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

