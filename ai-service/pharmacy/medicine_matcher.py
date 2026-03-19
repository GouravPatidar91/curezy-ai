import os
import asyncio
from typing import List, Dict
from functools import lru_cache
from supabase import create_client, Client

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    pass

# Initialize Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_ANON_KEY")

_supabase: Client = None

def get_supabase() -> Client:
    global _supabase
    if _supabase is None and SUPABASE_URL and SUPABASE_KEY:
        _supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    return _supabase

# Global Model instance for fast synchronous embedding without reloading
_model = None

def get_embedding_model():
    global _model
    if _model is None:
        print("[Pharmacy] Loading embedding model into memory...")
        _model = SentenceTransformer('all-MiniLM-L6-v2')
    return _model

class MedicineMatcher:
    """
    Given a list of treatment goals (e.g. from the AI Council),
    this engine queries the Supabase vector DB to find safe,
    available Indian medicines and their generic substitutes.
    """
    
    # Drugs that are highly regulated or risky. If matched, we flag them.
    RESTRICTED_CLASSES = [
        "Benzodiazepines", "Opioid Analgesics", 
        "Antipsychotics", "Barbiturates", "Sedatives"
    ]

    def __init__(self):
        self.supabase = get_supabase()
        
    async def match_goals_to_medicines(self, treatment_goals: List[str]) -> List[Dict]:
        """
        Takes treatment goals, embeds them, and queries the database.
        Returns a deduplicated list of recommended medicines.
        """
        if not self.supabase or not hasattr(self, 'RESTRICTED_CLASSES'):
            return []

        if not treatment_goals:
            return []

        # Run embedding in a threadpool so it doesn't block the async event loop
        loop = asyncio.get_event_loop()
        
        all_matches = []
        seen_compositions = set()
        
        for goal in treatment_goals:
            # 1. Embed the goal via CPU
            vector = await loop.run_in_executor(
                None, 
                lambda g: get_embedding_model().encode(g, convert_to_numpy=True).tolist(),
                goal
            )
            
            # 2. Query Supabase RPC for this specific goal
            try:
                response = self.supabase.rpc(
                    "match_medicines",
                    {
                        "query_embedding": vector,
                        "match_threshold": 0.55, # Minimum similarity score
                        "match_count": 3
                    }
                ).execute()
                
                rows = response.data
            except Exception as e:
                print(f"[Pharmacy Vector Search Error]: {e}")
                rows = []
                
            # 3. Process the results, apply safety filters, and prevent duplicate APIs
            for row in rows:
                comp = row.get("short_composition1")
                
                # Deduplication logic (if we already recommended Paracetamol for fever, don't recommend it again for headaches)
                if comp and comp in seen_compositions:
                    continue
                if comp:
                    seen_compositions.add(comp)
                
                # Safety Overrides
                requires_override = False
                action_class = str(row.get("therapeutic_action_class", ""))
                if any(r.lower() in action_class.lower() for r in self.RESTRICTED_CLASSES):
                    requires_override = True
                
                # Consolidate the match
                match_data = {
                    "goal_addressed": goal,
                    "brand_name": row.get("name"),
                    "active_ingredients": comp,
                    "price_rs": row.get("price"),
                    "action_class": action_class,
                    "requires_doctor_override": requires_override,
                    "substitutes": [
                        s for s in [row.get("substitute0"), row.get("substitute1")] if s
                    ],
                    "confidence_score": round((row.get("similarity", 0) * 100), 1)
                }
                all_matches.append(match_data)
                
        return all_matches
