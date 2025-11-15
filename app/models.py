import uuid
from datetime import datetime
from sqlalchemy import Column, String, JSON, DateTime, Text, Index
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.ext.mutable import MutableDict

from app.database import Base


class Resume(Base):
    """
    Resume model for storing parsed resume data

    This table stores the extracted structured information from resumes
    along with metadata about the original file.
    """

    __tablename__ = "resumes"

    id = Column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        unique=True,
        nullable=False,
    )

    original_filename = Column(String(255), nullable=False, index=True)
    file_type = Column(String(10), nullable=False)

    extracted_data = Column(MutableDict.as_mutable(JSON), nullable=False)

    file_path = Column(String(500), nullable=True)

    processing_status = Column(
        String(50), default="completed", nullable=False, index=True
    )
    processing_error = Column(Text, nullable=True)

    created_at = Column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False, index=True
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    __table_args__ = (
        Index("idx_resumes_created_at", "created_at"),
        Index("idx_resumes_filename", "original_filename"),
        Index("idx_resumes_status", "processing_status"),
        {"extend_existing": True},
    )

    def __repr__(self):
        return f"<Resume(id={self.id}, filename='{self.original_filename}', created_at={self.created_at})>"

    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "id": str(self.id),
            "original_filename": self.original_filename,
            "file_type": self.file_type,
            "extracted_data": self.extracted_data,
            "file_path": self.file_path,
            "processing_status": self.processing_status,
            "processing_error": self.processing_error,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def create_from_data(
        cls, filename: str, file_type: str, extracted_data: dict, file_path: str = None
    ):
        """Create a new Resume instance from extracted data"""
        return cls(
            original_filename=filename,
            file_type=file_type,
            extracted_data=extracted_data,
            file_path=file_path,
            processing_status="completed",
        )


class FileMetadata(Base):
    """
    File metadata model for tracking uploaded files

    This table stores metadata about uploaded files for audit purposes.
    """

    __tablename__ = "file_metadata"

    id = Column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        unique=True,
        nullable=False,
    )

    original_filename = Column(String(255), nullable=False)
    stored_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(String(50), nullable=True)
    file_type = Column(String(10), nullable=False)

    upload_ip = Column(String(50), nullable=True)
    user_agent = Column(Text, nullable=True)

    created_at = Column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False, index=True
    )

    __table_args__ = (
        Index("idx_file_metadata_created_at", "created_at"),
        {"extend_existing": True},
    )

    def __repr__(self):
        return f"<FileMetadata(id={self.id}, filename='{self.original_filename}', created_at={self.created_at})>"

    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "id": str(self.id),
            "original_filename": self.original_filename,
            "stored_filename": self.stored_filename,
            "file_path": self.file_path,
            "file_size": self.file_size,
            "file_type": self.file_type,
            "upload_ip": self.upload_ip,
            "user_agent": self.user_agent,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class ResumeView:
    """
    View class for resume data queries

    This class provides convenient methods for querying resume data.
    """

    @staticmethod
    def get_recent_resumes(limit: int = 10):
        """Get recently processed resumes"""

        pass

    @staticmethod
    def get_resume_stats():
        """Get processing statistics"""

        pass
