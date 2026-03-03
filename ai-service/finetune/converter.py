"""
finetune/converter.py
=====================
AI JSONL Converter — Takes raw text from the parser and uses Groq
(llama-3.3-70b-versatile) to extract structured medical training examples.

Output format (Alpaca-style, compatible with Unsloth SFTTrainer):
{
  "instruction": "<symptom/question text>",
  "input": "",
  "output": "<diagnosis/answer text>"
}
"""

import os
import json
import re
from typing import List, Dict, Optional
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

CHUNK_SIZE = 3000  # chars per conversion batch
EXAMPLES_PER_CHUNK = 5  # examples to extract per chunk


EXTRACTION_SYSTEM_PROMPT = """You are a medical AI training data expert. 
Your job is to convert raw medical text into structured training examples for fine-tuning language models.

For each example, create a JSON object with:
- "instruction": A clinical scenario/question describing symptoms, patient info, findings
- "input": Always empty string ""
- "output": A detailed medical response with differential diagnosis, reasoning, and recommendations

Rules:
- Make instruction realistic and detailed (patient age, gender, symptoms, duration, history)
- Make output comprehensive (differential dx with reasoning, next steps, red flags)
- NEVER use placeholder text — use specific real medical conditions
- Each example should represent a unique clinical scenario
- Minimum output length: 100 words

Return ONLY a JSON array of examples. No other text."""


EXTRACTION_USER_TEMPLATE = """Convert this medical text into {n} training examples.
Each example must be a complete clinical scenario with diagnosis reasoning.

RAW TEXT:
{text}

Return exactly this format (JSON array only):
[
  {{
    "instruction": "Patient scenario here...",
    "input": "",
    "output": "Differential diagnosis and clinical reasoning here..."
  }},
  ...
]"""


class JSOLConverter:

    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY not set in .env")
        self.client = Groq(api_key=api_key)
        self.model = "llama-3.3-70b-versatile"

    def convert(self, raw_text: str, job_id: str = "unknown") -> List[Dict]:
        """
        Convert raw text into a list of JSONL training examples.
        Processes text in chunks for large files.
        """
        if not raw_text or not raw_text.strip():
            return []

        chunks = self._chunk_text(raw_text)
        print(f"[Converter] Processing {len(chunks)} chunks from {len(raw_text):,} chars")

        all_examples = []
        for i, chunk in enumerate(chunks):
            print(f"[Converter] Chunk {i+1}/{len(chunks)}...")
            examples = self._convert_chunk(chunk)
            all_examples.extend(examples)
            print(f"[Converter]   → {len(examples)} examples (total: {len(all_examples)})")

        print(f"[Converter] ✅ Converted to {len(all_examples)} raw training examples")
        return all_examples

    def _chunk_text(self, text: str) -> List[str]:
        """Split text into chunks of ~CHUNK_SIZE characters, respecting paragraph boundaries."""
        if len(text) <= CHUNK_SIZE:
            return [text]

        chunks = []
        paragraphs = re.split(r'\n\n+', text)
        current = ""

        for para in paragraphs:
            if len(current) + len(para) > CHUNK_SIZE and current:
                chunks.append(current.strip())
                current = para
            else:
                current += "\n\n" + para if current else para

        if current.strip():
            chunks.append(current.strip())

        return chunks

    def _convert_chunk(self, chunk: str) -> List[Dict]:
        """Call Groq to extract training examples from a text chunk."""
        n = min(EXAMPLES_PER_CHUNK, max(1, len(chunk) // 500))

        prompt = EXTRACTION_USER_TEMPLATE.format(text=chunk[:CHUNK_SIZE], n=n)

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=3000,
                temperature=0.3
            )
            raw = response.choices[0].message.content.strip()
            return self._parse_response(raw)

        except Exception as e:
            print(f"[Converter] ⚠️  Groq error: {e}")
            return []

    def _parse_response(self, raw: str) -> List[Dict]:
        """Robustly parse the JSON array from Groq response."""
        # Try direct parse
        try:
            data = json.loads(raw)
            if isinstance(data, list):
                return [self._clean_example(ex) for ex in data if self._is_valid(ex)]
        except Exception:
            pass

        # Find JSON array in response
        start = raw.find("[")
        end = raw.rfind("]") + 1
        if start != -1 and end > start:
            try:
                data = json.loads(raw[start:end])
                if isinstance(data, list):
                    return [self._clean_example(ex) for ex in data if self._is_valid(ex)]
            except Exception:
                pass

        # Try to find individual JSON objects
        examples = []
        pattern = r'\{[^{}]*"instruction"[^{}]*"output"[^{}]*\}'
        matches = re.findall(pattern, raw, re.DOTALL)
        for m in matches:
            try:
                ex = json.loads(m)
                if self._is_valid(ex):
                    examples.append(self._clean_example(ex))
            except Exception:
                pass

        if not examples:
            print(f"[Converter] ⚠️  Could not parse response: {raw[:200]}")

        return examples

    def _is_valid(self, ex: dict) -> bool:
        if not isinstance(ex, dict):
            return False
        instruction = str(ex.get("instruction", "")).strip()
        output = str(ex.get("output", "")).strip()
        return len(instruction) >= 30 and len(output) >= 50

    def _clean_example(self, ex: dict) -> Dict:
        instruction = str(ex.get("instruction", "")).strip()
        output = str(ex.get("output", "")).strip()
        # Remove placeholder text
        banned = ["most likely diagnosis", "placeholder", "insert", "example_", "your diagnosis here"]
        for b in banned:
            if b.lower() in instruction.lower() or b.lower() in output.lower():
                return None
        return {
            "instruction": instruction,
            "input": "",
            "output": output
        }

    def save_jsonl(self, examples: List[Dict], output_path: str) -> int:
        """Save examples to a .jsonl file. Returns count of saved examples."""
        # Filter None
        examples = [e for e in examples if e is not None]
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            for ex in examples:
                f.write(json.dumps(ex, ensure_ascii=False) + "\n")
        print(f"[Converter] 💾 Saved {len(examples)} examples → {output_path}")
        return len(examples)


if __name__ == "__main__":
    import sys
    if "--test" in sys.argv:
        sample = """
Patient: 45-year-old male with chest pain radiating to left arm, diaphoresis, and nausea for 2 hours.
History: Hypertension (10 years), Type 2 Diabetes, smoker (25 pack-years).
Vitals: BP 160/100, HR 110, SpO2 96%. ECG: ST elevation in leads II, III, aVF.
Troponin I elevated at 2.8 ng/mL.
Diagnosis: Inferior STEMI. Pathophysiology: RCA occlusion causing inferior wall ischemia.
Treatment: Aspirin 325mg, Clopidogrel, IV heparin, emergent PCI.

Patient: 28-year-old female presents with sudden severe headache "worst of my life", photophobia, neck stiffness, fever 39.2°C.
CSF: xanthochromia, protein elevated, glucose low, Gram stain positive for diplococci.
Diagnosis: Bacterial Meningitis (Neisseria meningitidis).
Treatment: IV Ceftriaxone 2g q12h, Dexamethasone 0.15 mg/kg q6h.
"""
        converter = JSOLConverter()
        examples = converter.convert(sample)
        print(f"\n✅ Converter test: {len(examples)} examples")
        for i, ex in enumerate(examples):
            print(f"\n--- Example {i+1} ---")
            print(f"Instruction: {ex['instruction'][:100]}...")
            print(f"Output: {ex['output'][:100]}...")
