"""
REST API for PDF OCR Converter.
Provides HTTP endpoints for OCR operations.
"""

import logging
from pathlib import Path
from typing import Optional

try:
    from flask import Flask, request, jsonify
except ImportError:
    Flask = None

from core import OCROrchestrator
from exceptions import (
    OCROrchestrationError,
    JobNotFoundError,
    JobInputError,
)

logger = logging.getLogger(__name__)


def create_app() -> Flask:
    """
    Create and configure Flask application.
    
    Returns:
        Flask app instance
    """
    if Flask is None:
        raise ImportError("Flask is required for REST API")
    
    app = Flask(__name__)
    orchestrator = OCROrchestrator()
    
    # Health check endpoint
    @app.route('/health', methods=['GET'])
    def health():
        """
        Health check endpoint.
        
        Returns:
            JSON with status
        """
        return jsonify({
            'status': 'healthy',
            'service': 'PDF OCR Converter',
        }), 200
    
    # Process PDF endpoint
    @app.route('/api/v1/process', methods=['POST'])
    def process_pdf():
        """
        Process a PDF file.
        
        Request body:
        {
            "input_pdf_path": "/path/to/input.pdf",
            "output_pdf_path": "/path/to/output.pdf",
            "languages": ["eng", "hin"],
            "num_workers": 4,
            "enable_preprocessing": true
        }
        
        Returns:
            JSON with job information
        """
        try:
            data = request.get_json()
            
            if not data:
                return jsonify({'error': 'No JSON body'}), 400
            
            # Extract parameters
            input_pdf = data.get('input_pdf_path')
            output_pdf = data.get('output_pdf_path')
            languages = data.get('languages', ['eng'])
            num_workers = data.get('num_workers')
            
            if not input_pdf or not output_pdf:
                return jsonify({
                    'error': 'Missing required fields: input_pdf_path, output_pdf_path'
                }), 400
            
            # Process PDF
            job = orchestrator.process_pdf(
                input_pdf_path=Path(input_pdf),
                output_pdf_path=Path(output_pdf),
                languages=languages,
                num_workers=num_workers,
            )
            
            return jsonify({
                'job_id': job.job_id,
                'state': job.state.value,
                'input_pdf': str(job.input_pdf_path),
                'output_pdf': str(job.output_pdf_path),
                'total_pages': job.total_pages,
                'processed_pages': job.processed_pages,
            }), 200
        
        except JobInputError as e:
            logger.error(f"Job input error: {e}")
            return jsonify({'error': str(e)}), 400
        except OCROrchestrationError as e:
            logger.error(f"Orchestration error: {e}")
            return jsonify({'error': str(e)}), 500
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return jsonify({'error': 'Internal server error'}), 500
    
    # Get job status endpoint
    @app.route('/api/v1/jobs/<job_id>', methods=['GET'])
    def get_job_status(job_id: str):
        """
        Get job status.
        
        Args:
            job_id: Job ID
        
        Returns:
            JSON with job status
        """
        try:
            status = orchestrator.get_job_status(job_id)
            
            if status is None:
                return jsonify({'error': 'Job not found'}), 404
            
            return jsonify(status), 200
        
        except Exception as e:
            logger.error(f"Error getting job status: {e}")
            return jsonify({'error': 'Internal server error'}), 500
    
    return app
