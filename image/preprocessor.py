"""
Image preprocessing module.
Prepares scanned page images for OCR.
"""

from typing import Optional
import logging
import numpy as np

try:
    import cv2
except ImportError:
    cv2 = None

from dataclasses import dataclass
from exceptions import ImageProcessingError

logger = logging.getLogger(__name__)


@dataclass
class PreprocessingConfig:
    """Image preprocessing configuration."""
    enable_deskew: bool = True
    enable_denoise: bool = True
    enable_contrast: bool = True
    enable_threshold: bool = False
    preserve_quality: bool = True


class ImagePreprocessor:
    """
    Preprocesses scanned page images to improve OCR quality.
    
    Techniques:
    1. Deskew: Detect and correct page rotation
    2. Denoise: Remove scan artifacts and noise
    3. Contrast Enhancement: Improve text clarity
    4. Thresholding: Optional B&W conversion
    
    All preprocessing is optional and conservative to preserve visual quality.
    """

    def __init__(self):
        """Initialize preprocessor."""
        if cv2 is None:
            raise ImportError("OpenCV (cv2) is required for image preprocessing")

    def preprocess(
        self,
        image: np.ndarray,
        config: Optional[PreprocessingConfig] = None,
    ) -> np.ndarray:
        """
        Apply preprocessing pipeline to image.
        
        Args:
            image: Input image as numpy array (RGB or grayscale)
            config: Preprocessing configuration
        
        Returns:
            Preprocessed image
        
        Raises:
            ImageProcessingError: If preprocessing fails
        """
        if config is None:
            config = PreprocessingConfig()
        
        try:
            result = image.copy()
            
            # Convert to grayscale if needed for processing
            if len(result.shape) == 3 and result.shape[2] == 3:
                gray = cv2.cvtColor(result, cv2.COLOR_RGB2GRAY)
            else:
                gray = result
            
            # 1. Deskew
            if config.enable_deskew:
                gray = self._deskew(gray)
            
            # 2. Denoise
            if config.enable_denoise:
                gray = self._denoise(gray)
            
            # 3. Contrast enhancement
            if config.enable_contrast:
                gray = self._enhance_contrast(gray)
            
            # 4. Thresholding (optional)
            if config.enable_threshold:
                gray = self._threshold(gray)
            
            # Convert back to RGB if needed
            if len(image.shape) == 3 and image.shape[2] == 3:
                result = cv2.cvtColor(gray, cv2.COLOR_GRAY2RGB)
            else:
                result = gray
            
            logger.debug(f"Preprocessing complete: {result.shape}")
            return result
        
        except Exception as e:
            raise ImageProcessingError(f"Preprocessing failed: {e}")

    def _deskew(self, gray_image: np.ndarray) -> np.ndarray:
        """
        Detect and correct page skew/rotation.
        
        Args:
            gray_image: Grayscale image
        
        Returns:
            Deskewed image
        """
        try:
            # Detect edges
            edges = cv2.Canny(gray_image, 100, 200)
            
            # Hough line detection
            lines = cv2.HoughLines(edges, 1, np.pi/180, 100)
            
            if lines is None or len(lines) == 0:
                logger.debug("No skew detected")
                return gray_image
            
            # Calculate angle from lines
            angles = []
            for line in lines:
                rho, theta = line[0]
                # Convert to degrees
                angle = (theta * 180 / np.pi) - 90
                if -45 <= angle <= 45:
                    angles.append(angle)
            
            if not angles:
                return gray_image
            
            # Use median angle
            median_angle = np.median(angles)
            
            if abs(median_angle) < 1.0:  # Threshold to avoid over-rotation
                logger.debug(f"Skew corrected: {median_angle:.2f}°")
                return gray_image
            
            # Rotate image
            h, w = gray_image.shape
            center = (w // 2, h // 2)
            rotation_matrix = cv2.getRotationMatrix2D(center, median_angle, 1.0)
            rotated = cv2.warpAffine(
                gray_image,
                rotation_matrix,
                (w, h),
                borderMode=cv2.BORDER_REPLICATE,
            )
            
            logger.debug(f"Image deskewed by {median_angle:.2f}°")
            return rotated
        
        except Exception as e:
            logger.warning(f"Deskew failed: {e}")
            return gray_image

    def _denoise(self, gray_image: np.ndarray) -> np.ndarray:
        """
        Remove noise from image.
        
        Args:
            gray_image: Grayscale image
        
        Returns:
            Denoised image
        """
        try:
            # Use bilateral filter (preserves edges while removing noise)
            denoised = cv2.bilateralFilter(
                gray_image,
                d=9,              # Diameter of pixel neighborhood
                sigmaColor=75,    # Filter sigma in the color space
                sigmaSpace=75,    # Filter sigma in the coordinate space
            )
            logger.debug("Image denoised")
            return denoised
        except Exception as e:
            logger.warning(f"Denoise failed: {e}")
            return gray_image

    def _enhance_contrast(self, gray_image: np.ndarray) -> np.ndarray:
        """
        Enhance image contrast for better text visibility.
        
        Uses CLAHE (Contrast Limited Adaptive Histogram Equalization).
        
        Args:
            gray_image: Grayscale image
        
        Returns:
            Contrast-enhanced image
        """
        try:
            # Create CLAHE object
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(gray_image)
            logger.debug("Contrast enhanced")
            return enhanced
        except Exception as e:
            logger.warning(f"Contrast enhancement failed: {e}")
            return gray_image

    def _threshold(self, gray_image: np.ndarray) -> np.ndarray:
        """
        Convert image to binary (black and white).
        Uses Otsu's thresholding for automatic threshold selection.
        
        Args:
            gray_image: Grayscale image
        
        Returns:
            Binary (0 or 255) image
        """
        try:
            # Otsu's automatic thresholding
            _, binary = cv2.threshold(
                gray_image,
                0,
                255,
                cv2.THRESH_BINARY + cv2.THRESH_OTSU,
            )
            logger.debug("Image thresholded to binary")
            return binary
        except Exception as e:
            logger.warning(f"Thresholding failed: {e}")
            return gray_image

    @staticmethod
    def estimate_image_quality(image: np.ndarray) -> float:
        """
        Estimate image quality (0.0-1.0).
        
        Simple metric based on image properties.
        Higher score = higher quality.
        
        Args:
            image: Image as numpy array
        
        Returns:
            Quality score (0.0-1.0)
        """
        try:
            # Convert to grayscale if needed
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
            else:
                gray = image
            
            # Calculate Laplacian variance (blur detection)
            laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
            
            # Normalize to 0-1 range (empirically calibrated)
            quality = min(1.0, laplacian_var / 500.0)
            
            return quality
        except Exception:
            return 0.5  # Default to medium quality on error
