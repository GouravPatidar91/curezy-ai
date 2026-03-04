"""
agents/diagnostic_planner.py — Diagnostic Planning Agent (Phase 4.2)
After producing the top diagnosis, generates a ranked step-by-step diagnostic plan.
Transforms Curezy from "what might be wrong" to "here's what tests to do, in what order".
Competes with Isabel DDx, DynaMed, and UpToDate clinical decision support.
"""

from typing import List, Dict


PLANNER_FEW_SHOT = """
=== EXAMPLE ===
Top diagnosis: Bacterial Meningitis (65%)
Patient: 28F, fever, neck stiffness, headache

Diagnostic plan:
1. Non-contrast CT head [IMMEDIATE] — Rule out raised ICP before LP. Do NOT delay antibiotics for CT.
2. Lumbar Puncture [IMMEDIATE after CT] — CSF analysis confirms/excludes bacterial vs viral. Key: WBC, protein, glucose, culture.
3. Blood cultures x2 [BEFORE antibiotics if possible] — Identifies causative organism for targeted antibiotic therapy.
4. IV Ceftriaxone 2g + Dexamethasone [STAT] — Empirical broad-spectrum coverage. Do not delay.
5. MRI brain [if no improvement in 48h] — Rules out cerebral abscess or herpes encephalitis.
"""

PLANNER_PROMPT = """You are a clinical decision support system. Given the top diagnosis and patient data, produce a 5-step diagnostic test-ordering plan.

RULES:
1. Each step must specify: test name, timing (IMMEDIATE/urgent/routine), and what result would tell clinicians.
2. Order tests by priority — most critical first.
3. Include treatments only if time-sensitive (e.g., antibiotics before culture results).
4. Be specific to THIS patient's data.

{few_shot}

=== YOUR CASE ===
Top diagnosis: {condition} ({probability}%)
Patient SOAP: {soap_note}

Produce 5 steps. JSON only:
{{
  "diagnostic_plan": [
    {{"step": 1, "test": "<test_name>", "timing": "<IMMEDIATE|urgent|routine>", "rationale": "<what_this_tells_us>"}},
    {{"step": 2, "test": "<test_name>", "timing": "<timing>", "rationale": "<rationale>"}},
    {{"step": 3, "test": "<test_name>", "timing": "<timing>", "rationale": "<rationale>"}},
    {{"step": 4, "test": "<test_name>", "timing": "<timing>", "rationale": "<rationale>"}},
    {{"step": 5, "test": "<test_name>", "timing": "<timing>", "rationale": "<rationale>"}}
  ],
  "immediate_action": "<single_most_urgent_next_step>"
}}"""


def build_planner_prompt(top_condition: str, probability: float, soap_note: str) -> str:
    return PLANNER_PROMPT.format(
        few_shot=PLANNER_FEW_SHOT,
        condition=top_condition,
        probability=round(probability, 1),
        soap_note=soap_note[:500],
    )


def parse_plan_output(raw: dict) -> List[Dict]:
    """Parse and validate the diagnostic plan output."""
    steps = raw.get("diagnostic_plan", [])
    immediate = raw.get("immediate_action", "")

    valid_steps = []
    for step in steps:
        if isinstance(step, dict) and step.get("test") and step.get("rationale"):
            test = str(step["test"]).strip()
            if len(test) > 5 and "<" not in test:
                valid_steps.append({
                    "step":      int(step.get("step", len(valid_steps) + 1)),
                    "test":      test,
                    "timing":    str(step.get("timing", "routine")).upper(),
                    "rationale": str(step.get("rationale", ""))[:200],
                })

    return valid_steps, immediate
