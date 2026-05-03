import time
from typing import Dict, List, Optional
import json

class LatencyTracker:
    """
    Curezy AI Latency Tracking System (CLT).
    Tracks named intervals and provides a structured breakdown for monitoring.
    """
    def __init__(self):
        self.start_time = time.time()
        self.checkpoints: List[Dict] = []
        self.model_latencies: List[Dict] = []
        self._last_checkpoint = self.start_time

    def mark(self, name: str):
        """Mark a checkpoint and record time since last mark."""
        now = time.time()
        duration = round(now - self._last_checkpoint, 3)
        total_elapsed = round(now - self.start_time, 3)
        self.checkpoints.append({
            "phase": name,
            "duration_s": duration,
            "total_s": total_elapsed
        })
        self._last_checkpoint = now
        # print(f"[CLT] Phase '{name}' took {duration}s (Total: {total_elapsed}s)")

    def record_model(self, model_name: str, duration: float, input_chars: int, output_chars: int):
        """Record specific AI model performance."""
        self.model_latencies.append({
            "model": model_name,
            "duration_s": round(duration, 3),
            "input_len": input_chars,
            "output_len": output_chars,
            "chars_per_sec": round(output_chars / duration, 1) if duration > 0 else 0
        })

    def get_breakdown(self) -> Dict:
        """Returns the full latency report."""
        return {
            "total_duration_s": round(time.time() - self.start_time, 3),
            "phases": self.checkpoints,
            "models": self.model_latencies
        }

    def log_summary(self):
        """Prints a human-readable summary to the console."""
        summary = self.get_breakdown()
        print("\n" + "="*50)
        print(f"CUREZY AI LATENCY SUMMARY (Total: {summary['total_duration_s']}s)")
        print("-" * 50)
        for p in summary['phases']:
            print(f"  - {p['phase']:<30} : {p['duration_s']:>6}s")
        if summary['models']:
            print("-" * 50)
            print("MODEL PERFORMANCE:")
            for m in summary['models']:
                print(f"  - {m['model']:<20} : {m['duration_s']:>6}s ({m['chars_per_sec']} chars/s)")
        print("="*50 + "\n")
