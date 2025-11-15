from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


class ContactInfoSchema(BaseModel):
    """Schema for contact information extracted from resumes"""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "John Doe",
                "email": "john.doe@email.com",
                "phone": "+1-555-0123",
                "location": "New York, NY",
            }
        }
    )

    name: str = Field(..., description="Full name of the candidate")
    email: str = Field(..., description="Email address")
    phone: Optional[str] = Field(None, description="Phone number")
    location: Optional[str] = Field(None, description="Geographic location")


class WorkExperienceSchema(BaseModel):
    """Schema for work experience entries"""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "role": "Senior Software Engineer",
                "company": "Tech Corp",
                "duration": "Jan 2020 - Present",
                "responsibilities": "Lead development team, architect microservices, implement CI/CD pipeline",
            }
        }
    )

    role: str = Field(..., description="Job title or position")
    company: str = Field(..., description="Company name")
    duration: Optional[str] = Field(None, description="Employment duration")
    responsibilities: Optional[str] = Field(
        None, description="Key responsibilities and achievements"
    )


class EducationSchema(BaseModel):
    """Schema for education entries"""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "degree": "Bachelor of Science in Computer Science",
                "institution": "University of Technology",
                "year": "2019",
                "gpa": "3.8",
            }
        }
    )

    degree: str = Field(..., description="Degree obtained")
    institution: str = Field(..., description="Educational institution")
    year: Optional[str] = Field(None, description="Year of graduation")
    gpa: Optional[str] = Field(None, description="Grade point average")


class SkillsSchema(BaseModel):
    """Schema for skills"""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "technical_skills": ["Python", "FastAPI", "PostgreSQL", "Docker"],
                "soft_skills": ["Leadership", "Communication", "Teamwork"],
            }
        }
    )

    technical_skills: List[str] = Field(
        default_factory=list, description="Technical skills"
    )
    soft_skills: List[str] = Field(default_factory=list, description="Soft skills")


class CertificationSchema(BaseModel):
    """Schema for certifications"""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "AWS Certified Solutions Architect",
                "issuing_organization": "Amazon Web Services",
                "year": "2022",
            }
        }
    )

    name: str = Field(..., description="Certification name")
    issuing_organization: Optional[str] = Field(
        None, description="Issuing organization"
    )
    year: Optional[str] = Field(None, description="Year obtained")


class ResumeDataSchema(BaseModel):
    """Complete structured resume data schema"""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "contact_info": {
                    "name": "John Doe",
                    "email": "john.doe@email.com",
                    "phone": "+1-555-0123",
                    "location": "New York, NY",
                },
                "summary": "Experienced software engineer with 5+ years in backend development...",
                "work_experience": [
                    {
                        "role": "Senior Software Engineer",
                        "company": "Tech Corp",
                        "duration": "Jan 2020 - Present",
                        "responsibilities": "Lead development team, architect microservices...",
                    }
                ],
                "education": [
                    {
                        "degree": "BSc Computer Science",
                        "institution": "University of Technology",
                        "year": "2019",
                    }
                ],
                "skills": {
                    "technical_skills": ["Python", "FastAPI", "PostgreSQL"],
                    "soft_skills": ["Leadership", "Communication"],
                },
                "certifications": [
                    {
                        "name": "AWS Certified Developer",
                        "issuing_organization": "Amazon Web Services",
                        "year": "2021",
                    }
                ],
            }
        }
    )

    contact_information: ContactInfoSchema = Field(
        ..., description="Contact information"
    )
    summary: Optional[str] = Field(
        None, description="Professional summary or objective"
    )
    work_experience: List[WorkExperienceSchema] = Field(
        default_factory=list, description="Work experience entries"
    )
    education: List[EducationSchema] = Field(
        default_factory=list, description="Education history"
    )
    skills: SkillsSchema = Field(default_factory=SkillsSchema, description="Skills")
    certifications: List[CertificationSchema] = Field(
        default_factory=list, description="Professional certifications"
    )


class UploadResumeRequest(BaseModel):
    """Schema for resume upload request"""

    model_config = ConfigDict(json_schema_extra={"example": {"file": "resume.pdf"}})


class UploadResumeResponse(BaseModel):
    """Schema for resume upload response"""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "document_id": "123e4567-e89b-12d3-a456-426614174000",
                "message": "Resume uploaded and processed successfully",
                "extracted_resume_data": {
                    "contact_info": {"name": "John Doe", "email": "john.doe@email.com"},
                    "summary": "Experienced professional...",
                    "work_experience": [],
                    "education": [],
                    "skills": {"technical_skills": [], "soft_skills": []},
                    "certifications": [],
                },
            }
        }
    )

    document_id: UUID = Field(
        ..., description="Unique identifier for the processed resume"
    )
    message: str = Field(..., description="Response message")
    extracted_resume_data: ResumeDataSchema = Field(
        ..., description="Extracted resume data"
    )


class GetResumeResponse(BaseModel):
    """Schema for getting resume response"""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "document_id": "123e4567-e89b-12d3-a456-426614174000",
                "filename": "john_doe_resume.pdf",
                "extracted_data": {
                    "contact_info": {"name": "John Doe", "email": "john.doe@email.com"}
                },
                "created_at": "2023-11-15T10:30:00Z",
            }
        }
    )

    document_id: UUID = Field(..., description="Unique identifier for the resume")
    filename: str = Field(..., description="Original filename")
    extracted_data: Dict[str, Any] = Field(
        ..., description="Extracted resume data as JSON"
    )
    created_at: datetime = Field(..., description="Timestamp when resume was processed")


class ErrorResponse(BaseModel):
    """Schema for error responses"""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "error": "Invalid file type. Only PDF and DOCX files are supported.",
                "detail": "file_type_not_supported",
            }
        }
    )

    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Additional error details")


class HealthResponse(BaseModel):
    """Schema for health check response"""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "healthy",
                "version": "1.0.0",
                "database": "connected",
            }
        }
    )

    status: int = Field(..., description="Application status")
    version: str = Field(..., description="Application version")
    database: str = Field(..., description="Database connection status")


class FileProcessingResult(BaseModel):
    """Schema for file processing results"""

    success: bool = Field(..., description="Whether processing was successful")
    document_id: Optional[UUID] = Field(None, description="Document ID if successful")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    processing_time: Optional[float] = Field(
        None, description="Time taken for processing in seconds"
    )


class ProcessingStatus(BaseModel):
    """Schema for processing status"""

    status: str = Field(..., description="Current processing status")
    progress: int = Field(..., ge=0, le=100, description="Progress percentage")
    message: Optional[str] = Field(None, description="Additional status message")
