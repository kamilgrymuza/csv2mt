"""
Centralized Encoding Detection Utility

This module provides a single source of truth for detecting file encodings
across the entire codebase. It uses charset-normalizer for accurate detection
and fails explicitly if confidence is below the required threshold.

Usage:
    from app.services.encoding_detector import detect_encoding

    with open('file.csv', 'rb') as f:
        content = f.read()

    encoding = detect_encoding(content)
    text = content.decode(encoding)
"""

from typing import Optional
from charset_normalizer import from_bytes


class EncodingDetectionError(Exception):
    """Raised when encoding cannot be detected with sufficient confidence"""
    pass


def detect_encoding(
    content: bytes,
    min_confidence: float = 0.7,
    filename: Optional[str] = None,
    prioritize_encodings: Optional[list[str]] = None
) -> str:
    """
    Detect the encoding of file content with high confidence.

    This function uses charset-normalizer to statistically analyze the byte
    content and determine the most likely encoding. If the confidence is below
    the threshold, it raises an exception rather than guessing.

    Args:
        content: Raw bytes from the file
        min_confidence: Minimum confidence threshold (0.0 to 1.0). Default 0.7
        filename: Optional filename for better error messages
        prioritize_encodings: Optional list of encoding names to prioritize when
                            confidence scores are close (within 5%)

    Returns:
        The detected encoding name (e.g., 'utf-8', 'windows-1250')

    Raises:
        EncodingDetectionError: If encoding cannot be detected with sufficient confidence
        ValueError: If content is empty or invalid

    Examples:
        >>> with open('file.csv', 'rb') as f:
        ...     content = f.read()
        >>> encoding = detect_encoding(content)
        >>> text = content.decode(encoding)
    """
    if not content:
        raise ValueError("Cannot detect encoding of empty content")

    # Use charset-normalizer to detect encoding
    results = from_bytes(content)

    if not results:
        file_info = f" for file '{filename}'" if filename else ""
        raise EncodingDetectionError(
            f"Could not detect encoding{file_info}. "
            "The file may be corrupted or in an unsupported format."
        )

    # Get the best match
    best_match = results.best()

    if best_match is None:
        file_info = f" for file '{filename}'" if filename else ""
        raise EncodingDetectionError(
            f"Could not detect encoding{file_info}. "
            "No encoding matched with sufficient confidence."
        )

    encoding = best_match.encoding
    confidence = best_match.coherence

    # If we have prioritized encodings, check if any have similar confidence
    if prioritize_encodings:
        for result in results:
            # If a prioritized encoding is within 5% confidence of the best match
            if result.encoding in prioritize_encodings:
                confidence_diff = abs(confidence - result.coherence)
                if confidence_diff < 0.05:  # Within 5%
                    # Use the prioritized encoding instead
                    encoding = result.encoding
                    confidence = result.coherence
                    break

    # Check confidence threshold
    if confidence < min_confidence:
        file_info = f" for file '{filename}'" if filename else ""
        raise EncodingDetectionError(
            f"Encoding detection confidence too low{file_info}.\n"
            f"Detected: {encoding} with {confidence:.1%} confidence\n"
            f"Required: {min_confidence:.1%} minimum confidence\n"
            f"The file encoding cannot be determined reliably. "
            f"Please ensure the file is properly encoded or specify the encoding manually."
        )

    return encoding


def decode_file_content(
    content: bytes,
    min_confidence: float = 0.7,
    filename: Optional[str] = None,
    prioritize_encodings: Optional[list[str]] = None
) -> tuple[str, str]:
    """
    Detect encoding and decode file content in one step.

    This is a convenience function that combines encoding detection and
    decoding into a single operation.

    Args:
        content: Raw bytes from the file
        min_confidence: Minimum confidence threshold (0.0 to 1.0). Default 0.7
        filename: Optional filename for better error messages
        prioritize_encodings: Optional list of encoding names to prioritize when
                            confidence scores are close (within 5%)

    Returns:
        Tuple of (decoded_text, detected_encoding)

    Raises:
        EncodingDetectionError: If encoding cannot be detected with sufficient confidence
        ValueError: If content is empty or invalid

    Examples:
        >>> with open('file.csv', 'rb') as f:
        ...     content = f.read()
        >>> text, encoding = decode_file_content(content)
        >>> print(f"Decoded as {encoding}")
    """
    encoding = detect_encoding(content, min_confidence, filename, prioritize_encodings)

    try:
        text = content.decode(encoding)
    except (UnicodeDecodeError, LookupError) as e:
        file_info = f" for file '{filename}'" if filename else ""
        raise EncodingDetectionError(
            f"Failed to decode file{file_info} using detected encoding '{encoding}': {e}"
        )

    return text, encoding
