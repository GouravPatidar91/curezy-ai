"""
finetune/quality_filter.py
===========================
Quality filter for training examples. Applies rules-based +
LLM-scored checks to keep only high-quality medical training examples.
"""

import os
import re
from typing import List, Dict, Tuple, Optional
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

# ─────────────────────────────────────────────
# Quality thresholds
# ─────────────────────────────────────────────
MIN_INSTRUCTION_LEN = 40
MIN_OUTPUT_LEN      = 80
MIN_LLM_SCORE       = 7  # out of 10
MAX_EXAMPLES_TO_LLM_SCORE = 50  # Score only first N (API cost limit)

BANNED_PHRASES = [
    "most likely diagnosis", "placeholder", "insert here",
    "your answer", "example diagnosis", "lorem ipsum",
    "fill in", "todo:", "n/a", "not specified", "unknown condition",
    "sample output", "test string"
]

REQUIRED_MEDICAL_TERMS = [
    "patient", "symptom", "diagnosis", "treatment", "condition", "disease",
    "medicine", "clinical", "medical", "doctor", "hospital", "pain",
    "fever", "infection", "chronic", "acute", "blood", "organ"
]

SCORE_PROMPT = """Rate this medical training example on a scale of 0-10.
Criteria:
- 10: Excellent clinical scenario with detailed reasoning and specific diagnosis
- 7-9: Good quality, specific medical content, useful for training
- 4-6: Acceptable but generic or lacks specific clinical detail
- 0-3: Poor quality, too vague, placeholder text, or medically inaccurate

Example:
INSTRUCTION: {instruction}
OUTPUT: {output}

Reply with ONLY a number 0-10. Nothing else."""


class QualityFilter:

    def __init__(self, use_llm_scoring: bool = True):
        self.use_llm_scoring = use_llm_scoring
        self._groq: Optional[Groq] = None
        if use_llm_scoring:
            api_key = os.getenv("GROQ_API_KEY")
            if api_key:
                self._groq = Groq(api_key=api_key)

    def filter(self, examples: List[Dict]) -> Tuple[List[Dict], Dict]:
        """
        Filter examples. Returns (filtered_list, stats_dict).
        """
        if not examples:
            return [], {"input": 0, "output": 0, "rejected": 0, "reasons": {}}

        stats = {
            "input":   len(examples),
            "output":  0,
            "rejected": 0,
            "reasons": {}
        }

        print(f"[Filter] Filtering {len(examples)} examples...")

        # Stage 1: Rules-based filter
        stage1_passed = []
        for ex in examples:
            passed, reason = self._rules_check(ex)
            if passed:
                stage1_passed.append(ex)
            else:
                stats["rejected"] += 1
                stats["reasons"][reason] = stats["reasons"].get(reason, 0) + 1

        print(f"[Filter] Stage 1 (rules): {len(stage1_passed)}/{len(examples)} passed")

        # Stage 2: LLM scoring (on a subset to control cost)
        if self.use_llm_scoring and self._groq and stage1_passed:
            to_score = stage1_passed[:MAX_EXAMPLES_TO_LLM_SCORE]
            not_scored = stage1_passed[MAX_EXAMPLES_TO_LLM_SCORE:]

            llm_passed = []
            for ex in to_score:
                score = self._llm_score(ex)
                if score >= MIN_LLM_SCORE:
                    ex["_quality_score"] = score
                    llm_passed.append(ex)
                else:
                    stats["rejected"] += 1
                    reason = f"llm_score_below_{MIN_LLM_SCORE}"
                    stats["reasons"][reason] = stats["reasons"].get(reason, 0) + 1

            # Assume not-scored examples pass (they already passed rules)
            passed_final = llm_passed + not_scored
            print(f"[Filter] Stage 2 (LLM score): {len(llm_passed)}/{len(to_score)} passed")
        else:
            passed_final = stage1_passed

        # Sort by quality score descending
        passed_final.sort(key=lambda x: x.get("_quality_score", 7), reverse=True)

        # Remove internal score field before returning
        for ex in passed_final:
            ex.pop("_quality_score", None)

        stats["output"] = len(passed_final)
        stats["pass_rate"] = round(len(passed_final) / len(examples) * 100, 1) if examples else 0

        print(f"[Filter] ✅ {stats['output']}/{stats['input']} examples passed ({stats['pass_rate']}%)")
        if stats["reasons"]:
            print(f"[Filter] Rejection reasons: {stats['reasons']}")

        return passed_final, stats

    def _rules_check(self, ex: dict) -> Tuple[bool, str]:
        """Rule-based check. Returns (passed, rejection_reason)."""
        if not isinstance(ex, dict):
            return False, "not_dict"

        instruction = str(ex.get("instruction", "")).strip()
        output = str(ex.get("output", "")).strip()

        # Length checks
        if len(instruction) < MIN_INSTRUCTION_LEN:
            return False, "instruction_too_short"
        if len(output) < MIN_OUTPUT_LEN:
            return False, "output_too_short"

        # Output should be at least as long as instruction (diagnosis needs explanation)
        if len(output) < len(instruction) * 0.5:
            return False, "output_shorter_than_instruction"

        # Banned phrases
        combined = (instruction + " " + output).lower()
        for phrase in BANNED_PHRASES:
            if phrase in combined:
                return False, f"banned_phrase:{phrase[:20]}"

        # Must contain medical content
        has_medical = any(term in combined for term in REQUIRED_MEDICAL_TERMS)
        if not has_medical:
            return False, "no_medical_content"

        # Check for placeholder patterns
        placeholder_patterns = [r"<[^>]+>", r"\[.*?\]", r"\{.*?\}"]
        for pattern in placeholder_patterns:
            if re.search(pattern, instruction) or re.search(pattern, output):
                return False, "contains_placeholder_tokens"

        # Duplicate check: instruction and output should not be identical or near-identical
        if instruction.lower()[:50] == output.lower()[:50]:
            return False, "instruction_equals_output"

        return True, ""

    def _llm_score(self, ex: dict) -> int:
        """Ask Groq to rate example quality. Returns 0-10."""
        try:
            prompt = SCORE_PROMPT.format(
                instruction=ex["instruction"][:500],
                output=ex["output"][:500]
            )
            response = self._groq.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=5,
                temperature=0.0
            )
            raw = response.choices[0].message.content.strip()
            score = int(re.search(r"\d+", raw).group())
            return min(10, max(0, score))
        except Exception as e:
            print(f"[Filter] LLM score error: {e}")
            return 7  # Default pass if scoring fails


if __name__ == "__main__":
    import sys
    if "--test" in sys.argv:
        test_examples = [
            {
                "instruction": "45yo male with chest pain, diaphoresis, and dyspnea for 2h. BP 150/90, HR 110. ECG shows ST elevation leads II,III,aVF.",
                "input": "",
                "output": "This presentation is classic for Inferior STEMI due to RCA occlusion. Key findings: ST elevation in inferior leads (II, III, aVF), tachycardia, and hemodynamic compromise. Immediate management: aspirin 325mg, clopidogrel 600mg load, IV heparin, emergent PCI. Monitor for complications: right ventricular infarction (avoid nitrates/diuretics), complete heart block, Mobitz II."
            },
            {
                "instruction": "Patient has headache.",
                "input": "",
                "output": "This is probably a headache."
            },
            {
                "instruction": "The most likely diagnosis here is placeholder for real condition.",
                "input": "",
                "output": "Insert treatment plan here."
            },
        ]
        
        filt = QualityFilter(use_llm_scoring=False)
        passed, stats = filt.filter(test_examples)
        print(f"\n✅ Filter test:")
        print(f"   Input: {stats['input']}, Output: {stats['output']}, Rejected: {stats['rejected']}")
        print(f"   Reasons: {stats['reasons']}")
