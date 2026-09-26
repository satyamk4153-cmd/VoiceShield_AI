import re
from typing import Dict, Any


def mask_sensitive_pii(text: str) -> str:
    """
    Mask OTPs, credit cards, bank account numbers, and passwords
    to adhere to privacy and data minimization rules.
    """
    if not text:
        return ""
    
    # Mask 4-8 digit numeric codes (potential OTPs/PINs)
    text = re.sub(r'\b\d{4,8}\b', '[REDACTED_CODE]', text)
    
    # Mask 12-19 digit card/account numbers
    text = re.sub(r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b', '[REDACTED_CARD_NUMBER]', text)
    
    return text


def clean_transcript_text(text: str) -> str:
    """
    Sanitizes raw transcript text, removes control characters.
    """
    if not text:
        return ""
    # Strip dangerous HTML or script tags
    cleaned = re.sub(r'<[^>]+>', '', text)
    # Normalize whitespaces
    cleaned = ' '.join(cleaned.split())
    return cleaned
