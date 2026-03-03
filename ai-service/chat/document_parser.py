"""
document_parser.py — Groq-powered extraction of structured medical data
from uploaded PDF, TXT, and DOCX files.
"""

import os
import json
import re
from typing import Optional
from groq import Groq
from dotenv import load_dotenv

load_dotenv()


EXTRACTION_PROMPT = """You are a medical document parser. Extract structured medical information from the document text below.

Return ONLY valid JSON with these fields (use null if not found):
{
  "patient_name": null,
  "age": null,
  "gender": null,
  "symptoms_text": null,
  "severity": null,
  "symptom_duration": null,
  "medical_history_text": null,
  "medications_text": null,
  "allergies": null,
  "lab_text": null,
  "prior_diagnosis": null,
  "doctor_notes": null
}

Rules:
- age must be an integer or null
- severity must be 1-10 integer or null
- All other fields are strings or null
- Do NOT include extra text, only the JSON object

Document text:
"""


class DocumentParser:

    def __init__(self):
        self.groq = Groq(api_key=os.getenv("GROQ_API_KEY"))
        self.model = "llama-3.3-70b-versatile"

    def extract_text_from_file(self, file_path: str) -> Optional[str]:
        """Extract raw text from PDF, TXT, or DOCX."""
        ext = os.path.splitext(file_path)[1].lower()

        if ext == ".txt":
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    return f.read()
            except Exception as e:
                print(f"[DocumentParser] TXT read error: {e}")
                return None

        elif ext == ".pdf":
            return self._extract_pdf(file_path)

        elif ext == ".docx":
            return self._extract_docx(file_path)

        else:
            print(f"[DocumentParser] Unsupported file type: {ext}")
            return None

    def _extract_pdf(self, path: str) -> Optional[str]:
        """Try pdfplumber first, fall back to pypdf."""
        try:
            import pdfplumber
            text_parts = []
            with pdfplumber.open(path) as pdf:
                for page in pdf.pages:
                    t = page.extract_text()
                    if t:
                        text_parts.append(t)
            return "\n".join(text_parts) if text_parts else None
        except ImportError:
            pass
        except Exception as e:
            print(f"[DocumentParser] pdfplumber error: {e}")

        try:
            import pypdf
            reader = pypdf.PdfReader(path)
            parts = [page.extract_text() or "" for page in reader.pages]
            return "\n".join(p for p in parts if p.strip()) or None
        except ImportError:
            pass
        except Exception as e:
            print(f"[DocumentParser] pypdf error: {e}")

        return None

    def _extract_docx(self, path: str) -> Optional[str]:
        try:
            import docx
            doc = docx.Document(path)
            return "\n".join(p.text for p in doc.paragraphs if p.text.strip())
        except ImportError:
            print("[DocumentParser] python-docx not installed")
            return None
        except Exception as e:
            print(f"[DocumentParser] docx error: {e}")
            return None

    def parse_with_groq(self, raw_text: str) -> dict:
        """Send text to Groq and extract structured medical fields."""
        # Truncate to avoid huge token usage (first 4000 chars is usually enough)
        truncated = raw_text[:4000]

        prompt = EXTRACTION_PROMPT + truncated

        try:
            response = self.groq.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=600,
                temperature=0.1
            )
            content = response.choices[0].message.content.strip()

            # Extract JSON block if wrapped in markdown
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                content = json_match.group(0)

            parsed = json.loads(content)
            # Remove null entries
            return {k: v for k, v in parsed.items() if v is not None}

        except json.JSONDecodeError as e:
            print(f"[DocumentParser] JSON decode error: {e}")
            return {}
        except Exception as e:
            print(f"[DocumentParser] Groq extraction error: {e}")
            return {}

    def process_file(self, file_path: str, filename: str) -> dict:
        """
        Full pipeline: extract text → Groq parse → return result dict.

        Returns:
          {
            "filename": str,
            "raw_text_length": int,
            "parsed_fields": dict,    # structured medical data
            "success": bool,
            "error": str or None
          }
        """
        result = {
            "filename": filename,
            "raw_text_length": 0,
            "parsed_fields": {},
            "success": False,
            "error": None
        }

        raw_text = self.extract_text_from_file(file_path)
        if not raw_text:
            result["error"] = "Could not extract text from file"
            return result

        result["raw_text_length"] = len(raw_text)
        parsed = self.parse_with_groq(raw_text)
        result["parsed_fields"] = parsed
        result["success"] = True
        return result
