import os
from sentence_transformers import SentenceTransformer
from supabase import create_client, Client

class RAGRetriever:
    """
    Retrieves clinical guidelines and medical knowledge from Supabase pgvector
    based on semantic similarity to patient symptoms.
    """
    def __init__(self):
        self.enabled = False # Initialize first to prevent AttributeErrors
        self.supabase_url = os.getenv("SUPABASE_URL")
        # Support both naming conventions
        self.supabase_key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_KEY")
        
        if not self.supabase_url or not self.supabase_key:
            print("[RAG] Supabase credentials missing. RAG is disabled.")
            self.supabase = None
            return
            
        try:
            self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
            # Load the same lightweight embedding model used for Semantic Cache
            print("[RAG] Loading embedding model...")
            self.model = SentenceTransformer('all-MiniLM-L6-v2')
            self.enabled = True
        except Exception as e:
            print(f"[RAG] Failed to initialize: {e}")
            self.enabled = False

    def retrieve_guidelines(self, symptoms_text: str, top_k: int = 3, threshold: float = 0.5) -> str:
        """
        Embeds the symptoms and fetches relevant guidelines.
        Returns a formatted string of context for the LLM.
        """
        if not self.supabase:
            return ""
            
        try:
            # 1. Generate query embedding (ensure input is a single string)
            embedding = self.model.encode(str(symptoms_text)).tolist()
            
            # 2. Query Supabase RPC
            response = self.supabase.rpc(
                "match_medical_knowledge",
                {
                    "query_embedding": embedding,
                    "match_threshold": threshold,
                    "match_count": top_k
                }
            ).execute()
            
            results = response.data
            if not results:
                return ""
                
            # 3. Format context
            context_str = "--- CLINICAL GUIDELINES (RAG) ---\n"
            for item in results:
                context_str += f"Title: {item['title']}\n"
                context_str += f"Source: {item['source']}\n"
                context_str += f"Guidelines: {item['content']}\n\n"
                
            return context_str.strip()
            
        except Exception as e:
            print(f"[RAG] Error retrieving knowledge: {e}")
            return ""
