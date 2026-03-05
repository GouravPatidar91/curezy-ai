import os
import re
import json
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import Optional
import pytesseract
from PIL import Image
import pydicom
import cv2
from pydantic import BaseModel
from typing import List, Dict, Any

# Optional heavy dependencies for Render compatibility
try:
    import spacy
except ImportError:
    spacy = None

try:
    import scispacy
except ImportError:
    scispacy = None


# ─────────────────────────────────────────
# DATA MODELS
# ─────────────────────────────────────────

class LabReport(BaseModel):
    test_name: str
    value: str
    unit: str
    normal_range: str
    is_abnormal: bool

class Medication(BaseModel):
    name: str
    dose: str
    frequency: str
    duration: str
    usage_reason: Optional[str] = "unknown"

class PatientState(BaseModel):
    patient_id: str
    age: Optional[int]
    gender: Optional[str]
    symptoms: List[str]
    symptom_duration: Optional[str]
    symptom_onset: Optional[str]
    medications: List[Medication]
    lab_reports: List[LabReport]
    medical_history: List[str]
    risk_factors: List[str]
    imaging_findings: Optional[str]
    data_completeness_score: float
    missing_data: List[str]
    timestamp: str


# ─────────────────────────────────────────
# SPACY MEDICATION EXTRACTOR
# ─────────────────────────────────────────

class SpacyMedicalExtractor:
    def __init__(self):
        self.nlp = None
        
        # We also maintain a fallback keyword list for common drugs 
        # just in case the transformer misses it
        self.common_drugs = {
            "metformin": "diabetes", "insulin": "diabetes",
            "aspirin": "pain/heart", "ibuprofen": "pain/inflammation",
            "paracetamol": "fever/pain", "tylenol": "fever/pain",
            "amoxicillin": "infection", "lisinopril": "blood pressure",
            "omeprazole": "acid reflux", "losartan": "blood pressure",
            "albuterol": "asthma", "gabapentin": "nerve pain"
        }

    def _load_model(self):
        if spacy is None:
            print("[Spacy] library not installed. Falling back to keyword engine.")
            self.nlp = False
            return

        if self.nlp is None:
            try:
                self.nlp = spacy.load("en_core_web_trf")
                
                # Attempt to inject ScispaCy pipeline components for clinical entity linking
                if scispacy:
                    try:
                        from scispacy.abbreviation import AbbreviationDetector
                        from scispacy.linking import EntityLinker
                        
                        self.nlp.add_pipe("abbreviation_detector")
                        self.nlp.add_pipe("scispacy_linker", config={"resolve_abbreviations": True, "linker_name": "umls"})
                        print("[Spacy] Successfully injected ScispaCy UMLS linker into core pipeline.")
                    except (ImportError, Exception):
                        print("[Spacy] ScispaCy components failed to load. Using standard core pipeline.")
                else:
                    print("[Spacy] ScispaCy not found. Using standard core pipeline.")

            except OSError:
                print("[Spacy] Failed to load en_core_web_trf. Falling back to keyword engine.")
                self.nlp = False

    def extract(self, text: str) -> List[Medication]:
        if not text.strip():
            return []
            
        self._load_model()
        medications: Dict[str, Medication] = {}
        text_lower = text.lower()
        
        # 1. Fallback keyword extraction
        for drug, typical_reason in self.common_drugs.items():
            if drug in text_lower:
                medications[drug] = Medication(
                    name=drug.capitalize(),
                    dose="unknown", frequency="unknown",
                    duration="unknown", usage_reason=f"Likely for {typical_reason}"
                )

        # 2. SpaCy Transformer Extraction
        if self.nlp:
            doc = self.nlp(text)
            for ent in doc.ents:
                # PRODUCT or ORG tags often catch commercial drug names
                if ent.label_ in ["PRODUCT", "ORG", "CHEMICAL", "DISEASE"]:
                    # We only really want to add it if it looks like a drug 
                    # If it's a known non-drug, we skip it
                    ent_text = ent.text.lower()
                    
                    # Find dependency: what it's for 
                    # e.g. "taking aspirin for headache" -> "headache"
                    reason = "unknown"
                    for token in ent.root.head.children:
                        if token.dep_ == "prep" and token.text.lower() == "for":
                            for pobj in token.children:
                                if pobj.dep_ == "pobj":
                                    reason = pobj.text
                    
                    # ScispaCy Entity Linking enhancement:
                    # If the UMLS linker found a canonical concept, use it for clarity
                    canonical_name = ""
                    if hasattr(ent, "_") and hasattr(ent._, "kb_ents") and ent._.kb_ents:
                        linker = self.nlp.get_pipe("scispacy_linker")
                        best_cui = ent._.kb_ents[0][0] # Get CUI with highest score
                        try:
                            canonical_name = f" [{linker.kb.cui_to_entity[best_cui].canonical_name}]"
                        except Exception:
                            pass
                            
                    drug_display_name = ent.text.capitalize() + canonical_name
                    
                    if ent_text not in [m.lower() for m in medications.keys()]:
                        medications[ent_text] = Medication(
                            name=drug_display_name,
                            dose="unknown", frequency="unknown",
                            duration="unknown", usage_reason=reason
                        )

        return list(medications.values())


# ─────────────────────────────────────────
# SYMPTOM EXTRACTOR
# ─────────────────────────────────────────

class SymptomExtractor:
    def __init__(self):
        self.duration_patterns = [
            r'(\d+)\s*(day|days|week|weeks|month|months|hour|hours)',
            r'since\s+(\w+)',
            r'for\s+(\d+)\s*(day|days|week|weeks)'
        ]
        self.onset_keywords = ['sudden', 'gradual', 'acute', 'chronic', 'intermittent']

    def extract_duration(self, text: str) -> Optional[str]:
        for pattern in self.duration_patterns:
            match = re.search(pattern, text.lower())
            if match:
                return match.group(0)
        return None

    def extract_onset(self, text: str) -> Optional[str]:
        for keyword in self.onset_keywords:
            if keyword in text.lower():
                return keyword
        return None

    def extract_symptoms(self, text: str) -> List[str]:
        common_symptoms = [
            'fever', 'cough', 'cold', 'headache', 'fatigue',
            'nausea', 'vomiting', 'diarrhea', 'chest pain',
            'shortness of breath', 'dizziness', 'weakness',
            'loss of appetite', 'weight loss', 'night sweats',
            'body ache', 'sore throat', 'runny nose', 'rash',
            'abdominal pain', 'back pain', 'joint pain'
        ]
        found = []
        text_lower = text.lower()
        for symptom in common_symptoms:
            if symptom in text_lower:
                found.append(symptom)
        return found


# ─────────────────────────────────────────
# LAB REPORT PARSER
# ─────────────────────────────────────────

class LabReportParser:
    def __init__(self):
        self.lab_patterns = {
            'hemoglobin': r'h[ae]moglobin[:\s]+(\d+\.?\d*)\s*(g/dl|g/l)?',
            'wbc': r'wbc|white blood cell[:\s]+(\d+\.?\d*)',
            'rbc': r'rbc|red blood cell[:\s]+(\d+\.?\d*)',
            'platelets': r'platelet[:\s]+(\d+\.?\d*)',
            'glucose': r'glucose|sugar[:\s]+(\d+\.?\d*)\s*(mg/dl)?',
            'creatinine': r'creatinine[:\s]+(\d+\.?\d*)',
            'crp': r'crp|c-reactive protein[:\s]+(\d+\.?\d*)',
            'esr': r'esr[:\s]+(\d+\.?\d*)',
        }
        self.normal_ranges = {
            'hemoglobin': (12.0, 17.0),
            'wbc': (4000, 11000),
            'platelets': (150000, 400000),
            'glucose': (70, 100),
            'creatinine': (0.6, 1.2),
            'crp': (0, 10),
            'esr': (0, 20),
        }

    def parse_from_text(self, text: str) -> List[LabReport]:
        results = []
        text_lower = text.lower()
        for test, pattern in self.lab_patterns.items():
            match = re.search(pattern, text_lower)
            if match:
                try:
                    value = float(match.group(1))
                    normal = self.normal_ranges.get(test, (0, 999))
                    is_abnormal = value < normal[0] or value > normal[1]
                    results.append(LabReport(
                        test_name=test,
                        value=str(value),
                        unit="",
                        normal_range=f"{normal[0]}-{normal[1]}",
                        is_abnormal=is_abnormal
                    ))
                except:
                    continue
        return results


# ─────────────────────────────────────────
# OCR PROCESSOR
# ─────────────────────────────────────────

class OCRProcessor:
    def extract_text_from_image(self, image_path: str) -> str:
        try:
            img = Image.open(image_path)
            text = pytesseract.image_to_string(img)
            return text.strip()
        except Exception as e:
            return f"OCR Error: {str(e)}"

    def extract_text_from_dicom(self, dicom_path: str) -> Dict[str, Any]:
        try:
            ds = pydicom.dcmread(dicom_path)
            metadata = {
                'patient_name': str(getattr(ds, 'PatientName', 'Unknown')),
                'patient_age': str(getattr(ds, 'PatientAge', 'Unknown')),
                'study_description': str(getattr(ds, 'StudyDescription', 'Unknown')),
                'modality': str(getattr(ds, 'Modality', 'Unknown')),
                'study_date': str(getattr(ds, 'StudyDate', 'Unknown')),
            }
            return metadata
        except Exception as e:
            return {'error': str(e)}


# ─────────────────────────────────────────
# RISK FACTOR EXTRACTOR
# ─────────────────────────────────────────

class RiskFactorExtractor:
    def __init__(self):
        self.risk_factors = [
            'diabetes', 'hypertension', 'smoking', 'obesity',
            'asthma', 'copd', 'heart disease', 'kidney disease',
            'liver disease', 'hiv', 'tuberculosis', 'cancer',
            'immunocompromised', 'elderly', 'pregnancy'
        ]

    def extract(self, text: str) -> List[str]:
        found = []
        text_lower = text.lower()
        for factor in self.risk_factors:
            if factor in text_lower:
                found.append(factor)
        return found


# ─────────────────────────────────────────
# MAIN PREPROCESSOR
# ─────────────────────────────────────────

class PatientPreprocessor:
    def __init__(self):
        self.symptom_extractor = SymptomExtractor()
        self.lab_parser = LabReportParser()
        self.ocr_processor = OCRProcessor()
        self.risk_extractor = RiskFactorExtractor()
        self.spacy_extractor = SpacyMedicalExtractor()

    def calculate_completeness(self, patient_state: dict) -> tuple:
        required_fields = [
            'symptoms', 'age', 'gender',
            'medical_history', 'lab_reports', 'medications'
        ]
        missing = []
        score = 0

        if patient_state.get('symptoms'):
            score += 25
        else:
            missing.append('symptoms')

        if patient_state.get('age'):
            score += 15
        else:
            missing.append('age')

        if patient_state.get('gender'):
            score += 10
        else:
            missing.append('gender')

        if patient_state.get('lab_reports'):
            score += 25
        else:
            missing.append('lab_reports - prediction confidence would improve significantly')

        if patient_state.get('medications'):
            score += 15
        else:
            missing.append('medication history')

        if patient_state.get('medical_history'):
            score += 10
        else:
            missing.append('past medical history')

        return score, missing

    def process(
        self,
        patient_id: str,
        symptoms_text: str,
        medical_history_text: str = "",
        lab_text: str = "",
        image_path: str = None,
        dicom_path: str = None,
        age: int = None,
        gender: str = None,
        medications_text: str = ""
    ) -> PatientState:

        # Extract all components
        symptoms = self.symptom_extractor.extract_symptoms(symptoms_text)
        duration = self.symptom_extractor.extract_duration(symptoms_text)
        onset = self.symptom_extractor.extract_onset(symptoms_text)
        lab_reports = self.lab_parser.parse_from_text(lab_text) if lab_text else []
        risk_factors = self.risk_extractor.extract(
            f"{symptoms_text} {medical_history_text}"
        )
        history = [h.strip() for h in medical_history_text.split('.') if h.strip()]

        # OCR processing
        imaging_findings = None
        if image_path:
            ocr_text = self.ocr_processor.extract_text_from_image(image_path)
            imaging_findings = ocr_text
        if dicom_path:
            dicom_meta = self.ocr_processor.extract_text_from_dicom(dicom_path)
            imaging_findings = json.dumps(dicom_meta)

        # Medication parsing (via SpaCy NER + Dependency parsing)
        combined_text = f"{symptoms_text} . {medications_text}"
        medications = self.spacy_extractor.extract(combined_text)

        # Build state dict for completeness check
        state_dict = {
            'symptoms': symptoms,
            'age': age,
            'gender': gender,
            'lab_reports': lab_reports,
            'medications': medications,
            'medical_history': history
        }

        completeness_score, missing_data = self.calculate_completeness(state_dict)

        return PatientState(
            patient_id=patient_id,
            age=age,
            gender=gender,
            symptoms=symptoms,
            symptom_duration=duration,
            symptom_onset=onset,
            medications=medications,
            lab_reports=lab_reports,
            medical_history=history,
            risk_factors=risk_factors,
            imaging_findings=imaging_findings,
            data_completeness_score=completeness_score,
            missing_data=missing_data,
            timestamp=datetime.now().isoformat()
        )