import re
from typing import Tuple, Dict, Any, List


class PIIRedactionService:
    """
    Data Privacy & Redaction Pipeline.
    Masks high-risk financial, authentication, and personal identifiers
    before transcript persistence, LLM transmission, or logging.
    """

    # 1. High-risk authentication credentials: OTPs / PINs (4 to 8 digits)
    OTP_PATTERN = re.compile(r'(?i)\b(?:otp|pin|passcode|code|verification)\s*(?:is|:)?\s*(\d{4,8})\b')
    GENERIC_4_8_DIGIT = re.compile(r'\b\d{4,8}\b')

    # 2. Payment Cards (13-19 digits, formatted with spaces or hyphens)
    CARD_PATTERN = re.compile(r'\b(?:\d{4}[-\s]?){3}\d{1,4}\b')

    # 3. Bank Account Numbers (9 to 18 digits)
    BANK_ACCOUNT_PATTERN = re.compile(r'(?i)(?:account|acct|a/c)\s*(?:no\.?|number)?\s*[:#-]?\s*(\d{9,18})\b')

    # 4. Indian PAN Numbers (5 letters, 4 digits, 1 letter)
    PAN_PATTERN = re.compile(r'\b[A-Z]{5}[0-9]{4}[A-Z]{1}\b')

    # 5. Aadhaar Numbers (12 digits, optional spaces/hyphens)
    AADHAAR_PATTERN = re.compile(r'\b\d{4}[-\s]\d{4}[-\s]\d{4}\b')

    # 6. Phone Numbers (international and 10-digit national)
    PHONE_PATTERN = re.compile(r'\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b')

    # 7. Email Addresses
    EMAIL_PATTERN = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')

    @classmethod
    def redact_transcript(cls, text: str) -> Tuple[str, Dict[str, int]]:
        """
        Redacts sensitive tokens and returns the cleaned text along with
        a tally of redacted entities for audit purposes.
        """
        if not text:
            return "", {}

        redacted = text
        stats: Dict[str, int] = {}

        # Mask emails
        emails = cls.EMAIL_PATTERN.findall(redacted)
        if emails:
            stats["email"] = len(emails)
            redacted = cls.EMAIL_PATTERN.sub("[REDACTED_EMAIL]", redacted)

        # Mask cards
        cards = cls.CARD_PATTERN.findall(redacted)
        if cards:
            stats["credit_card"] = len(cards)
            redacted = cls.CARD_PATTERN.sub("[REDACTED_CARD]", redacted)

        # Mask Aadhaar
        aadhaars = cls.AADHAAR_PATTERN.findall(redacted)
        if aadhaars:
            stats["national_id"] = len(aadhaars)
            redacted = cls.AADHAAR_PATTERN.sub("[REDACTED_ID]", redacted)

        # Mask PAN
        pans = cls.PAN_PATTERN.findall(redacted)
        if pans:
            stats["tax_id"] = len(pans)
            redacted = cls.PAN_PATTERN.sub("[REDACTED_TAX_ID]", redacted)

        # Mask Bank Accounts
        accounts = cls.BANK_ACCOUNT_PATTERN.findall(redacted)
        if accounts:
            stats["bank_account"] = len(accounts)
            redacted = cls.BANK_ACCOUNT_PATTERN.sub("[REDACTED_ACCOUNT]", redacted)

        # Mask OTPs/PINs explicitly associated with keywords
        otps = cls.OTP_PATTERN.findall(redacted)
        if otps:
            stats["auth_code"] = len(otps)
            redacted = cls.OTP_PATTERN.sub(r"[REDACTED_OTP]", redacted)

        # Mask phone numbers
        phones = cls.PHONE_PATTERN.findall(redacted)
        if phones:
            stats["phone"] = len(phones)
            redacted = cls.PHONE_PATTERN.sub("[REDACTED_PHONE]", redacted)

        return redacted, stats
