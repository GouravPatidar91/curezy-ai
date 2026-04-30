import re
from typing import Any, Dict

# Regex patterns for common PHI in India
PHONE_PATTERN = re.compile(r'\b(?:\+91|91)?[6789]\d{9}\b')
AADHAR_PATTERN = re.compile(r'\b\d{4}\s?\d{4}\s?\d{4}\b')
EMAIL_PATTERN = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')

def scrub_text(text: str) -> str:
    """Redact PHI from a text string."""
    if not isinstance(text, str):
        return text
    
    text = PHONE_PATTERN.sub("[REDACTED_PHONE]", text)
    text = AADHAR_PATTERN.sub("[REDACTED_AADHAR]", text)
    text = EMAIL_PATTERN.sub("[REDACTED_EMAIL]", text)
    return text

def scrub_patient_state(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recursively scrub a patient state dictionary.
    Ensures that any PHI is removed before logging or DB persistence.
    """
    scrubbed = {}
    for key, value in state.items():
        if key in ("patient_name", "phone", "email", "aadhar"):
            scrubbed[key] = "[REDACTED]"
            continue
            
        if isinstance(value, str):
            scrubbed[key] = scrub_text(value)
        elif isinstance(value, list):
            scrubbed[key] = [scrub_text(v) if isinstance(v, str) else v for v in value]
        elif isinstance(value, dict):
            scrubbed[key] = scrub_patient_state(value)
        else:
            scrubbed[key] = value
            
    return scrubbed
