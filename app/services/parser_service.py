import uuid
from typing import Dict, Any, Optional, Tuple, List
from pathlib import Path
from datetime import datetime


from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from app.models import Resume
from app.schemas import ResumeDataSchema
from app.services.llm_service import extraction_chain
from app.utils.extractor import extract_and_clean_text
from app.utils.logger import (
    get_logger,
    log_parse_start,
    log_parse_success,
    log_parse_error,
)

logger = get_logger("app.services.parser_service")


class ResumeParsingState:
    """State object for resume parsing workflow"""

    def __init__(self):
        self.file_path: Optional[str] = None
        self.original_filename: Optional[str] = None
        self.file_type: Optional[str] = None
        self.extracted_text: Optional[str] = None
        self.cleaned_text: Optional[str] = None
        self.extracted_data: Optional[Dict[str, Any]] = None
        self.validation_errors: Optional[List[str]] = None
        self.document_id: Optional[str] = None
        self.error_message: Optional[str] = None
        self.processing_time: Optional[float] = None


class ResumeParsingWorkflow:
    """LangGraph workflow for resume parsing"""

    def __init__(self):
        self.checkpoint_memory = MemorySaver()
        self.workflow = self._create_workflow()

    def _create_workflow(self) -> StateGraph:
        """Create the LangGraph workflow"""

        workflow = StateGraph(dict)

        workflow.add_node("extract_text", self._extract_text_node)
        workflow.add_node("clean_text", self._clean_text_node)
        workflow.add_node("extract_data", self._extract_data_node)

        workflow.add_node("save_to_database", self._save_to_database_node)
        workflow.add_node("handle_error", self._handle_error_node)

        workflow.set_entry_point("extract_text")

        workflow.add_edge("extract_text", "clean_text")
        workflow.add_edge("clean_text", "extract_data")

        workflow.add_conditional_edges(
            "extract_data",
            self._check_validation_result,
            {"valid": "save_to_database", "invalid": "handle_error"},
        )
        workflow.add_edge("save_to_database", END)
        workflow.add_edge("handle_error", END)

        return workflow.compile(checkpointer=self.checkpoint_memory)

    async def _extract_text_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Extract text from uploaded file"""
        try:
            file_path = state.get("file_path")
            original_filename = state.get("original_filename")

            log_parse_start(original_filename)
            start_time = datetime.now()

            extracted_text = extract_and_clean_text(file_path)

            processing_time = (datetime.now() - start_time).total_seconds()

            logger.info(
                f"Successfully extracted text from {original_filename} in {processing_time:.2f}s"
            )
            state["extracted_text"] = extracted_text
            state["processing_time"] = processing_time

            return state

        except Exception as e:
            logger.error(f"Text extraction failed: {e}")
            return {
                "error_message": f"Text extraction failed: {str(e)}",
                "processing_time": 0,
            }

    async def _clean_text_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Clean and preprocess extracted text"""
        try:
            extracted_text = state.get("extracted_text")

            if not extracted_text:
                raise ValueError("No text to clean")

            from app.utils.extractor import text_cleaner

            cleaned_text = text_cleaner.clean_text(extracted_text)
            cleaned_text = text_cleaner.remove_resume_noise(cleaned_text)

            logger.info(f"Text cleaned successfully, length: {len(cleaned_text)}")
            state["cleaned_text"] = cleaned_text

            return state

        except Exception as e:
            logger.error(f"Text cleaning failed: {e}")
            return {"error_message": f"Text cleaning failed: {str(e)}"}

    async def _extract_data_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Extract structured data using LLM"""
        try:
            cleaned_text = state.get("cleaned_text")

            if not cleaned_text:
                raise ValueError("No cleaned text available for extraction")

            try:

                extracted_data = await extraction_chain.extract_from_text(cleaned_text)

                logger.info("Successfully extracted structured data from text")
                state["extracted_data"] = extracted_data
                state["validation_passed"] = True
            except Exception as e:
                logger.error(f"Data extraction failed: {e}")
                state = {
                    "error_message": f"Data extraction failed: {str(e)}",
                    "validation_passed": False,
                    "validation_errors": [repr(e)],
                }

            return state

        except Exception as e:
            logger.error(f"Data extraction failed: {e}")
            return {"error_message": f"Data extraction failed: {str(e)}"}

    async def _validate_data_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Validate extracted data"""
        try:
            extracted_data = state.get("extracted_data")

            if not extracted_data:
                raise ValueError("No data to validate")

            ResumeDataSchema.model_validate(extracted_data)

            logger.info("Data validation successful")
            state["validation_passed"] = True
            state["validation_errors"] = []

            return state

        except Exception as e:
            logger.error(f"Data validation failed: {e}")
            return {"validation_passed": False, "validation_errors": [str(e)]}

    async def _save_to_database_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Save parsed resume to database"""
        try:
            extracted_data = state.get("extracted_data")
            original_filename = state.get("original_filename")
            file_path = state.get("file_path")

            document_id = str(uuid.uuid4())

            file_type = Path(original_filename).suffix.lower().lstrip(".")

            resume = Resume.create_from_data(
                filename=original_filename,
                file_type=file_type,
                extracted_data=extracted_data,
                file_path=file_path,
            )
            resume.id = uuid.UUID(document_id)

            logger.info(f"Resume saved to database with ID: {document_id}")
            state["document_id"] = document_id
            state["resume_record"] = resume.to_dict()

            return state

        except Exception as e:
            logger.error(f"Database save failed: {e}")
            return {"error_message": f"Database save failed: {str(e)}"}

    async def _handle_error_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Handle workflow errors"""
        error_message = state.get("error_message", "Unknown error occurred")
        validation_errors = state.get("validation_errors", [])

        logger.error(f"Workflow completed with errors: {error_message}")
        if validation_errors:
            logger.error(f"Validation errors: {validation_errors}")

        return {"error_message": error_message, "validation_errors": validation_errors}

    def _check_validation_result(self, state: Dict[str, Any]) -> str:
        """Check if validation passed"""
        validation_passed = state.get("validation_passed", False)
        return "valid" if validation_passed else "invalid"


class ResumeParserService:
    """Main service for resume parsing operations"""

    def __init__(self):
        self.workflow: StateGraph = ResumeParsingWorkflow()

    async def parse_resume(
        self, file_path: str, original_filename: str, unique_id: str, db_session=None
    ) -> Tuple[bool, Dict[str, Any], Optional[str]]:
        """
        Parse a resume file and return structured data

        Args:
            file_path (str): Path to the uploaded file
            original_filename (str): Original filename
            db_session: Database session for saving results

        Returns:
            Tuple[bool, Dict[str, Any], Optional[str]]:
                (success, result_data, error_message)
        """
        try:

            initial_state = {
                "file_path": file_path,
                "original_filename": original_filename,
                "file_type": Path(original_filename).suffix.lower().lstrip("."),
            }

            result = await self.workflow.workflow.ainvoke(
                initial_state,
                config={
                    "configurable": {
                        "thread_id": unique_id,
                    }
                },
            )

            if "error_message" in result:
                error_msg = result["error_message"]
                log_parse_error(original_filename, error_msg)
                return False, {}, error_msg

            document_id = result.get("document_id")
            extracted_data = result.get("extracted_data", {})
            processing_time = result.get("processing_time", 0)

            if db_session and document_id:
                try:
                    resume_data = result.get("resume_record")
                    if resume_data:
                        resume_record = Resume.create_from_data(
                            filename=resume_data["original_filename"],
                            file_type=resume_data["file_type"],
                            extracted_data=resume_data["extracted_data"],
                            file_path=resume_data.get("file_path"),
                        )

                        db_session.add(resume_record)
                        await db_session.commit()
                        await db_session.refresh(resume_record)
                except Exception as db_error:
                    logger.error(f"Failed to save to database: {db_error}")

            log_parse_success(document_id, processing_time)

            return (
                True,
                {
                    "document_id": document_id,
                    "extracted_resume_data": extracted_data,
                    "processing_time": processing_time,
                    "filename": original_filename,
                },
                None,
            )

        except Exception as e:
            error_msg = f"Resume parsing failed: {str(e)}"
            logger.error(error_msg)
            log_parse_error(original_filename, error_msg)
            return False, {}, error_msg

    async def get_parsing_status(self, thread_id: str) -> Dict[str, Any]:
        """
        Get the status of a parsing workflow

        Args:
            thread_id (str): Workflow thread ID

        Returns:
            Dict[str, Any]: Status information
        """
        try:

            config = {"configurable": {"thread_id": thread_id}}
            state = self.workflow.workflow.get_state(config)

            return {
                "thread_id": thread_id,
                "status": "running",
                "values": state.values,
                "next": state.next,
            }

        except Exception as e:
            logger.error(f"Failed to get parsing status for thread {thread_id}: {e}")
            return {"thread_id": thread_id, "status": "error", "error": str(e)}


parser_service = ResumeParserService()
