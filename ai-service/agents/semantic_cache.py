import os
import json
from typing import Dict, Optional, Tuple
from sentence_transformers import SentenceTransformer
import numpy as np
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

class SemanticCache:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SemanticCache, cls).__new__(cls)
            cls._instance._init_cache()
        return cls._instance

    def _init_cache(self):
        print("[SemanticCache] Initializing pgvector embedding model (all-MiniLM-L6-v2)...")
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        
        url: str = os.getenv("SUPABASE_URL", "")
        key: str = os.getenv("SUPABASE_KEY", "")
        if not url or not key:
            print("[SemanticCache] Supabase URL or Key missing. Semantic cache disabled.")
            self.supabase = None
        else:
            self.supabase: Client = create_client(url, key)

    def _build_text_representation(self, patient_state: Dict) -> str:
        symptoms = str(patient_state.get("symptoms_text", "")).strip().lower()
        history = str(patient_state.get("medical_history_text", "")).strip().lower()
        age = patient_state.get("age", "")
        gender = str(patient_state.get("gender", "")).strip().lower()

        text = f"symptoms: {symptoms}. "
        if history: text += f"history: {history}. "
        if age: text += f"age: {age}. "
        if gender: text += f"gender: {gender}."
        
        return text.strip()

    def add_to_cache(self, patient_state: Dict, clinical_analysis: Dict, confidence_report: Dict, data_gaps: list):
        if not self.supabase: return
        
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

        # Generate embedding and normalize for inner product
        embedding = self.model.encode(text_rep)
        embedding = embedding / np.linalg.norm(embedding)
        embedding_list = embedding.tolist()

        record = {
            "text_rep": text_rep,
            "embedding": embedding_list,
            "clinical_analysis": clinical_analysis,
            "confidence_report": confidence_report,
            "data_gaps": data_gaps
        }

        try:
            self.supabase.table("semantic_cache").insert(record).execute()
            print(f"[SemanticCache] Added highly-confident diagnosis to Supabase pgvector.")
        except Exception as e:
            print(f"[SemanticCache] Insert error: {e}")

    def get_cached_result(self, patient_state: Dict, similarity_threshold: float = 0.95) -> Optional[Tuple[Dict, Dict, list]]:
        if not self.supabase: return None

        text_rep = self._build_text_representation(patient_state)
        if not text_rep or len(text_rep) < 10: return None

        embedding = self.model.encode(text_rep)
        embedding = embedding / np.linalg.norm(embedding)
        embedding_list = embedding.tolist()

        try:
            response = self.supabase.rpc(
                "match_semantic_cache", 
                {
                    "query_embedding": embedding_list, 
                    "match_threshold": similarity_threshold, 
                    "match_count": 1
                }
            ).execute()
            
            data = response.data
            if data and len(data) > 0:
                best_score = data[0].get("similarity", 0)
                print(f"[SemanticCache] 🔥 CACHE HIT (pgvector)! Similarity score: {best_score:.4f}. Returning instant millisecond response.")
                return (data[0]["clinical_analysis"], data[0]["confidence_report"], data[0].get("data_gaps", []))
                
        except Exception as e:
            print(f"[SemanticCache] Query error: {e}")

        print(f"[SemanticCache] Miss. Running full LLM inference...")
        return None
