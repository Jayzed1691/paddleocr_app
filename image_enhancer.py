"""
Image Enhancement Pipeline for OCR Preprocessing
Provides various image enhancement operations to improve OCR accuracy
"""

import logging
from typing import Tuple, Optional
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter
import cv2

logger = logging.getLogger(__name__)


class ImageEnhancer:
    """
    Image enhancement pipeline for OCR preprocessing
    """

    def __init__(self):
        """Initialize image enhancer"""
        pass

    def enhance(
        self,
        image: Image.Image,
        rotation: float = 0,
        brightness: float = 1.0,
        contrast: float = 1.0,
        sharpness: float = 1.0,
        denoise: bool = False,
        deskew: bool = False,
        grayscale: bool = False,
        adaptive_threshold: bool = False
    ) -> Image.Image:
        """
        Apply enhancement pipeline to image

        Args:
            image: Input PIL Image
            rotation: Rotation angle in degrees (positive = counter-clockwise)
            brightness: Brightness factor (1.0 = no change)
            contrast: Contrast factor (1.0 = no change)
            sharpness: Sharpness factor (1.0 = no change)
            denoise: Apply denoising filter
            deskew: Auto-correct skew/tilt
            grayscale: Convert to grayscale
            adaptive_threshold: Apply adaptive thresholding

        Returns:
            Enhanced PIL Image
        """
        try:
            logger.info("Starting image enhancement pipeline")

            # Convert to RGB if needed
            if image.mode != 'RGB':
                image = image.convert('RGB')

            # Rotation
            if rotation != 0:
                image = self.rotate(image, rotation)
                logger.debug(f"Applied rotation: {rotation}°")

            # Brightness
            if brightness != 1.0:
                image = self.adjust_brightness(image, brightness)
                logger.debug(f"Applied brightness: {brightness}")

            # Contrast
            if contrast != 1.0:
                image = self.adjust_contrast(image, contrast)
                logger.debug(f"Applied contrast: {contrast}")

            # Sharpness
            if sharpness != 1.0:
                image = self.adjust_sharpness(image, sharpness)
                logger.debug(f"Applied sharpness: {sharpness}")

            # Denoise
            if denoise:
                image = self.apply_denoise(image)
                logger.debug("Applied denoising")

            # Deskew
            if deskew:
                image = self.auto_deskew(image)
                logger.debug("Applied auto-deskew")

            # Grayscale
            if grayscale:
                image = self.convert_to_grayscale(image)
                logger.debug("Converted to grayscale")

            # Adaptive threshold
            if adaptive_threshold:
                image = self.apply_adaptive_threshold(image)
                logger.debug("Applied adaptive thresholding")

            logger.info("Image enhancement complete")
            return image

        except Exception as e:
            logger.error(f"Error during image enhancement: {e}")
            return image  # Return original on error

    def rotate(self, image: Image.Image, angle: float) -> Image.Image:
        """
        Rotate image by specified angle

        Args:
            image: Input image
            angle: Rotation angle in degrees

        Returns:
            Rotated image
        """
        return image.rotate(angle, expand=True, fillcolor='white')

    def adjust_brightness(self, image: Image.Image, factor: float) -> Image.Image:
        """
        Adjust image brightness

        Args:
            image: Input image
            factor: Brightness factor (1.0 = no change, <1.0 = darker, >1.0 = brighter)

        Returns:
            Brightness-adjusted image
        """
        enhancer = ImageEnhance.Brightness(image)
        return enhancer.enhance(factor)

    def adjust_contrast(self, image: Image.Image, factor: float) -> Image.Image:
        """
        Adjust image contrast

        Args:
            image: Input image
            factor: Contrast factor (1.0 = no change, <1.0 = less contrast, >1.0 = more contrast)

        Returns:
            Contrast-adjusted image
        """
        enhancer = ImageEnhance.Contrast(image)
        return enhancer.enhance(factor)

    def adjust_sharpness(self, image: Image.Image, factor: float) -> Image.Image:
        """
        Adjust image sharpness

        Args:
            image: Input image
            factor: Sharpness factor (1.0 = no change, <1.0 = blur, >1.0 = sharpen)

        Returns:
            Sharpness-adjusted image
        """
        enhancer = ImageEnhance.Sharpness(image)
        return enhancer.enhance(factor)

    def apply_denoise(self, image: Image.Image) -> Image.Image:
        """
        Apply denoising filter to reduce image noise

        Args:
            image: Input image

        Returns:
            Denoised image
        """
        # Convert to numpy array
        img_array = np.array(image)

        # Apply bilateral filter (preserves edges while reducing noise)
        denoised = cv2.bilateralFilter(img_array, 9, 75, 75)

        return Image.fromarray(denoised)

    def convert_to_grayscale(self, image: Image.Image) -> Image.Image:
        """
        Convert image to grayscale

        Args:
            image: Input image

        Returns:
            Grayscale image (converted back to RGB for compatibility)
        """
        grayscale = image.convert('L')
        # Convert back to RGB for OCR compatibility
        return grayscale.convert('RGB')

    def apply_adaptive_threshold(self, image: Image.Image) -> Image.Image:
        """
        Apply adaptive thresholding for better text contrast

        Args:
            image: Input image

        Returns:
            Thresholded image
        """
        # Convert to grayscale numpy array
        gray = np.array(image.convert('L'))

        # Apply adaptive threshold
        binary = cv2.adaptiveThreshold(
            gray,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            11,  # Block size
            2    # Constant subtracted from mean
        )

        # Convert back to RGB
        binary_rgb = cv2.cvtColor(binary, cv2.COLOR_GRAY2RGB)
        return Image.fromarray(binary_rgb)

    def auto_deskew(self, image: Image.Image) -> Image.Image:
        """
        Automatically detect and correct image skew

        Args:
            image: Input image

        Returns:
            Deskewed image
        """
        try:
            # Convert to grayscale numpy array
            gray = np.array(image.convert('L'))

            # Apply threshold
            thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]

            # Find all coordinates of rotated pixels
            coords = np.column_stack(np.where(thresh > 0))

            # Compute minimum area bounding box
            angle = cv2.minAreaRect(coords)[-1]

            # Correct angle
            if angle < -45:
                angle = -(90 + angle)
            else:
                angle = -angle

            # Only deskew if angle is significant (> 0.5 degrees)
            if abs(angle) > 0.5:
                logger.info(f"Auto-deskew detected angle: {angle:.2f}°")
                return self.rotate(image, angle)
            else:
                logger.debug("No significant skew detected")
                return image

        except Exception as e:
            logger.warning(f"Auto-deskew failed: {e}")
            return image

    def detect_rotation_angle(self, image: Image.Image) -> float:
        """
        Detect document rotation angle

        Args:
            image: Input image

        Returns:
            Detected rotation angle in degrees
        """
        try:
            gray = np.array(image.convert('L'))
            thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
            coords = np.column_stack(np.where(thresh > 0))
            angle = cv2.minAreaRect(coords)[-1]

            if angle < -45:
                angle = -(90 + angle)
            else:
                angle = -angle

            return angle
        except:
            return 0.0

    def create_comparison(
        self,
        original: Image.Image,
        enhanced: Image.Image
    ) -> Image.Image:
        """
        Create side-by-side comparison of original and enhanced images

        Args:
            original: Original image
            enhanced: Enhanced image

        Returns:
            Combined comparison image
        """
        # Resize to same height
        max_height = max(original.height, enhanced.height)

        if original.height != max_height:
            original = original.resize(
                (int(original.width * max_height / original.height), max_height)
            )

        if enhanced.height != max_height:
            enhanced = enhanced.resize(
                (int(enhanced.width * max_height / enhanced.height), max_height)
            )

        # Create combined image
        total_width = original.width + enhanced.width + 20  # 20px gap
        combined = Image.new('RGB', (total_width, max_height), color='white')

        # Paste images
        combined.paste(original, (0, 0))
        combined.paste(enhanced, (original.width + 20, 0))

        return combined
