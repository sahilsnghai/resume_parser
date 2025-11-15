import sys
from pathlib import Path
from loguru import logger as loguru_logger

from app.core.config import settings


def setup_logger():
    """Set up the application logger with Loguru"""

    loguru_logger.remove()

    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)

    loguru_logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | <level>{message}</level>",
        level=settings.LOG_LEVEL,
        colorize=True,
        backtrace=True,
        diagnose=True,
    )

    loguru_logger.add(
        logs_dir / "app.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
        level=settings.LOG_LEVEL,
        rotation="10 MB",
        retention="30 days",
        compression="zip",
        backtrace=True,
        diagnose=True,
    )

    loguru_logger.add(
        logs_dir / "error.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
        level="ERROR",
        rotation="10 MB",
        retention="90 days",
        compression="zip",
        backtrace=True,
        diagnose=True,
    )

    if settings.LOG_LEVEL == "INFO":
        loguru_logger.add(
            logs_dir / "app.json",
            format="{message}",
            level="INFO",
            rotation="100 MB",
            retention="365 days",
            compression="zip",
            serialize=True,
        )

    loguru_logger.info(f"Logger initialized with level: {settings.LOG_LEVEL}")
    loguru_logger.info(f"Application name: {settings.APP_NAME}")
    loguru_logger.info(f"Application version: {settings.APP_VERSION}")


def get_logger(name: str = None):
    """
    Get a logger instance

    Args:
        name (str, optional): Logger name. Defaults to None.

    Returns:
        Logger: Loguru logger instance
    """
    if name:
        return loguru_logger.bind(name=name)
    return loguru_logger


logger = get_logger("app")


def setup_custom_levels():
    """Set up custom log levels for specific use cases"""

    loguru_logger.level("PARSE", no=25, color="<yellow>", icon="📄")
    loguru_logger.level("LLM", no=26, color="<blue>", icon="🤖")
    loguru_logger.level("UPLOAD", no=27, color="<green>", icon="⬆️")
    loguru_logger.level("EXTRACT", no=28, color="<cyan>", icon="🔍")


setup_custom_levels()


class LogTiming:
    """Context manager for logging operation timing"""

    def __init__(self, operation_name: str, logger_instance=None):
        self.operation_name = operation_name
        self.logger = logger_instance or logger
        self.start_time = None

    def __enter__(self):
        self.start_time = loguru_logger.datetime.now()
        self.logger.info(f"Starting {self.operation_name}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        end_time = loguru_logger.datetime.now()
        duration = (end_time - self.start_time).total_seconds()

        if exc_type is None:
            self.logger.info(
                f"Completed {self.operation_name} in {duration:.2f} seconds"
            )
        else:
            self.logger.error(
                f"Failed {self.operation_name} after {duration:.2f} seconds: {exc_val}"
            )


def log_parse_start(filename: str, file_size: int = None):
    """Log the start of resume parsing"""
    logger.log(
        "PARSE",
        f"Starting resume parsing for {filename}"
        + (f" (size: {file_size} bytes)" if file_size else ""),
    )


def log_parse_success(document_id: str, processing_time: float):
    """Log successful resume parsing"""
    logger.log(
        "PARSE",
        f"Successfully parsed resume {document_id} in {processing_time:.2f} seconds",
    )


def log_parse_error(filename: str, error: str):
    """Log resume parsing error"""
    logger.log("PARSE", f"Failed to parse resume {filename}: {error}")


def log_llm_call(prompt_tokens: int, completion_tokens: int, model: str):
    """Log LLM API call"""
    total_tokens = prompt_tokens + completion_tokens
    logger.log(
        "LLM",
        f"LLM API call - Model: {model}, Tokens: {total_tokens} (prompt: {prompt_tokens}, completion: {completion_tokens})",
    )


def log_llm_success(operation: str, processing_time: float):
    """Log successful LLM operation"""
    logger.log(
        "LLM",
        f"LLM {operation} completed successfully in {processing_time:.2f} seconds",
    )


def log_llm_error(operation: str, error: str):
    """Log LLM operation error"""
    logger.log("LLM", f"LLM {operation} failed: {error}")


def log_upload_start(filename: str, file_size: int):
    """Log file upload start"""
    logger.log("UPLOAD", f"Starting upload for {filename} ({file_size} bytes)")


def log_upload_success(filename: str, document_id: str):
    """Log successful file upload"""
    logger.log("UPLOAD", f"Successfully uploaded {filename} as document {document_id}")


def log_extraction_start(text_length: int):
    """Log text extraction start"""
    logger.log("EXTRACT", f"Starting text extraction for {text_length} characters")


def log_extraction_success(field_count: int):
    """Log successful text extraction"""
    logger.log("EXTRACT", f"Successfully extracted {field_count} fields")


def log_file_error(operation: str, filename: str, error: str):
    """Log file operation error"""
    logger.error(f"File {operation} failed for {filename}: {error}")


def log_execution_time(operation_name: str = None):
    """
    Decorator to log function execution time

    Args:
        operation_name (str, optional): Name of the operation. If None, uses function name.
    """

    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            op_name = operation_name or f"{func.__module__}.{func.__name__}"
            with LogTiming(op_name):
                return await func(*args, **kwargs)

        def sync_wrapper(*args, **kwargs):
            op_name = operation_name or func.__name__
            with LogTiming(op_name):
                return func(*args, **kwargs)

        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

    return decorator


import asyncio
