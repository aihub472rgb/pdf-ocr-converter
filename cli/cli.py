"""
Command-line interface for PDF OCR Converter.
"""

import logging
from pathlib import Path
from typing import Optional, List
import sys

try:
    import click
except ImportError:
    click = None

from core import OCROrchestrator
from exceptions import (
    OCROrchestrationError,
    JobInputError,
)

logger = logging.getLogger(__name__)


if click is not None:
    @click.group()
    def cli():
        """
        PDF OCR Converter - Convert scanned PDFs to searchable PDFs.
        """
        pass
    
    @cli.command()
    @click.argument('input_pdf', type=click.Path(exists=True))
    @click.argument('output_pdf', type=click.Path())
    @click.option(
        '--languages', '-l',
        multiple=True,
        default=['eng'],
        help='OCR languages (e.g., eng, hin, fra)',
    )
    @click.option(
        '--workers', '-w',
        type=int,
        default=None,
        help='Number of worker threads',
    )
    @click.option(
        '--preprocess',
        is_flag=True,
        default=True,
        help='Enable image preprocessing',
    )
    @click.option(
        '--no-preprocess',
        is_flag=True,
        help='Disable image preprocessing',
    )
    @click.option(
        '--verbose', '-v',
        is_flag=True,
        help='Verbose output',
    )
    def process(
        input_pdf: str,
        output_pdf: str,
        languages: tuple,
        workers: Optional[int],
        preprocess: bool,
        no_preprocess: bool,
        verbose: bool,
    ):
        """
        Process a PDF file for OCR.
        
        Example:
            pdf-ocr-converter process input.pdf output.pdf --languages eng hin
        """
        # Configure logging
        log_level = logging.DEBUG if verbose else logging.INFO
        logging.basicConfig(level=log_level)
        
        # Handle preprocessing flag
        if no_preprocess:
            preprocess = False
        
        try:
            click.echo(f"Processing PDF: {input_pdf}")
            click.echo(f"Languages: {', '.join(languages)}")
            
            orchestrator = OCROrchestrator()
            job = orchestrator.process_pdf(
                input_pdf_path=Path(input_pdf),
                output_pdf_path=Path(output_pdf),
                languages=list(languages),
                num_workers=workers,
            )
            
            click.echo(f"\n✓ Processing complete!")
            click.echo(f"Job ID: {job.job_id}")
            click.echo(f"Pages: {job.processed_pages}/{job.total_pages}")
            click.echo(f"Output: {job.output_pdf_path}")
            
            if job.failed_pages:
                click.echo(f"Failed pages: {len(job.failed_pages)}")
            
        except JobInputError as e:
            click.echo(f"✗ Input error: {e}", err=True)
            sys.exit(1)
        except OCROrchestrationError as e:
            click.echo(f"✗ Processing error: {e}", err=True)
            sys.exit(1)
        except Exception as e:
            click.echo(f"✗ Unexpected error: {e}", err=True)
            sys.exit(1)
    
    @cli.command()
    @click.argument('input_pdf', type=click.Path(exists=True))
    @click.option('--verbose', '-v', is_flag=True, help='Verbose output')
    def inspect(input_pdf: str, verbose: bool):
        """
        Inspect a PDF file.
        
        Shows page count, dimensions, and existing text layers.
        
        Example:
            pdf-ocr-converter inspect input.pdf
        """
        try:
            from pdf import PDFInspector
            
            log_level = logging.DEBUG if verbose else logging.INFO
            logging.basicConfig(level=log_level)
            
            click.echo(f"Inspecting PDF: {input_pdf}")
            
            inspector = PDFInspector()
            info = inspector.inspect_full(input_pdf)
            
            click.echo(f"\nPDF Information:")
            click.echo(f"  Pages: {info['page_count']}")
            click.echo(f"  With text layer: {info['estimated_text_pages']}")
            click.echo(f"  Needs OCR: {info['page_count'] - info['estimated_text_pages']}")
            
            if verbose:
                click.echo(f"\n  Average page size: {info['avg_page_width']:.0f}x{info['avg_page_height']:.0f} pt")
                click.echo(f"  Estimated size: {info['total_size_mb']:.1f} MB")
        
        except Exception as e:
            click.echo(f"✗ Error: {e}", err=True)
            sys.exit(1)
    
    def main():
        """
        Main entry point for CLI.
        """
        cli()

else:
    def main():
        """Dummy main if click not available."""
        print("Click is required for CLI. Install with: pip install click")
        sys.exit(1)
