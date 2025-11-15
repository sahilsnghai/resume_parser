import uuid
import hashlib
import aiofiles
from typing import Optional
from pathlib import Path

from fastapi import UploadFile, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models import FileMetadata
from app.utils.logger import (
    get_logger,
    log_upload_start,
    log_upload_success,
    log_file_error,
)

logger = get_logger("app.services.file_service")


class FileService:
    """Service for file operations"""

    def __init__(self):
        self.upload_dir = Path(settings.UPLOAD_DIR)
        self.max_file_size = settings.MAX_FILE_SIZE
        self.allowed_extensions = set(
            ext.lower() for ext in settings.ALLOWED_EXTENSIONS
        )

        self.upload_dir.mkdir(parents=True, exist_ok=True)

    def validate_file(self, file: UploadFile) -> None:
        """
        Validate uploaded file

        Args:
            file (UploadFile): File to validate

        Raises:
            HTTPException: If file validation fails
        """

        file_extension = Path(file.filename).suffix.lower()
        if file_extension not in self.allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type: {file_extension}. Allowed types: {', '.join(self.allowed_extensions)}",
            )

        if hasattr(file, "size") and file.size and file.size > self.max_file_size:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Maximum size: {self.max_file_size} bytes",
            )

    def generate_filename(self, original_filename: str) -> str | str:
        """
        Generate a unique filename for storage

        Args:
            original_filename (str): Original filename

        Returns:
            str: Unique id
            str: Generated filename
        """

        file_extension = Path(original_filename).suffix.lower()

        unique_id = str(uuid.uuid4())[:8]
        timestamp = str(
            int(hashlib.sha256(str(uuid.uuid4()).encode()).hexdigest(), 16) % 100000000
        )

        return unique_id, f"{unique_id}_{timestamp}{file_extension}"

    async def save_upload_file(
        self,
        file: UploadFile,
        upload_ip: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> dict:
        """
        Save uploaded file and return metadata

        Args:
            file (UploadFile): File to save
            upload_ip (str, optional): Upload IP address
            user_agent (str, optional): User agent string

        Returns:
            dict: File metadata including storage information
        """

        self.validate_file(file)

        unique_id, stored_filename = self.generate_filename(file.filename)
        file_path = self.upload_dir / stored_filename

        log_upload_start(file.filename, getattr(file, "size", "unknown"))

        try:

            content = await file.read()

            if len(content) > self.max_file_size:
                raise HTTPException(
                    status_code=413,
                    detail=f"File too large after reading: {len(content)} bytes",
                )

            async with aiofiles.open(file_path, "wb") as f:
                await f.write(content)

            file_metadata = {
                "original_filename": file.filename,
                "stored_filename": stored_filename,
                "file_path": str(file_path),
                "file_size": len(content),
                "file_type": Path(file.filename).suffix.lower().lstrip("."),
                "upload_ip": upload_ip,
                "user_agent": user_agent,
                "unique_id": unique_id,
            }

            log_upload_success(file.filename, str(uuid.uuid4()))

            return file_metadata

        except Exception as e:
            logger.error(f"Error saving file {file.filename}: {e}")

            if file_path.exists():
                file_path.unlink()
            raise HTTPException(
                status_code=500, detail=f"Failed to save file: {str(e)}"
            )

    async def delete_file(self, filename: str) -> bool:
        """
        Delete a stored file

        Args:
            filename (str): Name of the file to delete

        Returns:
            bool: True if deleted, False if file not found
        """
        try:
            file_path = self.upload_dir / filename
            if file_path.exists():
                file_path.unlink()
                logger.info(f"Deleted file: {filename}")
                return True
            else:
                logger.warning(f"File not found for deletion: {filename}")
                return False
        except Exception as e:
            logger.error(f"Error deleting file {filename}: {e}")
            return False

    def get_file_path(self, filename: str) -> Path:
        """
        Get full path to a stored file

        Args:
            filename (str): Stored filename

        Returns:
            Path: Full path to file
        """
        return self.upload_dir / filename

    def file_exists(self, filename: str) -> bool:
        """
        Check if file exists

        Args:
            filename (str): Filename to check

        Returns:
            bool: True if file exists
        """
        file_path = self.upload_dir / filename
        return file_path.exists()

    def get_file_size(self, filename: str) -> Optional[int]:
        """
        Get file size in bytes

        Args:
            filename (str): Filename

        Returns:
            Optional[int]: File size in bytes, None if file not found
        """
        file_path = self.upload_dir / filename
        try:
            return file_path.stat().st_size if file_path.exists() else None
        except Exception:
            return None

    def get_file_info(self, filename: str) -> Optional[dict]:
        """
        Get comprehensive file information

        Args:
            filename (str): Filename

        Returns:
            Optional[dict]: File information or None if file not found
        """
        file_path = self.upload_dir / filename
        if not file_path.exists():
            return None

        try:
            stat = file_path.stat()
            return {
                "filename": filename,
                "size": stat.st_size,
                "created": stat.st_ctime,
                "modified": stat.st_mtime,
                "path": str(file_path),
            }
        except Exception as e:
            logger.error(f"Error getting file info for {filename}: {e}")
            return None


file_service = FileService()


class FileMetadataService:
    """Service for file metadata database operations"""

    @staticmethod
    async def create_file_metadata(
        db: AsyncSession,
        original_filename: str,
        stored_filename: str,
        file_path: str,
        file_size: int,
        file_type: str,
        upload_ip: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> FileMetadata:
        """
        Create file metadata record in database

        Args:
            db (AsyncSession): Database session
            original_filename (str): Original filename
            stored_filename (str): Stored filename
            file_path (str): Full file path
            file_size (int): File size in bytes
            file_type (str): File type (extension)
            upload_ip (str, optional): Upload IP address
            user_agent (str, optional): User agent string

        Returns:
            FileMetadata: Created metadata record
        """
        try:
            metadata = FileMetadata(
                original_filename=original_filename,
                stored_filename=stored_filename,
                file_path=file_path,
                file_size=f"{file_size:,} bytes",
                file_type=file_type,
                upload_ip=upload_ip,
                user_agent=user_agent,
            )

            db.add(metadata)
            await db.commit()
            await db.refresh(metadata)

            logger.info(f"Created file metadata for {stored_filename}")
            return metadata

        except Exception as e:
            await db.rollback()
            logger.error(f"Error creating file metadata: {e}")
            raise

    @staticmethod
    async def get_file_metadata(
        db: AsyncSession, stored_filename: str
    ) -> Optional[FileMetadata]:
        """
        Get file metadata by stored filename

        Args:
            db (AsyncSession): Database session
            stored_filename (str): Stored filename

        Returns:
            Optional[FileMetadata]: File metadata or None if not found
        """
        try:
            from sqlalchemy import select

            result = await db.execute(
                select(FileMetadata).where(
                    FileMetadata.stored_filename == stored_filename
                )
            )
            metadata = result.scalar_one_or_none()

            return metadata

        except Exception as e:
            logger.error(f"Error getting file metadata for {stored_filename}: {e}")
            return None

    @staticmethod
    async def delete_file_metadata(db: AsyncSession, stored_filename: str) -> bool:
        """
        Delete file metadata from database

        Args:
            db (AsyncSession): Database session
            stored_filename (str): Stored filename

        Returns:
            bool: True if deleted, False if not found
        """
        try:
            metadata = await FileMetadataService.get_file_metadata(db, stored_filename)
            if metadata:
                await db.delete(metadata)
                await db.commit()
                logger.info(f"Deleted file metadata for {stored_filename}")
                return True
            return False

        except Exception as e:
            await db.rollback()
            logger.error(f"Error deleting file metadata for {stored_filename}: {e}")
            return False
