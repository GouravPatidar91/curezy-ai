import hashlib
import secrets
import os
from datetime import datetime
from typing import Optional
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()


class APIKeyManager:

    def __init__(self):
        try:
            self.supabase = create_client(
                os.getenv("SUPABASE_URL"),
                os.getenv("SUPABASE_KEY")
            )
        except Exception as e:
            print(f"[APIKey] Supabase init failed: {e}")
            self.supabase = None

    def _hash_key(self, raw_key: str) -> str:
        return hashlib.sha256(raw_key.encode()).hexdigest()

    def generate_key(
        self,
        name: str,
        client: str,
        permissions: list = None,
        rate_limit: int = 100
    ) -> dict:
        # Generate key in format: curezy_live_xxxxxxxxxxxx
        raw_key = f"curezy_live_{secrets.token_hex(24)}"
        key_id = f"kid_{secrets.token_hex(8)}"
        key_hash = self._hash_key(raw_key)

        record = {
            "key_id": key_id,
            "key_hash": key_hash,
            "name": name,
            "client": client,
            "permissions": permissions or ["analyze", "preprocess"],
            "is_active": True,
            "rate_limit": rate_limit,
            "calls_today": 0,
            "total_calls": 0,
            "created_at": datetime.now().isoformat()
        }

        if self.supabase:
            try:
                self.supabase.table("api_keys").insert(record).execute()
                print(f"[APIKey] Created key for {client}: {key_id}")
            except Exception as e:
                print(f"[APIKey] Failed to save key: {e}")

        return {
            "key_id": key_id,
            "api_key": raw_key,  # shown ONCE, never stored raw
            "client": client,
            "name": name,
            "permissions": permissions or ["analyze", "preprocess"],
            "rate_limit": rate_limit,
            "warning": "Save this key now. It will never be shown again."
        }

    def validate_key(self, raw_key: str) -> Optional[dict]:
        if not self.supabase:
            return None

        try:
            key_hash = self._hash_key(raw_key)

            result = self.supabase.table("api_keys") \
                .select("*") \
                .eq("key_hash", key_hash) \
                .eq("is_active", True) \
                .execute()

            if not result.data:
                return None

            key_record = result.data[0]

            # Check rate limit
            if key_record["calls_today"] >= key_record["rate_limit"]:
                return None

            # Update usage stats
            self.supabase.table("api_keys") \
                .update({
                    "calls_today": key_record["calls_today"] + 1,
                    "total_calls": key_record["total_calls"] + 1,
                    "last_used": datetime.now().isoformat()
                }) \
                .eq("key_id", key_record["key_id"]) \
                .execute()

            return {
                "key_id": key_record["key_id"],
                "client": key_record["client"],
                "name": key_record["name"],
                "permissions": key_record["permissions"],
                "rate_limit": key_record["rate_limit"],
                "calls_today": key_record["calls_today"] + 1
            }

        except Exception as e:
            print(f"[APIKey] Validation error: {e}")
            return None

    def revoke_key(self, key_id: str) -> bool:
        if not self.supabase:
            return False
        try:
            self.supabase.table("api_keys") \
                .update({"is_active": False}) \
                .eq("key_id", key_id) \
                .execute()
            return True
        except Exception as e:
            print(f"[APIKey] Failed to revoke: {e}")
            return False

    def list_keys(self) -> list:
        if not self.supabase:
            return []
        try:
            result = self.supabase.table("api_keys") \
                .select("key_id, name, client, permissions, is_active, rate_limit, calls_today, total_calls, last_used, created_at") \
                .order("created_at", desc=True) \
                .execute()
            return result.data
        except Exception as e:
            print(f"[APIKey] Failed to list keys: {e}")
            return []