"""
scripts/ingest_medicines.py
===========================
Reads the Indian Medicines CSV dataset, generates semantic vector embeddings
using a local open-source model (free & fast), and pushes the rows in chunks
to the Supabase Postgres database.

Requirements:
pip install pandas sentence-transformers supabase python-dotenv tqdm
"""

import os
import argparse
import pandas as pd
import numpy as np
from tqdm import tqdm
from dotenv import load_dotenv
from supabase import create_client, Client

# Use a fast, local embedding model (no API costs)
# Output vector size is 384 dimensions
EMBEDDING_MODEL_NAME = 'all-MiniLM-L6-v2'

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    print("Missing sentence-transformers. Run: pip install sentence-transformers")
    exit(1)

# Load environment variables
import dotenv
dotenv.load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ Critical Error: Missing SUPABASE_URL or SUPABASE_KEY in .env file.")
    print("Please set them and try again.")
    exit(1)


def parse_csv_to_dicts(csv_path: str):
    """Load and clean the CSV data."""
    print(f"📄 Loading CSV {csv_path}...")
    try:
        # Load CSV, treating empty fields as None so Supabase inserts NULL
        df = pd.read_csv(csv_path)
        df = df.replace({np.nan: None})
        
        # We need to map boolean-like columns correctly
        if 'Is_discontinued' in df.columns:
            df['Is_discontinued'] = df['Is_discontinued'].apply(
                lambda x: True if str(x).upper() == 'TRUE' else False
            )
            
        if 'Habit Forming' in df.columns:
            df['Habit Forming'] = df['Habit Forming'].apply(
                lambda x: True if str(x).upper() == 'YES' else False
            )
            
        # Clean up commas in price strings if they exist, to float
        if 'price(₹)' in df.columns:
            df['price(₹)'] = df['price(₹)'].replace(r'[^\d.]', '', regex=True)
            df['price(₹)'] = pd.to_numeric(df['price(₹)'], errors='coerce')
            df['price(₹)'] = df['price(₹)'].replace({np.nan: None})
            
        return df.to_dict('records')
    except Exception as e:
        print(f"❌ Failed to load CSV: {e}")
        exit(1)


def generate_search_string(row: dict) -> str:
    """
    Builds the logical string that the AI will 'read' during a vector search.
    We combine the core uses and the primary composition.
    """
    parts = []
    use = row.get("Consolidate use0")
    if use: 
        parts.append(f"Primary Indication: {use}")
        
    comp = row.get("short_composition1")
    if comp:
        parts.append(f"Composition: {comp}")
        
    ac_class = row.get("Therapeutic Action Class")
    if ac_class:
        parts.append(f"Class: {ac_class}")
        
    return " | ".join(parts)[:1000] # clamp length just in case


def main():
    parser = argparse.ArgumentParser(description="Ingest Medicine CSV to Supabase with Vector Embeddings")
    parser.add_argument("csv_path", type=str, help="Path to your Indian Medicines CSV file")
    parser.add_argument("--batch-size", type=int, default=250, help="Number of rows per Supabase insert (batch size)")
    args = parser.parse_args()

    # 1. Init external connections
    print("🔌 Connecting to Supabase...")
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    print(f"🧠 Loading free local Embedding Model ({EMBEDDING_MODEL_NAME})...")
    # This downloads ~80MB the first time it runs, then runs from cache
    model = SentenceTransformer(EMBEDDING_MODEL_NAME)
    
    # 2. Parse data
    records = parse_csv_to_dicts(args.csv_path)
    total_records = len(records)
    print(f"📊 Found {total_records} medicine rows.")

    batch_size = args.batch_size
    
    print("🚀 Starting Ingestion Pipeline (Embedding + Upload)...")
    
    # Process in batches
    for i in tqdm(range(0, total_records, batch_size), desc="Ingesting Batches"):
        batch_records = records[i : i + batch_size]
        
        db_rows = []
        # Pre-compute text to embed for this batch
        texts_to_embed = []
        
        for row in batch_records:
            search_text = generate_search_string(row)
            texts_to_embed.append(search_text)
            
            # Map CSV headers to our Postgres table column names
            db_row = {
                "csv_id": row.get("id"),
                "name": row.get("name"),
                "price": row.get("price(₹)"),
                "is_discontinued": row.get("Is_discontinued"),
                "manufacturer_name": row.get("manufacturer_name"),
                "type": row.get("type"),
                "pack_size_label": row.get("pack_size_label"),
                "short_composition1": row.get("short_composition1"),
                "short_composition2": row.get("short_composition2"),
                "substitute0": row.get("substitute0"),
                "substitute1": row.get("substitute1"),
                "substitute2": row.get("substitute2"),
                "substitute3": row.get("substitute3"),
                "substitute4": row.get("substitute4"),
                "consolidate_use0": row.get("Consolidate use0"),
                "use1": row.get("use1"),
                "use2": row.get("use2"),
                "use3": row.get("use3"),
                "use4": row.get("use4"),
                "chemical_class": row.get("Chemical Class"),
                "habit_forming": row.get("Habit Forming"),
                "therapeutic_action_class": row.get("Therapeutic Action Class"),
                "search_text": search_text,
                # use_embedding will be appended after batch embed
            }
            db_rows.append(db_row)
            
        # Generate embeddings in one fast batch (happens locally on CPU/GPU instantly)
        embeddings = model.encode(texts_to_embed, convert_to_numpy=True)
        
        # Attach the embeddings to our database rows
        for idx, embedding in enumerate(embeddings):
            # Postgres pgvector expects a Python list of floats
            db_rows[idx]["use_embedding"] = embedding.tolist()
            
        # Push this batch to Supabase
        try:
            # Insert the rows (requires no unique constraints on csv_id)
            supabase.table("medicines").insert(db_rows).execute()
        except Exception as e:
            print(f"\n❌ Error inserting batch {i} to {i+batch_size}:")
            print(str(e))
            # Continue to next batch instead of crashing the whole 50k run
            
    print("✅ Ingestion fully complete! The Medicine Table is ready for RAG.")


if __name__ == "__main__":
    main()
