"""
Application constants and configuration defaults.
"""

# Application metadata
APP_NAME = "PDF OCR Converter"
APP_VERSION = "1.0.0"
APP_AUTHOR = "PDF OCR Team"
APP_LICENSE = "MIT"

# OCR Configuration
OCR_LANGUAGES = {
    'eng': 'English',
    'hin': 'Hindi',
}
DEFAULT_LANGUAGES = ['eng', 'hin']

# Processing Configuration
DEFAULT_WORKER_COUNT = 4
MIN_WORKER_COUNT = 1
MAX_WORKER_COUNT = 16

# Memory and Resource Thresholds (in MB)
CRITICAL_RAM_THRESHOLD = 200  # Pause workers if RAM < this
WARNING_RAM_THRESHOLD = 500   # Warn if RAM < this
CRITICAL_DISK_THRESHOLD = 500  # Stop if disk < this
WARNING_DISK_THRESHOLD = 1000  # Warn if disk < this

# Per-worker resource estimates (MB)
BYTES_PER_WORKER = 200 * 1024 * 1024  # 200 MB per worker

# Queue Configuration
MAX_QUEUE_SIZE = 50
QUEUE_TIMEOUT_SECONDS = 5.0

# Page Processing
MAX_PAGE_RETRIES = 3
PAGE_PROCESSING_TIMEOUT_SECONDS = 300  # 5 minutes
OCR_TIMEOUT_SECONDS = 300

# Checkpoint Configuration
CHECKPOINT_VERSION = "1.0"
CHECKPOINT_INTERVAL = 1  # Save checkpoint every N pages

# Image Preprocessing
DEFAULT_DPI = 300  # Assumed DPI for scanned pages
MAX_PAGE_DIMENSION_POINTS = 1000  # 14 inches at 72 DPI
MIN_PAGE_DIMENSION_POINTS = 100   # 1.4 inches

# PDF Optimization
ENABLE_PDF_OPTIMIZATION = True
COMPRESSION_LEVEL = 6  # 0-9, higher = more compression

# Logging
LOG_LEVEL_DEFAULT = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Error Handling
TRANSIENT_ERRORS_RETRYABLE = [
    'TimeoutError',
    'MemoryError',
    'OSError',  # Temp file issues
]

# GUI Configuration
GUI_WINDOW_WIDTH = 800
GUI_WINDOW_HEIGHT = 900
GUI_PROGRESS_UPDATE_INTERVAL = 500  # ms

# File Operations
TEMP_DIR_PREFIX = "pdf_ocr_work_"
OUTPUT_PDF_SUFFIX = "_searchable.pdf"
CHECKPOINT_FILENAME = "checkpoint.json"
ERROR_LOG_FILENAME = "errors.json"
PROCESSING_REPORT_FILENAME = "report.json"

# Cover Page
GENERATE_COVER_PAGE_DEFAULT = False
COVER_PAGE_WIDTH_POINTS = 612  # US Letter width
COVER_PAGE_HEIGHT_POINTS = 792  # US Letter height

# Validation
MIN_PDF_FILE_SIZE = 1024  # 1 KB
MAX_PDF_FILE_SIZE = 5 * 1024 * 1024 * 1024  # 5 GB (practical limit)
MAX_PAGES_REASONABLE = 50000  # Flag PDFs with more pages
