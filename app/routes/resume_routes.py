import uuid
from fastapi import APIRouter, File, UploadFile, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models import Resume
from app.schemas import UploadResumeResponse, GetResumeResponse, ResumeDataSchema
from app.services.file_service import file_service, FileMetadataService
from app.services.parser_service import parser_service
from app.utils.logger import get_logger

router = APIRouter()
logger = get_logger("app.routes.resume_routes")


@router.post(
    "/upload", response_model=UploadResumeResponse, status_code=status.HTTP_201_CREATED
)
async def upload_resume(
    request: Request, file: UploadFile = File(...), db: AsyncSession = Depends(get_db)
):
    """
    Upload a resume file and extract structured data

    Args:
        request (Request): FastAPI request object
        file (UploadFile): Uploaded file (PDF or DOCX)
        db (AsyncSession): Database session

    Returns:
        UploadResumeResponse: Upload result with extracted data

    Raises:
        HTTPException: If upload or processing fails
    """

    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")

    logger.info(f"Resume upload request from {client_ip}")

    try:

        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="No file provided"
            )

        document_id = str(uuid.uuid4())

        file_metadata = await file_service.save_upload_file(
            file, upload_ip=client_ip, user_agent=user_agent
        )

        await FileMetadataService.create_file_metadata(
            db=db,
            original_filename=file_metadata["original_filename"],
            stored_filename=file_metadata["stored_filename"],
            file_path=file_metadata["file_path"],
            file_size=file_metadata["file_size"],
            file_type=file_metadata["file_type"],
            upload_ip=client_ip,
            user_agent=user_agent,
        )

        success, result_data, error_message = await parser_service.parse_resume(
            file_path=file_metadata["file_path"],
            original_filename=file_metadata["original_filename"],
            unique_id=file_metadata["unique_id"],
            db_session=db,
        )

        if not success:

            error_resume = Resume(
                id=uuid.UUID(document_id),
                original_filename=file_metadata["original_filename"],
                file_type=file_metadata["file_type"],
                extracted_data={},
                file_path=file_metadata["file_path"],
                processing_status="failed",
                processing_error=error_message,
            )
            db.add(error_resume)
            await db.commit()

            logger.error(f"Resume processing failed: {error_message}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to process resume: {error_message}",
            )

        extracted_data = result_data.get("extracted_resume_data", {})

        logger.info(f"Resume processed successfully: {document_id}")

        return UploadResumeResponse(
            document_id=uuid.UUID(result_data["document_id"]),
            message="Resume uploaded and processed successfully",
            extracted_resume_data=ResumeDataSchema.parse_obj(extracted_data),
        )

    except HTTPException:

        raise
    except Exception as e:
        logger.error(f"Unexpected error during resume upload: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during resume processing",
        )


@router.get("/resume/{document_id}", response_model=GetResumeResponse)
async def get_resume(document_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """
    Retrieve resume data by document ID

    Args:
        document_id (uuid.UUID): Resume document ID
        db (AsyncSession): Database session

    Returns:
        GetResumeResponse: Resume data

    Raises:
        HTTPException: If resume not found
    """
    try:

        result = await db.execute(select(Resume).where(Resume.id == document_id))
        resume = result.scalar_one_or_none()

        if not resume:
            logger.warning(f"Resume not found: {document_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Resume not found"
            )

        logger.info(f"Retrieved resume: {document_id}")

        return GetResumeResponse(
            document_id=resume.id,
            filename=resume.original_filename,
            extracted_data=resume.extracted_data,
            created_at=resume.created_at,
        )

    except HTTPException:

        raise
    except Exception as e:
        logger.error(f"Error retrieving resume {document_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while retrieving the resume",
        )
