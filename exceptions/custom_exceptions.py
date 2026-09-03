"""
Custom exception classes for PDF OCR Converter.
"""


class PDFOCRException(Exception):
    """
    Base exception for all PDF OCR Converter errors.
    """

    def __init__(self, message: str, error_code: str = "UNKNOWN"):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)

    def __str__(self):
        return f"[{self.error_code}] {self.message}"


# PDF-related exceptions

class PDFValidationError(PDFOCRException):
    """PDF validation failed."""

    def __init__(self, message: str):
        super().__init__(message, "PDF_VALIDATION_ERROR")


class PDFCorruptedError(PDFOCRException):
    """PDF file is corrupted or unreadable."""

    def __init__(self, message: str):
        super().__init__(message, "PDF_CORRUPTED")


class PDFEncryptedError(PDFOCRException):
    """PDF is encrypted and password is required."""

    def __init__(self, message: str):
        super().__init__(message, "PDF_ENCRYPTED")


class PDFUnsupportedError(PDFOCRException):
    """PDF format or feature not supported."""

    def __init__(self, message: str):
        super().__init__(message, "PDF_UNSUPPORTED")


class PDFExtractionError(PDFOCRException):
    """Error extracting page or content from PDF."""

    def __init__(self, message: str, page_num: int = None):
        msg = f"Page {page_num}: {message}" if page_num is not None else message
        super().__init__(msg, "PDF_EXTRACTION_ERROR")
        self.page_num = page_num


class PDFReconstructionError(PDFOCRException):
    """Error reconstructing PDF with OCR data."""

    def __init__(self, message: str):
        super().__init__(message, "PDF_RECONSTRUCTION_ERROR")


# OCR-related exceptions

class OCREngineError(PDFOCRException):
    """Error with OCR engine."""

    def __init__(self, message: str):
        super().__init__(message, "OCR_ENGINE_ERROR")


class OCRLanguageNotFoundError(PDFOCRException):
    """OCR language data not found."""

    def __init__(self, language: str):
        super().__init__(
            f"Language data not found: {language}",
            "OCR_LANGUAGE_NOT_FOUND"
        )
        self.language = language


class OCRTimeoutError(PDFOCRException):
    """OCR processing timed out."""

    def __init__(self, message: str, page_num: int = None):
        msg = f"Page {page_num}: {message}" if page_num is not None else message
        super().__init__(msg, "OCR_TIMEOUT")
        self.page_num = page_num


class OCRProcessingError(PDFOCRException):
    """Error during OCR processing."""

    def __init__(self, message: str, page_num: int = None):
        msg = f"Page {page_num}: {message}" if page_num is not None else message
        super().__init__(msg, "OCR_PROCESSING_ERROR")
        self.page_num = page_num


# Image processing exceptions

class ImageProcessingError(PDFOCRException):
    """Error during image preprocessing."""

    def __init__(self, message: str, page_num: int = None):
        msg = f"Page {page_num}: {message}" if page_num is not None else message
        super().__init__(msg, "IMAGE_PROCESSING_ERROR")
        self.page_num = page_num


class ImageQualityError(PDFOCRException):
    """Image quality insufficient for processing."""

    def __init__(self, message: str, page_num: int = None):
        msg = f"Page {page_num}: {message}" if page_num is not None else message
        super().__init__(msg, "IMAGE_QUALITY_ERROR")
        self.page_num = page_num


# Job and processing exceptions

class JobError(PDFOCRException):
    """Error with job processing."""

    def __init__(self, message: str):
        super().__init__(message, "JOB_ERROR")


class JobNotFoundError(PDFOCRException):
    """Job not found."""

    def __init__(self, job_id: str):
        super().__init__(f"Job not found: {job_id}", "JOB_NOT_FOUND")
        self.job_id = job_id


class JobAlreadyRunningError(PDFOCRException):
    """Another job is already running on this PDF."""

    def __init__(self, message: str):
        super().__init__(message, "JOB_ALREADY_RUNNING")


class JobInterruptedError(PDFOCRException):
    """Job was interrupted by user."""

    def __init__(self, message: str = "Job interrupted by user"):
        super().__init__(message, "JOB_INTERRUPTED")


# Checkpoint and resume exceptions

class CheckpointError(PDFOCRException):
    """Error with checkpoint management."""

    def __init__(self, message: str):
        super().__init__(message, "CHECKPOINT_ERROR")


class CheckpointInvalidError(PDFOCRException):
    """Checkpoint data is invalid or corrupted."""

    def __init__(self, message: str):
        super().__init__(message, "CHECKPOINT_INVALID")


class CheckpointNotFoundError(PDFOCRException):
    """Checkpoint not found for job."""

    def __init__(self, job_id: str):
        super().__init__(f"Checkpoint not found: {job_id}", "CHECKPOINT_NOT_FOUND")
        self.job_id = job_id


# File and I/O exceptions

class FileOperationError(PDFOCRException):
    """Error during file operation."""

    def __init__(self, message: str):
        super().__init__(message, "FILE_OPERATION_ERROR")


class InsufficientDiskSpaceError(PDFOCRException):
    """Insufficient disk space for operation."""

    def __init__(self, required_mb: int, available_mb: int):
        msg = f"Insufficient disk space: {required_mb} MB required, {available_mb} MB available"
        super().__init__(msg, "INSUFFICIENT_DISK_SPACE")
        self.required_mb = required_mb
        self.available_mb = available_mb


class InsufficientMemoryError(PDFOCRException):
    """Insufficient RAM for operation."""

    def __init__(self, required_mb: int, available_mb: int):
        msg = f"Insufficient memory: {required_mb} MB required, {available_mb} MB available"
        super().__init__(msg, "INSUFFICIENT_MEMORY")
        self.required_mb = required_mb
        self.available_mb = available_mb


# Configuration exceptions

class ConfigurationError(PDFOCRException):
    """Configuration error."""

    def __init__(self, message: str):
        super().__init__(message, "CONFIGURATION_ERROR")


# Worker and concurrency exceptions

class WorkerError(PDFOCRException):
    """Error with worker process/thread."""

    def __init__(self, message: str):
        super().__init__(message, "WORKER_ERROR")


class QueueTimeoutError(PDFOCRException):
    """Work queue operation timed out."""

    def __init__(self, message: str):
        super().__init__(message, "QUEUE_TIMEOUT")


# GUI exceptions

class GUIError(PDFOCRException):
    """Error in GUI operation."""

    def __init__(self, message: str):
        super().__init__(message, "GUI_ERROR")
