import os
import re
import json
import time
import traceback
import asyncio
from collections import Counter
from typing import List, Optional, Dict, Tuple
from pydantic import BaseModel
import ollama
from dotenv import load_dotenv

# ── Knowledge & Support imports ──────────────────────────────────────────────
from knowledge.symptom_map import format_rag_block, get_red_flags
from knowledge.icd10_map import normalize_condition_name, normalize_conditions_list
from agents.soap_converter import convert_to_soap
from agents.clinical_rules import run_clinical_rules
from agents.evidence_extractor import build_evidence_prompt, extract_evidence_from_raw

# ── Phase 1 — Metacognitive Reasoning ────────────────────────────────────────
from agents.thinker import (
    build_critic_prompt, build_revision_prompt,
    parse_critique, get_must_check_conditions
)
from agents.differential_pruner import prune_conditions, get_pruning_summary
from agents.confidence_auditor import (
    build_audit_prompt, parse_audit_result, confidence_adjustment
)

# ── Phase 2 — Feedback Infrastructure ────────────────────────────────────────
from agents.quality_scorer import compute_q_score

# ── Phase 3 — Dynamic Few-Shot ────────────────────────────────────────────────
from agents.fewshot_curator import get_dynamic_examples, STATIC_EXAMPLES

# ── Phase 4 — Advanced AI ─────────────────────────────────────────────────────
from agents.diagnostic_planner import (
    build_planner_prompt, parse_plan_output
)
from agents.counterfactual_reasoner import (
    build_counterfactual_prompt, parse_counterfactual_output
)

load_dotenv()


# ─────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────

def _to_str(val) -> str:
    if isinstance(val, str):   return val
    if isinstance(val, dict):  return val.get("condition") or val.get("name") or str(val)
    if isinstance(val, list):  return ", ".join(_to_str(v) for v in val)
    return str(val)

def _safe_float(val, default: float = 0.0) -> float:
    try:    return float(val)
    except: return default

def _safe_list(val) -> list:
    return val if isinstance(val, list) else []


# ─────────────────────────────────────────
# PHASE 1.1 — JSON SCHEMA FOR GRAMMAR-CONSTRAINED GENERATION
# Prevents the model from physically outputting <placeholder> tokens
# ─────────────────────────────────────────

CONDITION_JSON_SCHEMA = {
    "type": "object",
    "required": ["doctor", "specialty", "conditions", "missing_data", "urgent_flags", "reasoning_summary"],
    "properties": {
        "doctor":     {"type": "string", "minLength": 3},
        "specialty":  {"type": "string", "minLength": 3},
        "conditions": {
            "type": "array",
            "minItems": 1,
            "maxItems": 3,
            "items": {
                "type": "object",
                "required": ["condition", "probability", "confidence", "evidence", "reasoning"],
                "properties": {
                    "condition":   {"type": "string", "minLength": 5, "maxLength": 120},
                    "probability": {"type": "number", "minimum": 1, "maximum": 99},
                    "confidence":  {"type": "number", "minimum": 1, "maximum": 99},
                    "evidence":    {"type": "array", "minItems": 1, "items": {"type": "string", "minLength": 5}},
                    "reasoning":   {"type": "string", "minLength": 10}
                }
            }
        },
        "missing_data":       {"type": "array", "items": {"type": "string"}},
        "urgent_flags":       {"type": "array", "items": {"type": "string"}},
        "reasoning_summary":  {"type": "string", "minLength": 20}
    }
}


# ─────────────────────────────────────────
# PHASE 1.2 — PLACEHOLDER SANITIZER
# ─────────────────────────────────────────

_PLACEHOLDER_RE = re.compile(r"<[^>]{1,50}>", re.IGNORECASE)
_PLACEHOLDER_EXACT = {
    "condition1","condition2","condition3","ev1","ev2","ev3",
    "r1","r2","r3","finding","diagnosis","rationale","placeholder",
    "real_disease_name_here","fill_in_condition_name","specific_diagnosis_name",
}
_VALID_FRAGS = {
    "influenza","migraine","appendicitis","gastroenteritis","meningitis",
    "pneumonia","hypertension","diabetes","asthma","bronchitis","sinusitis",
    "tonsillitis","pharyngitis","otitis","urinary","infection","anemia",
    "arthritis","myocardial","angina","arrhythmia","fibrillation",
    "hepatitis","pancreatitis","cholecystitis","colitis","gastritis",
    "peptic","hernia","vertigo","vestibular","stroke","thrombosis",
    "embolism","hemorrhage","ischemic","epilepsy","depression","anxiety",
    "thyroid","gout","osteoarthritis","kidney","renal","cystitis",
    "pyelonephritis","covid","malaria","dengue","lyme","mononucleosis",
    "encephalitis","flu","cold","rhinitis","conjunctivitis","glaucoma",
    "neuropathy","sciatica","spondylosis","sepsis","lupus","common",
    "viral","bacterial","fungal","acute","chronic","syndrome","disease",
    "failure","disorder","deficiency","upper","respiratory","lower",
}


class OutputValidator:
    def has_placeholder(self, text: str) -> bool:
        if _PLACEHOLDER_RE.search(text):
            return True
        lo = text.lower().strip()
        return lo in _PLACEHOLDER_EXACT

    def has_medical_content(self, name: str) -> bool:
        lo = name.lower()
        return any(f in lo for f in _VALID_FRAGS)

    def probabilities_flat(self, conditions: list) -> bool:
        if len(conditions) < 2: return False
        probs = [_safe_float(c.get("probability", 0)) for c in conditions]
        return (max(probs) - min(probs)) <= 2.0

    def validate(self, conditions: list) -> Tuple[bool, str]:
        if not conditions:
            return False, "No conditions"
        for c in conditions:
            name = _to_str(c.get("condition",""))
            if self.has_placeholder(name):
                return False, f"Placeholder name: '{name}'"
            if not self.has_medical_content(name):
                return False, f"Non-medical name: '{name}'"
            for ev in _safe_list(c.get("evidence",[])):
                if self.has_placeholder(_to_str(ev)):
                    return False, f"Placeholder evidence: '{ev}'"
            reasoning = _to_str(c.get("reasoning",""))
            if self.has_placeholder(reasoning):
                return False, f"Placeholder reasoning: '{reasoning[:60]}'"
        if self.probabilities_flat(conditions):
            return False, "Flat probabilities — template defaults"
        return True, "OK"


# ─────────────────────────────────────────
# COUNCIL MEMBERS
# ─────────────────────────────────────────

COUNCIL = [
    {"name":"Dr. Gemma",  "model":"alibayram/medgemma:4b",            "specialty":"General Medicine",   "role":"Primary Diagnostician", "weight":1.5, "tokens":2048},
    {"name":"Dr. OpenBio","model":"koesn/llama3-openbiollm-8b:latest", "specialty":"Biomedical Research","role":"Evidence Validator",    "weight":1.4, "tokens":2048},
    {"name":"Dr. Mistral","model":"mistral:7b",                        "specialty":"Differential Diagnosis","role":"Devil's Advocate",  "weight":1.2, "tokens":1536},
]


# ─────────────────────────────────────────
# OUTPUT MODELS
# ─────────────────────────────────────────

class ClinicalCondition(BaseModel):
    condition:   str
    probability: float
    confidence:  float
    evidence:    List[str]
    reasoning:   str

class FinalClinicalOutput(BaseModel):
    patient_id:               str
    top_3_conditions:         List[ClinicalCondition]
    consensus_confidence:     float
    agents_agreed:            bool
    council_votes:            Optional[dict]
    disagreement_details:     Optional[str]
    missing_data_suggestions: List[str]
    safety_flags:             List[str]
    doctor_review_required:   bool
    reasoning_summary:        str
    execution_time_seconds:   Optional[float]


# ─────────────────────────────────────────
# PHASE 1.1+1.2 — LLM CLIENT (Grammar-Constrained)
# ─────────────────────────────────────────

class CouncilLLMClient:

    async def query_async(self, prompt: str, model: str, num_predict: int = 2048,
                          use_json_schema: bool = False, temperature: float = 0.1) -> str:
        try:
            client  = ollama.AsyncClient()
            options = {
                "temperature":    temperature,
                "num_predict":    num_predict,
                "top_p":          0.9,
                "repeat_penalty": 1.1,
                "stop": ["USER:", "Human:", "Assistant:", "=== WORKED EXAMPLE"]
            }
            kwargs = {"model": model, "prompt": prompt, "options": options}

            # Phase 1.1: Use full JSON Schema for grammar-constrained output
            if use_json_schema:
                kwargs["format"] = CONDITION_JSON_SCHEMA
            # else: plain text for CoT prompts (we parse JSON from the output)

            response = await client.generate(**kwargs)
            return response.get("response", "{}")
        except Exception as exc:
            print(f"[Council] Error querying {model}: {exc}")
            return "{}"

    def parse_json(self, text: str) -> dict:
        """Find the last JSON object in text (handles CoT + JSON mixed output)."""
        if not text or not text.strip(): return {}
        # Strategy 1: Last braced block
        last = text.rfind("}")
        if last != -1:
            depth, start = 0, last
            for i in range(last, -1, -1):
                if text[i] == "}": depth += 1
                elif text[i] == "{":
                    depth -= 1
                    if depth == 0: start = i; break
            try:
                r = json.loads(text[start:last+1])
                if r: return r
            except: pass
        # Strategy 2: ```json block
        if "```json" in text:
            try:
                s = text[text.find("```json")+7:]
                e = s.find("```")
                if e != -1: return json.loads(s[:e].strip())
            except: pass
        # Strategy 3: Fix common issues
        try:
            s, e = text.find("{"), text.rfind("}")+1
            if s != -1 and e > s:
                chunk = text[s:e].replace("'",'"').replace("True","true").replace("False","false").replace("None","null")
                return json.loads(chunk)
        except: pass
        print(f"[Council] JSON parse failed on: {text[:150]}")
        return {}


# ─────────────────────────────────────────
# PHASE 1.2 — PROMPT BUILDER (No <> Templates, Only Few-Shot)
# ─────────────────────────────────────────

class PromptBuilder:

    # Worked examples — NO schema template shown, model infers format
    _FEW_SHOT = """
=== WORKED EXAMPLE A ===
Patient SOAP:
S: Chief complaint: fever 39.5°C, neck stiffness, severe headache, photophobia | Duration: acute (<24h) | Onset: SUDDEN
O: Age 28, Female. Labs: none provided.
C: PMH: none. Meds: none. Risk factors: none.

Dr. Gemma's clinical reasoning:
Step 1: Fever + neck stiffness + headache = classic meningeal irritation triad. Photophobia reinforces meningeal inflammation.
Step 2: Sudden onset <24h = bacterial time course (viral is typically slower). Young adult with no prior illness.
Step 3: Viral Meningitis remains a differential but bacterial probability is higher given the acuity.

{"doctor":"Dr. Gemma","specialty":"General Medicine","conditions":[{"condition":"Bacterial Meningitis","probability":65,"confidence":78,"evidence":["Meningeal triad: fever 39.5°C + neck stiffness + photophobia","Sudden onset <24h consistent with bacterial time course","Young female without prior immunocompromise"],"reasoning":"Classic bacterial meningitis triad with acute onset. LP + IV antibiotics within 1 hour."},{"condition":"Viral Meningitis","probability":25,"confidence":55,"evidence":["Fever + headache + photophobia also seen in viral","Absence of petechial rash (slightly against bacterial)"],"reasoning":"Cannot exclude viral without CSF analysis. Typically less acute onset."},{"condition":"Subarachnoid Hemorrhage","probability":10,"confidence":40,"evidence":["Sudden severe headache warrants CT before LP","Photophobia can occur in SAH"],"reasoning":"Must rule out with CT before LP given presentation severity."}],"missing_data":["Lumbar puncture (CSF analysis)","CT head (before LP)","Blood cultures","Kernig/Brudzinski sign exam"],"urgent_flags":["EMERGENCY: LP + IV broad-spectrum antibiotics within 1 hour"],"reasoning_summary":"Acute meningeal triad in young adult. Bacterial meningitis is primary until LP excludes it. Treat immediately."}

=== WORKED EXAMPLE B ===
Patient SOAP:
S: Chief complaint: chest pain radiating to left arm, sweating, nausea | Duration: acute (1-3 days) | Onset: Acute
O: Age 55, Male. Labs: none provided.
C: PMH: hypertension. Meds: amlodipine. Risk factors: hypertension, male.

Dr. Mistral's clinical reasoning:
Step 1: Chest pain + left arm radiation + diaphoresis = ACS triad. Duration 30 min exceeds typical angina (<10 min).
Step 2: Male 55yo hypertensive = high Framingham cardiac risk. Amlodipine use confirms pre-existing cardiac workup.
Step 3: Must distinguish STEMI from NSTEMI — ECG critical. Aortic dissection must be excluded.

{"doctor":"Dr. Mistral","specialty":"Differential Diagnosis","conditions":[{"condition":"Acute Myocardial Infarction","probability":72,"confidence":82,"evidence":["Left arm radiation — classic ACS referred pain pattern","Diaphoresis (sympathetic activation) — ACS marker","Duration >30 min beyond typical angina threshold","Male 55yo hypertensive — high Framingham cardiac risk"],"reasoning":"Classic STEMI/NSTEMI presentation. Immediate 12-lead ECG + cath lab activation."},{"condition":"Unstable Angina","probability":20,"confidence":60,"evidence":["Chest pain pattern consistent","No ST elevation data available to confirm MI"],"reasoning":"Cannot distinguish from NSTEMI without troponin. Treat as ACS protocol."},{"condition":"Aortic Dissection","probability":8,"confidence":40,"evidence":["Acute severe chest pain","Hypertension — dissection risk factor"],"reasoning":"Must exclude with bilateral BP measurement and CT-angiogram if dissection suspected."}],"missing_data":["12-lead ECG urgent","Troponin I/T serials","Bilateral BP measurement","CXR"],"urgent_flags":["EMERGENCY: Activate cath lab — PCI within 90 minutes"],"reasoning_summary":"High-probability ACS in hypertensive male. Immediate ECG, cath lab activation, aspirin 300mg."}
"""

    def diagnosis_prompt(self, soap: dict, doctor: dict) -> str:
        """
        Phase 1.2: Prompt with few-shot examples only — NO <> schema template.
        Phase 2.1: Uses SOAP-structured patient data instead of raw symptom blob.
        Phase 2 (RAG): Injects clinically grounded candidate conditions.
        """
        rag_block   = format_rag_block(soap["symptoms"])
        red_flags   = get_red_flags(soap["symptoms"])
        rf_str      = ", ".join(red_flags) if red_flags else "none identified"
        soap_string = soap["soap_string"]

        return f"""You are {doctor['name']}, {doctor['specialty']}. Your role: {doctor['role']}.

CRITICAL RULES — Follow these exactly:
1. Write your reasoning as Step 1, Step 2, Step 3 BEFORE the JSON.
2. Then output JSON formatted EXACTLY like the examples below.
3. Condition names must be REAL medical diagnoses (e.g., "Influenza A", "Bacterial Meningitis", "Acute Appendicitis").
4. Probability values must be different from each other and sum to approximately 100.
5. Evidence items must cite SPECIFIC findings from this patient's data (numbers, timing, location).
6. Do NOT copy placeholders or generic terms — write real clinical language.

{self._FEW_SHOT}

=== YOUR PATIENT ===
{soap_string}
Red Flags to Consider: {rf_str}

{rag_block}

Now write your Step 1 / Step 2 / Step 3 reasoning, then your JSON (doctor name: "{doctor['name']}", specialty: "{doctor['specialty']}"):"""

    def debate_prompt(self, soap: dict, doctor: dict, all_outputs: list) -> str:
        """Phase 2 adversarial debate — uses SOAP note for context."""
        council_summary = ""
        my_top, majority_condition = "Unknown", "Unknown"
        top_conditions = []

        for o in all_outputs:
            if o.get("conditions"):
                top = o["conditions"][0].get("condition","Unknown")
                top_conditions.append(top)
                council_summary += f"\n{o['doctor']}: {top} — {o.get('reasoning_summary','')[:120]}"
                if o.get("doctor") == doctor["name"]:
                    my_top = top

        if top_conditions:
            majority_condition = Counter(top_conditions).most_common(1)[0][0]

        return f"""You are {doctor['name']}, {doctor['specialty']}, in a medical council debate.

Patient: {soap['soap_string'][:400]}

Council diagnoses so far:{council_summary}

Your diagnosis: {my_top} | Council majority: {majority_condition}

Answer all three:
1. CHALLENGE: One specific clinical reason {majority_condition} might be WRONG for this patient.
2. SUPPORT: One piece of patient evidence that DOES support {majority_condition}.
3. FINAL: Your updated diagnosis and confidence (50–95%).

JSON only:
{{"doctor":"{doctor['name']}","agrees_with_majority":true,"challenge_reason":"<specific_reason>","support_reason":"<specific_evidence>","updated_top_condition":"{my_top}","confidence_after_debate":75,"updated_conditions":[],"additional_insights":""}}"""

    def moderator_prompt(self, debate_outputs: list, patient_symptoms: str) -> str:
        summary = ""
        for d in debate_outputs:
            summary += f"\n{d.get('doctor')}: {d.get('updated_top_condition','?')} ({d.get('confidence_after_debate','?')}%)"
            summary += f" | Challenge: {d.get('challenge_reason','N/A')[:80]}"
        return f"""You are the Chief Medical Officer. Synthesize the council debate.

Patient symptoms: {patient_symptoms}
Debate results:{summary}

Write a 2-sentence clinical synthesis. JSON only:
{{"consensus_narrative":"<2_sentence_synthesis>","final_agreed_condition":"<most_supported_condition>","consensus_confidence_adjustment":<integer_-15_to_15>}}"""

    def evidence_refinement_prompt(self, condition: str, soap: dict) -> str:
        return build_evidence_prompt(condition, soap["soap_string"])


# ─────────────────────────────────────────
# PHASE 2.5 — SPECIFICITY SCORER
# ─────────────────────────────────────────

def compute_specificity_score(condition_name: str, patient_symptoms: List[str]) -> float:
    """
    Phase 2.5: Compute confidence from how many defining symptoms of the
    diagnosed condition are present in the patient data.
    Returns a calibration multiplier (0.7–1.3).
    """
    from knowledge.symptom_map import SYMPTOM_DIFFERENTIAL_MAP
    condition_lower = condition_name.lower()

    for entry in SYMPTOM_DIFFERENTIAL_MAP:
        for cond_name, _, _ in entry.get("conditions", []):
            if cond_name.lower() in condition_lower or condition_lower in cond_name.lower():
                cluster = {s.lower() for s in entry["symptoms"]}
                patient = {s.lower() for s in patient_symptoms}
                overlap = len(cluster & patient)
                score   = overlap / max(len(cluster), 1)
                if score >= 0.7:   return 1.3
                elif score >= 0.5: return 1.1
                elif score >= 0.3: return 1.0
                else:              return 0.8

    return 1.0  # Unknown condition — neutral multiplier


# ─────────────────────────────────────────
# HALLUCINATION DETECTOR
# ─────────────────────────────────────────

class HallucinationDetector:
    def detect(self, council_outputs: List[dict]) -> Dict:
        valid = [o for o in council_outputs if o.get("conditions")]
        if len(valid) < 2:
            return {"outliers": [], "agreement_score": 0.5, "majority_condition": "unknown"}
        tops   = [normalize_condition_name(o["conditions"][0].get("condition","")).lower() for o in valid]
        counts = Counter(tops)
        majority, majority_count = counts.most_common(1)[0]
        outliers = []
        for o in valid:
            top = normalize_condition_name(o["conditions"][0].get("condition","")).lower()
            if top != majority and majority_count >= 2:
                outliers.append({"doctor": o.get("doctor"), "diagnosis": o["conditions"][0].get("condition")})
                print(f"[Hallucination] ⚠️  {o.get('doctor')} outlier: {o['conditions'][0].get('condition')}")
        return {"outliers": outliers, "majority_condition": majority, "agreement_score": round(majority_count/len(tops), 2)}


# ─────────────────────────────────────────
# WEIGHTED CONSENSUS ENGINE (Phase 2.5 Calibrated)
# ─────────────────────────────────────────

class WeightedConsensusEngine:

    def _best_conditions(self, doctor_name: str, council_out: list, debate_out: list) -> list:
        for o in debate_out:
            if o.get("doctor") == doctor_name:
                updated = [c for c in _safe_list(o.get("updated_conditions",[])) if isinstance(c,dict) and c.get("condition")]
                if updated: return updated
        for o in council_out:
            if o.get("doctor") == doctor_name:
                return [c for c in _safe_list(o.get("conditions",[])) if isinstance(c,dict) and c.get("condition")]
        return []

    def build(self, council_outputs, debate_outputs, h_report, patient_id,
              execution_time, patient_symptoms=None, moderator_output=None,
              forced_conditions=None, forced_flags=None) -> FinalClinicalOutput:
        try:
            validator        = OutputValidator()
            outlier_doctors  = {o["doctor"] for o in h_report.get("outliers",[])}
            agreement_score  = h_report.get("agreement_score", 0.5)
            forced_conditions = forced_conditions or []
            forced_flags      = forced_flags or []
            scores: Dict[str, dict] = {}

            for doctor in COUNCIL:
                conditions = self._best_conditions(doctor["name"], council_outputs, debate_outputs)
                # ICD-10 normalize
                conditions = normalize_conditions_list(conditions)
                if not conditions: continue

                valid, reason = validator.validate(conditions)
                if not valid:
                    print(f"[Consensus] ⚠️  {doctor['name']} rejected: {reason}")
                    conditions = conditions[:1]
                    if not conditions: continue

                weight = doctor["weight"]
                if doctor["name"] in outlier_doctors:      weight *= 0.55
                for d in debate_outputs:
                    if d.get("doctor") == doctor["name"] and d.get("agrees_with_majority"):
                        weight *= 1.1; break

                for i, cond in enumerate(conditions[:3]):
                    name  = normalize_condition_name(_to_str(cond.get("condition",""))).strip()
                    if not name or len(name) < 3: continue
                    prob  = max(5, min(95, _safe_float(cond.get("probability",50), 50)))
                    conf  = max(5, min(95, _safe_float(cond.get("confidence",50), 50)))
                    pos   = [1.0, 0.55, 0.25][i]

                    # Phase 2.5: Specificity score multiplier
                    spec_mult = compute_specificity_score(name, patient_symptoms or [])
                    score     = prob * conf * weight * pos * spec_mult

                    if name not in scores:
                        scores[name] = {"total_score":0,"evidence":[],"reasoning":[],"probs":[],"confs":[]}
                    scores[name]["total_score"] += score
                    scores[name]["probs"].append(prob)
                    scores[name]["confs"].append(conf)
                    for e in _safe_list(cond.get("evidence",[])):
                        ev = _to_str(e).strip()
                        if ev and len(ev) > 5 and not validator.has_placeholder(ev) and ev not in scores[name]["evidence"]:
                            scores[name]["evidence"].append(ev)
                    r = _to_str(cond.get("reasoning","")).strip()
                    if r and len(r) > 10 and not validator.has_placeholder(r):
                        scores[name]["reasoning"].append(f"{doctor['name']}: {r}")

            sorted_conds = sorted(scores.items(), key=lambda x: x[1]["total_score"], reverse=True)
            final: List[ClinicalCondition] = []

            # Prepend forced conditions from clinical rules (guaranteed slots)
            forced_names = set()
            for fc in forced_conditions[:2]:  # max 2 forced slots
                name = normalize_condition_name(fc.get("condition",""))
                if not name: continue
                forced_names.add(name.lower())
                final.append(ClinicalCondition(
                    condition   = name,
                    probability = float(fc.get("probability", 60)),
                    confidence  = float(fc.get("confidence", 75)),
                    evidence    = [_to_str(e) for e in _safe_list(fc.get("evidence",[]))[:4]],
                    reasoning   = _to_str(fc.get("reasoning","Clinical rule-based diagnosis"))
                ))

            # Fill remaining slots from consensus scoring
            for name, data in sorted_conds:
                if len(final) >= 3: break
                if name.lower() in forced_names: continue
                probs = data["probs"]; confs = data["confs"]
                final.append(ClinicalCondition(
                    condition   = name,
                    probability = round(sum(probs)/len(probs),1) if probs else 50.0,
                    confidence  = round(sum(confs)/len(confs),1) if confs else 50.0,
                    evidence    = data["evidence"][:5],
                    reasoning   = " | ".join(data["reasoning"][:2]) or "Council consensus"
                ))

            # Fallback
            if not final:
                best = max([o for o in council_outputs if o.get("conditions")],
                           key=lambda o: next((d["weight"] for d in COUNCIL if d["name"]==o.get("doctor")),0),
                           default=None)
                if best:
                    for c in best["conditions"][:3]:
                        nm = normalize_condition_name(_to_str(c.get("condition","Unknown")))
                        final.append(ClinicalCondition(
                            condition=nm, probability=_safe_float(c.get("probability",50),50),
                            confidence=_safe_float(c.get("confidence",45),45),
                            evidence=[_to_str(e) for e in _safe_list(c.get("evidence",[]))],
                            reasoning=_to_str(c.get("reasoning","Fallback output"))
                        ))

            # Phase 2.5: Calibrated confidence
            raw_conf = sum(c.confidence for c in final)/len(final) if final else 0.0
            if agreement_score >= 0.9:     calib = 1.25
            elif agreement_score >= 0.66:  calib = 1.0
            else:                          calib = 0.7; raw_conf = min(raw_conf, 50.0)

            mod_adj = _safe_float(moderator_output.get("consensus_confidence_adjustment",0)) if moderator_output else 0
            avg_conf = min(92.0, max(15.0, raw_conf * calib + mod_adj))

            missing = list({_to_str(x).strip() for o in council_outputs for x in _safe_list(o.get("missing_data",[])) if _to_str(x).strip()})
            flags: List[str] = list(forced_flags)
            for o in council_outputs:
                for f in _safe_list(o.get("urgent_flags",[])):
                    s = _to_str(f).strip()
                    if s and s not in flags: flags.append(s)
            if avg_conf < 50: flags.append("LOW CONFIDENCE — Doctor review strongly recommended")
            if outlier_doctors: flags.append(f"COUNCIL DISAGREEMENT — {len(outlier_doctors)} outlier(s)")

            council_votes = {o.get("doctor"): (o["conditions"][0].get("condition","Unknown") if o.get("conditions") else "No output") for o in council_outputs}

            if moderator_output and moderator_output.get("consensus_narrative"):
                summary = moderator_output["consensus_narrative"]
            else:
                best_out = max([o for o in council_outputs if o.get("conditions")],
                               key=lambda o: next((d["weight"] for d in COUNCIL if d["name"]==o.get("doctor")),0), default={})
                summary = _to_str(best_out.get("reasoning_summary","")) or f"Council of {len(COUNCIL)} AI specialists. Agreement: {agreement_score*100:.0f}%."

            return FinalClinicalOutput(
                patient_id=patient_id, top_3_conditions=final, consensus_confidence=round(avg_conf,1),
                agents_agreed=len(outlier_doctors)==0, council_votes=council_votes,
                disagreement_details=f"Outliers: {', '.join(outlier_doctors)}" if outlier_doctors else None,
                missing_data_suggestions=missing, safety_flags=flags,
                doctor_review_required=(avg_conf<60 or bool(outlier_doctors) or bool(flags)),
                reasoning_summary=summary, execution_time_seconds=round(execution_time,1)
            )

        except Exception as e:
            print(f"[Consensus] ❌ CRASH: {e}"); traceback.print_exc()
            return FinalClinicalOutput(
                patient_id=patient_id, top_3_conditions=[], consensus_confidence=30.0,
                agents_agreed=False, council_votes={},
                disagreement_details=f"Consensus error: {str(e)}",
                missing_data_suggestions=["Full assessment recommended"],
                safety_flags=["PARTIAL OUTPUT — Doctor review required"],
                doctor_review_required=True,
                reasoning_summary=f"Consensus engine error: {str(e)}",
                execution_time_seconds=round(execution_time,1)
            )


# ─────────────────────────────────────────
# CLINICAL REASONER — MAIN CLASS
# ─────────────────────────────────────────

class ClinicalReasoner:

    def __init__(self):
        self.llm       = CouncilLLMClient()
        self.prompts   = PromptBuilder()
        self.detector  = HallucinationDetector()
        self.consensus = WeightedConsensusEngine()
        self.validator = OutputValidator()
        print(f"[Council] Initialized ({len(COUNCIL)} members):")
        for d in COUNCIL: print(f"  {d['name']} — {d['model']}")

    async def _run_doctor_async(self, doctor: dict, soap: dict, patient_state: dict) -> dict:
        """
        Phase 1.1+1.2+Phase 3 Self-Consistency:
        Run 3 parallel inferences, majority-vote on ICD-10 normalized top condition.
        """
        print(f"[Council] {doctor['name']} analyzing...")
        t0 = time.time()
        prompt = self.prompts.diagnosis_prompt(soap, doctor)
        temperatures = [0.05, 0.2, 0.4]

        for attempt in range(3):
            try:
                # Try grammar-constrained JSON schema first
                tasks_schema = [
                    self.llm.query_async(prompt, doctor["model"], doctor["tokens"],
                                         use_json_schema=True, temperature=t)
                    for t in temperatures
                ]
                raws = await asyncio.gather(*tasks_schema, return_exceptions=True)

                parsed_outputs = []
                for raw in raws:
                    if isinstance(raw, Exception): continue
                    parsed = self.llm.parse_json(str(raw))
                    conditions = normalize_conditions_list(
                        [c for c in _safe_list(parsed.get("conditions",[])) if isinstance(c,dict) and c.get("condition")]
                    )
                    if conditions:
                        valid, reason = self.validator.validate(conditions)
                        if valid:
                            parsed["conditions"] = conditions
                            parsed_outputs.append(parsed)
                        else:
                            print(f"[Council] {doctor['name']} rejected (attempt {attempt+1}): {reason}")

                if not parsed_outputs:
                    # Fallback: plain text CoT prompt (no schema)
                    tasks_plain = [
                        self.llm.query_async(prompt, doctor["model"], doctor["tokens"],
                                              use_json_schema=False, temperature=t)
                        for t in temperatures
                    ]
                    raws2 = await asyncio.gather(*tasks_plain, return_exceptions=True)
                    for raw in raws2:
                        if isinstance(raw, Exception): continue
                        parsed = self.llm.parse_json(str(raw))
                        conditions = normalize_conditions_list(
                            [c for c in _safe_list(parsed.get("conditions",[])) if isinstance(c,dict) and c.get("condition")]
                        )
                        if conditions:
                            valid, reason = self.validator.validate(conditions)
                            if valid:
                                parsed["conditions"] = conditions
                                parsed_outputs.append(parsed)

                if not parsed_outputs:
                    await asyncio.sleep(1); continue

                tops   = [normalize_condition_name(p["conditions"][0].get("condition","")).lower() for p in parsed_outputs]
                counts = Counter(tops)
                majority, majority_count = counts.most_common(1)[0]
                best   = next((p for p in parsed_outputs if normalize_condition_name(p["conditions"][0].get("condition","")).lower() == majority), parsed_outputs[0])
                best["doctor"]    = doctor["name"]
                best["specialty"] = doctor["specialty"]
                best["_consistency"] = round(majority_count/len(tops), 2)

                elapsed = round(time.time()-t0, 1)
                print(f"[Council] ✅ {doctor['name']} {elapsed}s — {best['conditions'][0].get('condition','?')} (consistency {majority_count}/{len(tops)})")
                return best

            except Exception as e:
                print(f"[Council] ⚠️ {doctor['name']} attempt {attempt+1}: {e}")
                await asyncio.sleep(1)

        elapsed = round(time.time()-t0, 1)
        print(f"[Council] ❌ {doctor['name']} exhausted retries ({elapsed}s)")
        return {"doctor":doctor["name"],"specialty":doctor["specialty"],"conditions":[],"missing_data":[],"urgent_flags":[],"reasoning_summary":"All attempts failed"}

    async def _refine_evidence_async(self, top_condition: str, soap: dict, doctor_model: str) -> List[str]:
        """Phase 2.4: Secondary LLM call to generate specific clinical evidence."""
        try:
            prompt = self.prompts.evidence_refinement_prompt(top_condition, soap)
            raw    = await self.llm.query_async(prompt, doctor_model, 512, use_json_schema=False, temperature=0.1)
            return extract_evidence_from_raw(raw, soap.get("symptoms",[]))
        except Exception as e:
            print(f"[Evidence] Extractor failed: {e}")
            return [f"Patient reported: {s}" for s in soap.get("symptoms",[])[:4]]

    async def _run_debate_async(self, doctor: dict, soap: dict, all_outputs: list) -> dict:
        for attempt in range(3):
            try:
                prompt = self.prompts.debate_prompt(soap, doctor, all_outputs)
                raw    = await self.llm.query_async(prompt, doctor["model"], 768, use_json_schema=False, temperature=0.2)
                output = self.llm.parse_json(raw)
                if output and output.get("updated_top_condition"):
                    return {
                        "doctor":                 doctor["name"],
                        "agrees_with_majority":   bool(output.get("agrees_with_majority",True)),
                        "disagreement_reason":    str(output.get("challenge_reason","")),
                        "support_reason":         str(output.get("support_reason","")),
                        "updated_top_condition":  normalize_condition_name(str(output.get("updated_top_condition",""))),
                        "updated_conditions":     normalize_conditions_list(_safe_list(output.get("updated_conditions",[]))),
                        "confidence_after_debate": _safe_float(output.get("confidence_after_debate",65),65),
                        "additional_insights":    str(output.get("additional_insights",""))
                    }
            except Exception as e:
                print(f"[Council] ⚠️ {doctor['name']} debate attempt {attempt+1}: {e}")
            await asyncio.sleep(1)
        return {"doctor":doctor["name"],"agrees_with_majority":True,"updated_conditions":[],"confidence_after_debate":60.0,"updated_top_condition":"","disagreement_reason":"","support_reason":"","additional_insights":""}

    async def _run_moderator_async(self, debate_outputs: list, patient_symptoms: str) -> dict:
        try:
            prompt = self.prompts.moderator_prompt(debate_outputs, patient_symptoms)
            raw    = await self.llm.query_async(prompt, COUNCIL[0]["model"], 512, use_json_schema=False, temperature=0.1)
            output = self.llm.parse_json(raw)
            if output and output.get("consensus_narrative"):
                return output
        except Exception as e:
            print(f"[Council] ⚠️ Moderator failed: {e}")
        return {}

    def _run_doctor(self, doctor, soap, patient_state): return asyncio.run(self._run_doctor_async(doctor, soap, patient_state))
    def _run_debate(self, doctor, soap, all_outputs):   return asyncio.run(self._run_debate_async(doctor, soap, all_outputs))

    MODEL_KEY_MAP = {"medgemma":"Dr. Gemma", "openbiollm":"Dr. OpenBio", "mistral":"Dr. Mistral"}

    def analyze_single(self, patient_state: dict, model_key: str) -> FinalClinicalOutput:
        pid   = patient_state.get("patient_id","unknown")
        start = time.time()
        soap  = convert_to_soap(patient_state)  # Phase 2.1

        doctor_name = self.MODEL_KEY_MAP.get(model_key)
        doctor      = next((d for d in COUNCIL if d["name"] == doctor_name), None)
        if not doctor:
            return FinalClinicalOutput(patient_id=pid,top_3_conditions=[],consensus_confidence=0,
                agents_agreed=False,council_votes={},disagreement_details=f"Unknown: {model_key}",
                missing_data_suggestions=[],safety_flags=["INVALID MODEL"],doctor_review_required=True,
                reasoning_summary=f"Model '{model_key}' not found.",execution_time_seconds=0)

        output     = self._run_doctor(doctor, soap, patient_state)
        conditions = normalize_conditions_list(output.get("conditions",[]))[:3]
        final      = [ClinicalCondition(
            condition=normalize_condition_name(_to_str(c.get("condition","Unknown"))),
            probability=_safe_float(c.get("probability",50),50),
            confidence=_safe_float(c.get("confidence",50),50),
            evidence=[_to_str(e) for e in _safe_list(c.get("evidence",[]))],
            reasoning=_to_str(c.get("reasoning",""))
        ) for c in conditions if isinstance(c,dict) and c.get("condition")]

        avg_conf = sum(c.confidence for c in final)/len(final) if final else 0.0
        return FinalClinicalOutput(patient_id=pid,top_3_conditions=final,consensus_confidence=round(avg_conf,1),
            agents_agreed=True,council_votes={doctor["name"]:final[0].condition if final else "No output"},
            disagreement_details=None,missing_data_suggestions=[_to_str(x) for x in _safe_list(output.get("missing_data",[]))],
            safety_flags=[_to_str(x) for x in _safe_list(output.get("urgent_flags",[]))],
            doctor_review_required=avg_conf<60,
            reasoning_summary=_to_str(output.get("reasoning_summary",f"Analysis by {doctor['name']}")),
            execution_time_seconds=round(time.time()-start,1))

    # ── Persistence helper ────────────────────────────────────────────────────
    def _persist_outcome(self, result: "FinalClinicalOutput", q_breakdown: dict,
                          forced_conditions: list, extra: dict):
        """Asynchronously persist analysis result to Supabase council_outcomes table."""
        try:
            supabase_url = os.getenv("SUPABASE_URL")
            supabase_key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_ANON_KEY")
            if not (supabase_url and supabase_key):
                return
            from supabase import create_client
            client = create_client(supabase_url, supabase_key)
            row = {
                "patient_id":           result.patient_id,
                "top_diagnosis":        result.top_3_conditions[0].condition if result.top_3_conditions else None,
                "top_diagnosis_prob":   result.top_3_conditions[0].probability if result.top_3_conditions else None,
                "all_conditions":       [c.dict() for c in result.top_3_conditions],
                "council_votes":        result.council_votes or {},
                "consensus_confidence": result.consensus_confidence,
                "agreement_score":      1.0 if result.agents_agreed else 0.5,
                "agents_agreed":        result.agents_agreed,
                "execution_time_s":     result.execution_time_seconds,
                "safety_flags":         result.safety_flags,
                "doctor_review_req":    result.doctor_review_required,
                "reasoning_summary":    result.reasoning_summary,
                "missing_data":         result.missing_data_suggestions,
                "q_score":              q_breakdown.get("q_score"),
                "q_agreement":          q_breakdown.get("agreement_score"),
                "q_confidence":         q_breakdown.get("confidence_score"),
                "q_evidence":           q_breakdown.get("evidence_score"),
                "q_probability":        q_breakdown.get("probability_score"),
                "q_rule_alignment":     q_breakdown.get("rule_alignment"),
                "q_grade":              q_breakdown.get("grade"),
                "prompt_version":       os.getenv("PROMPT_VERSION", "v1.0"),
                "llm_models_used":      [d["model"] for d in COUNCIL],
            }
            client.table("council_outcomes").insert(row).execute()
            print(f"[Council] 💾 Outcome persisted (Q={q_breakdown.get('q_score','?')} grade={q_breakdown.get('grade','?')})")
        except Exception as e:
            print(f"[Council] ⚠️ Persistence skipped: {e}")

    # ── Phase 1.1: Think-Revise async pass ───────────────────────────────────
    async def _run_critic_revision_async(self, council_outputs: list, soap: dict) -> list:
        """Run critic review + targeted revision for any doctor with low scores."""
        revised = list(council_outputs)
        for i, output in enumerate(council_outputs):
            if not output.get("conditions"):
                continue
            doctor = COUNCIL[i]
            try:
                critic_prompt = build_critic_prompt(soap["soap_string"], doctor["name"], output)
                raw           = await self.llm.query_async(critic_prompt, doctor["model"], 512,
                                                            use_json_schema=False, temperature=0.1)
                critique      = self.llm.parse_json(raw)
                if not critique:
                    continue
                needs_revision, instruction = parse_critique(critique)
                if needs_revision:
                    print(f"[Thinker] 🔄 {doctor['name']} needs revision: {instruction[:80]}")
                    rev_prompt  = build_revision_prompt(soap["soap_string"], doctor, output, critique)
                    rev_raw     = await self.llm.query_async(rev_prompt, doctor["model"], 1024,
                                                              use_json_schema=True, temperature=0.1)
                    rev_parsed  = self.llm.parse_json(rev_raw)
                    new_conds   = normalize_conditions_list(
                        [c for c in _safe_list(rev_parsed.get("conditions",[])) if isinstance(c, dict) and c.get("condition")]
                    )
                    if new_conds:
                        valid, reason = self.validator.validate(new_conds)
                        if valid:
                            revised[i] = {**output, "conditions": new_conds,
                                          "reasoning_summary": rev_parsed.get("reasoning_summary", output.get("reasoning_summary",""))}
                            print(f"[Thinker] ✅ {doctor['name']} revised: {new_conds[0].get('condition','?')}")
                        else:
                            print(f"[Thinker] ⚠️  Revision rejected ({reason}) — keeping original")
                else:
                    print(f"[Thinker] ✓ {doctor['name']} passes critic review")
            except Exception as e:
                print(f"[Thinker] ⚠️ {doctor['name']} critic failed: {e}")
        return revised

    # ── Phase 4.2: Diagnostic Planner ────────────────────────────────────────
    async def _run_diagnostic_plan_async(self, top_condition: str, probability: float, soap: dict) -> tuple:
        try:
            prompt  = build_planner_prompt(top_condition, probability, soap["soap_string"])
            raw     = await self.llm.query_async(prompt, COUNCIL[0]["model"], 768,
                                                  use_json_schema=False, temperature=0.1)
            parsed  = self.llm.parse_json(raw)
            return parse_plan_output(parsed)
        except Exception as e:
            print(f"[Planner] ⚠️ Failed: {e}")
            return [], ""

    # ── Phase 4.1: Counterfactual Reasoner ───────────────────────────────────
    async def _run_counterfactual_async(self, top_condition: str, probability: float, soap: dict) -> list:
        try:
            prompt   = build_counterfactual_prompt(top_condition, probability, soap)
            raw      = await self.llm.query_async(prompt, COUNCIL[2]["model"], 512,
                                                   use_json_schema=False, temperature=0.3)
            parsed   = self.llm.parse_json(raw)
            insights = parse_counterfactual_output(parsed)
            if insights:
                print(f"[Counterfactual] {len(insights)} insights generated")
            return insights
        except Exception as e:
            print(f"[Counterfactual] ⚠️ Failed: {e}")
            return []

    # ── Phase 1.4: Confidence Audit ──────────────────────────────────────────
    async def _run_confidence_audit_async(self, conditions: list, confidence: float, soap: dict) -> dict:
        try:
            prompt  = build_audit_prompt(soap["soap_string"], conditions, confidence)
            raw     = await self.llm.query_async(prompt, COUNCIL[0]["model"], 400,
                                                  use_json_schema=False, temperature=0.1)
            parsed  = self.llm.parse_json(raw)
            if parsed and parsed.get("audit_grade"):
                print(f"[Auditor] Grade: {parsed.get('audit_grade')} | Ind. conf: {parsed.get('independent_confidence','?')}%")
                return parsed
        except Exception as e:
            print(f"[Auditor] ⚠️ Failed: {e}")
        return {}

    def analyze(self, patient_state: dict) -> FinalClinicalOutput:
        pid   = patient_state.get("patient_id","unknown")
        start = time.time()

        # Phase 2.1: Convert to SOAP note
        soap  = convert_to_soap(patient_state)
        patient_symptoms = soap["symptoms"]

        # Phase 2.2: Run hard clinical rules BEFORE any LLM call
        forced_conditions, forced_flags = run_clinical_rules(patient_state)

        print(f"\n[Council] {'='*40}")
        print(f"[Council] Patient: {pid} | Symptoms: {soap['symptoms'][:5]}")
        print(f"[Council] {'='*40}")

        try:
            # ── ROUND 1: Self-Consistency Parallel Diagnosis ──────────────────
            print(f"\n[Council] ROUND 1 — {len(COUNCIL)} models (self-consistency + grammar constraints)")

            async def run_round_1():
                tasks   = [self._run_doctor_async(d, soap, patient_state) for d in COUNCIL]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                outputs = []
                for idx, r in enumerate(results):
                    doc = COUNCIL[idx]
                    if isinstance(r, Exception):
                        print(f"[Council] ❌ {doc['name']} failed: {r}")
                        outputs.append({"doctor":doc["name"],"specialty":doc["specialty"],"conditions":[],"missing_data":[],"urgent_flags":[],"reasoning_summary":str(r)})
                    else:
                        outputs.append(r)
                return outputs

            council_outputs = asyncio.run(run_round_1())
            valid_count = len([o for o in council_outputs if o.get("conditions")])
            print(f"[Council] Round 1: {valid_count}/{len(COUNCIL)} valid | {round(time.time()-start,1)}s")

            # ── Phase 2.4: Refine evidence for top conditions ─────────────────
            print(f"\n[Council] ROUND 1b — Evidence refinement")
            async def run_evidence_refinement():
                tasks = []
                for i, o in enumerate(council_outputs):
                    if o.get("conditions"):
                        top_cond = o["conditions"][0].get("condition","Unknown")
                        tasks.append((i, self._refine_evidence_async(top_cond, soap, COUNCIL[i]["model"])))
                refined = await asyncio.gather(*[t[1] for t in tasks], return_exceptions=True)
                for j, (i, _) in enumerate(tasks):
                    if not isinstance(refined[j], Exception) and refined[j]:
                        council_outputs[i]["conditions"][0]["evidence"] = refined[j]
                return council_outputs

            council_outputs = asyncio.run(run_evidence_refinement())

            if valid_count == 0:
                # If all failed but we have forced conditions from rules, return those
                if forced_conditions:
                    final = [ClinicalCondition(**{k:v for k,v in fc.items() if k in ClinicalCondition.__fields__}) for fc in forced_conditions[:3]]
                    return FinalClinicalOutput(patient_id=pid,top_3_conditions=final,consensus_confidence=70.0,
                        agents_agreed=True,council_votes={},disagreement_details="LLM models failed — clinical rules applied",
                        missing_data_suggestions=["Full clinical assessment required"],safety_flags=forced_flags,
                        doctor_review_required=True,reasoning_summary="Clinical decision rules applied. LLM council unavailable.",
                        execution_time_seconds=round(time.time()-start,1))
                return FinalClinicalOutput(patient_id=pid,top_3_conditions=[],consensus_confidence=0,
                    agents_agreed=False,council_votes={},disagreement_details="All models failed",
                    missing_data_suggestions=["Full assessment required"],
                    safety_flags=["SYSTEM ERROR — Consult a doctor"],doctor_review_required=True,
                    reasoning_summary="All council members failed.",execution_time_seconds=round(time.time()-start,1))

            # ── ROUND 1.5 (NEW): Think-Revise Metacognitive Critic (Phase 1.1) ─
            print(f"\n[Council] ROUND 1.5 — Think-Revise metacognitive critic")
            async def run_critic_revision(): return await self._run_critic_revision_async(council_outputs, soap)
            council_outputs = asyncio.run(run_critic_revision())

            # ── ROUND 2: Hallucination Detection (ICD-10 normalized) ─────────
            print(f"\n[Council] ROUND 2 — Hallucination detection + ICD-10 normalization")
            h_report = self.detector.detect(council_outputs)
            print(f"[Council] Agreement: {h_report['agreement_score']*100:.0f}% | Majority: {h_report.get('majority_condition','?')}")

            # ── ROUND 2.5 (NEW): Differential Pruning (Phase 1.3) ────────────
            print(f"\n[Council] ROUND 2.5 — Differential pruning (negative symptom elimination)")
            for i, output in enumerate(council_outputs):
                if output.get("conditions"):
                    original_conds = list(output["conditions"])
                    pruned_conds   = prune_conditions(original_conds, patient_symptoms)
                    summary        = get_pruning_summary(original_conds, pruned_conds)
                    if summary != "No pruning applied":
                        print(f"[Pruner] {COUNCIL[i]['name']}: {summary}")
                    council_outputs[i]["conditions"] = pruned_conds

            # ── ROUND 3: Adversarial Debate ───────────────────────────────────
            print(f"\n[Council] ROUND 3 — Adversarial debate")
            async def run_round_3():
                tasks   = [self._run_debate_async(d, soap, council_outputs) for d in COUNCIL]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                return [r if not isinstance(r,Exception) else {"doctor":COUNCIL[i]["name"],"agrees_with_majority":True,"updated_conditions":[],"confidence_after_debate":60} for i,r in enumerate(results)]
            debate_outputs = asyncio.run(run_round_3())

            # ── ROUND 3b: Moderator ───────────────────────────────────────────
            print(f"\n[Council] ROUND 3b — Moderator synthesis")
            symptom_str = ", ".join(patient_symptoms) or "unspecified"
            async def run_moderator(): return await self._run_moderator_async(debate_outputs, symptom_str)
            moderator_output = asyncio.run(run_moderator())

            # ── ROUND 4: Calibrated Bayesian Consensus ────────────────────────
            print(f"\n[Council] ROUND 4 — Calibrated Bayesian consensus + clinical rules merge")
            total  = round(time.time()-start, 1)
            result = self.consensus.build(
                council_outputs, debate_outputs, h_report, pid, total,
                patient_symptoms=patient_symptoms, moderator_output=moderator_output,
                forced_conditions=forced_conditions, forced_flags=forced_flags
            )

            # ── ROUND 4.5 (NEW): Confidence Audit (Phase 1.4) ────────────────
            print(f"\n[Council] ROUND 4.5 — Confidence audit + sanity check")
            async def run_audit():
                return await self._run_confidence_audit_async(
                    [c.dict() for c in result.top_3_conditions],
                    result.consensus_confidence, soap
                )
            audit_result = asyncio.run(run_audit())
            if audit_result:
                audit_parsed    = parse_audit_result(audit_result, result.missing_data_suggestions)
                blended_conf    = confidence_adjustment(result.consensus_confidence, audit_parsed["independent_confidence"])
                result = FinalClinicalOutput(
                    patient_id=result.patient_id,
                    top_3_conditions=result.top_3_conditions,
                    consensus_confidence=blended_conf,
                    agents_agreed=result.agents_agreed,
                    council_votes=result.council_votes,
                    disagreement_details=result.disagreement_details,
                    missing_data_suggestions=audit_parsed["enriched_missing"],
                    safety_flags=result.safety_flags + audit_parsed["extra_flags"],
                    doctor_review_required=result.doctor_review_required or audit_parsed["audit_grade"] in ("C","D"),
                    reasoning_summary=result.reasoning_summary,
                    execution_time_seconds=result.execution_time_seconds,
                )

            # ── ROUND 5 (NEW): Diagnostic Plan + Counterfactuals (Phase 4) ───
            diagnostic_plan = []; immediate_action = ""; counterfactuals = []
            if result.top_3_conditions:
                top_cond = result.top_3_conditions[0].condition
                top_prob = result.top_3_conditions[0].probability
                print(f"\n[Council] ROUND 5 — Diagnostic plan + counterfactuals for: {top_cond}")
                async def run_plan_cf():
                    plan_task = self._run_diagnostic_plan_async(top_cond, top_prob, soap)
                    cf_task   = self._run_counterfactual_async(top_cond, top_prob, soap)
                    return await asyncio.gather(plan_task, cf_task, return_exceptions=True)
                plan_result, cf_result = asyncio.run(run_plan_cf())
                if not isinstance(plan_result, Exception): diagnostic_plan, immediate_action = plan_result
                if not isinstance(cf_result, Exception):   counterfactuals = cf_result

            # ── ROUND 6 (NEW): Q-Score + Supabase Persistence (Phase 2) ──────
            print(f"\n[Council] ROUND 6 — Q-score + outcome persistence")
            q_output    = {"top_3_conditions":[c.dict() for c in result.top_3_conditions],
                           "consensus_confidence":result.consensus_confidence,"agents_agreed":result.agents_agreed}
            q_breakdown = compute_q_score(q_output, forced_conditions)
            print(f"[Council] Q-Score: {q_breakdown['q_score']} (Grade {q_breakdown['grade']})")
            self._persist_outcome(result, q_breakdown, forced_conditions, {})

            # Attach extended fields for API consumers
            result.__dict__["diagnostic_plan"]  = diagnostic_plan
            result.__dict__["immediate_action"] = immediate_action
            result.__dict__["counterfactuals"]  = counterfactuals
            result.__dict__["q_score"]          = q_breakdown["q_score"]
            result.__dict__["q_grade"]          = q_breakdown["grade"]

            total_final = round(time.time()-start, 1)
            print(f"\n[Council] {'='*40}")
            print(f"[Council] ✅ Complete {total_final}s | Conf: {result.consensus_confidence}% | Q: {q_breakdown['q_score']} ({q_breakdown['grade']}) | Agreed: {result.agents_agreed}")
            if result.top_3_conditions: print(f"[Council] Top: {result.top_3_conditions[0].condition}")
            if diagnostic_plan: print(f"[Council] Plan: {len(diagnostic_plan)} steps | Action: {immediate_action[:60]}")
            if counterfactuals: print(f"[Council] Counterfactuals: {len(counterfactuals)}")
            print(f"[Council] {'='*40}\n")
            return result

        except Exception as e:
            print(f"[Council] ❌ FATAL: {e}"); traceback.print_exc()
            return FinalClinicalOutput(
                patient_id=pid,top_3_conditions=[],consensus_confidence=0,agents_agreed=False,
                council_votes={},disagreement_details=str(e),
                missing_data_suggestions=["Manual assessment required"],
                safety_flags=["SYSTEM ERROR — Consult a doctor directly"],
                doctor_review_required=True,
                reasoning_summary=f"System error: {str(e)}.",
                execution_time_seconds=round(time.time()-start,1)
            )