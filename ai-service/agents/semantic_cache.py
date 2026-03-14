import os
import json
import numpy as np
import threading
from typing import Dict, Optional, Tuple
from sentence_transformers import SentenceTransformer
import faiss

CACHE_DIR = os.path.join(os.path.dirname(__file__), "..", ".cache", "semantic")
os.makedirs(CACHE_DIR, exist_ok=True)

INDEX_PATH = os.path.join(CACHE_DIR, "faiss.index")
METADATA_PATH = os.path.join(CACHE_DIR, "metadata.json")

class SemanticCache:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(SemanticCache, cls).__new__(cls)
                cls._instance._init_cache()
            return cls._instance

    def _init_cache(self):
        print("[SemanticCache] Initializing lightning-fast embedding model (all-MiniLM-L6-v2)...")
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.embedding_dim = self.model.get_sentence_embedding_dimension()
        self.index = None
        self.metadata = []
        self._load_index()

    def _load_index(self):
        if os.path.exists(INDEX_PATH) and os.path.exists(METADATA_PATH):
            try:
                self.index = faiss.read_index(INDEX_PATH)
                with open(METADATA_PATH, "r") as f:
                    self.metadata = json.load(f)
                print(f"[SemanticCache] Loaded existing FAISS index with {self.index.ntotal} records.")
            except Exception as e:
                print(f"[SemanticCache] Failed to load index: {e}. Starting fresh.")
                self.index = faiss.IndexFlatIP(self.embedding_dim)  # Inner product for cosine similarity (if normalized)
                self.metadata = []
        else:
            self.index = faiss.IndexFlatIP(self.embedding_dim)
            self.metadata = []

    def _save_index(self):
        faiss.write_index(self.index, INDEX_PATH)
        with open(METADATA_PATH, "w") as f:
            json.dump(self.metadata, f)

    def _build_text_representation(self, patient_state: Dict) -> str:
        symptoms = str(patient_state.get("symptoms_text", "")).strip().lower()
        history = str(patient_state.get("medical_history_text", "")).strip().lower()
        age = patient_state.get("age", "")
        gender = str(patient_state.get("gender", "")).strip().lower()

        # Build a dense summary of the clinical picture
        text = f"symptoms: {symptoms}. "
        if history:
            text += f"history: {history}. "
        if age:
            text += f"age: {age}. "
        if gender:
            text += f"gender: {gender}."
        
        return text.strip()

    def add_to_cache(self, patient_state: Dict, clinical_analysis: Dict, confidence_report: Dict, data_gaps: list):
        """
        Only called when a full analysis achieves high confidence.
        """
        # Only cache if confidence is decent, e.g., >= 75%
        confidence_val = confidence_report.get("overall_confidence", 0)
        try:
            if float(confidence_val) < 75.0:
                print(f"[SemanticCache] Low confidence ({confidence_val}%), skipping cache insertion.")
                return
        except ValueError:
            return

        text_rep = self._build_text_representation(patient_state)
        if not text_rep or len(text_rep) < 10:
            return

        # Generate embedding and normalize for cosine similarity via FlatIP
        embedding = self.model.encode([text_rep])
        faiss.normalize_L2(embedding)

        # Store metadata
        record = {
            "text": text_rep,
            "clinical_analysis": clinical_analysis,
            "confidence_report": confidence_report,
            "data_gaps": data_gaps
        }

        with self._lock:
            self.index.add(embedding)
            self.metadata.append(record)
            self._save_index()
            print(f"[SemanticCache] Added new highly-confident diagnosis to cache. Total records: {self.index.ntotal}")

    def get_cached_result(self, patient_state: Dict, similarity_threshold: float = 0.95) -> Optional[Tuple[Dict, Dict, list]]:
        """
        Checks FAISS for an exact or near-exact (> 95% similarity) match.
        Returns (clinical_analysis, confidence_report, data_gaps) in ~20ms if found.
        """
        if self.index is None or self.index.ntotal == 0:
            return None

        text_rep = self._build_text_representation(patient_state)
        if not text_rep or len(text_rep) < 10:
            return None

        embedding = self.model.encode([text_rep])
        faiss.normalize_L2(embedding)

        # Search top 1 nearest neighbor
        distances, indices = self.index.search(embedding, 1)
        
        best_idx = indices[0][0]
        best_score = distances[0][0]

        if best_idx != -1 and best_score >= similarity_threshold:
            print(f"[SemanticCache] 🔥 CACHE HIT! Similarity score: {best_score:.4f}. Returning instant millisecond response.")
            match = self.metadata[best_idx]
            return (match["clinical_analysis"], match["confidence_report"], match.get("data_gaps", []))

        print(f"[SemanticCache] Miss. Best score was {best_score:.4f} (Threshold: {similarity_threshold}). Running full LLM inference...")
        return None
