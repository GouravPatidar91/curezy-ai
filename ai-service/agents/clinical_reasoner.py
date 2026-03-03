import os
import json
import time
import traceback
import asyncio
from collections import Counter
from typing import List, Optional, Dict
from pydantic import BaseModel
import ollama
from dotenv import load_dotenv

load_dotenv()


# ─────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────

def _to_str(val) -> str:
    if isinstance(val, str):
        return val
    if isinstance(val, dict):
        return val.get("condition") or val.get("name") or val.get("message") or str(val)
    if isinstance(val, list):
        return ", ".join(_to_str(v) for v in val)
    return str(val)

def _safe_float(val, default: float = 0.0) -> float:
    try:
        return float(val)
    except Exception:
        return default

def _safe_list(val) -> list:
    if isinstance(val, list):
        return val
    return []


# ─────────────────────────────────────────
# OUTPUT MODELS
# ─────────────────────────────────────────

class ClinicalCondition(BaseModel):
    condition: str
    probability: float
    confidence: float
    evidence: List[str]
    reasoning: str

class FinalClinicalOutput(BaseModel):
    patient_id: str
    top_3_conditions: List[ClinicalCondition]
    consensus_confidence: float
    agents_agreed: bool
    council_votes: Optional[dict]
    disagreement_details: Optional[str]
    missing_data_suggestions: List[str]
    safety_flags: List[str]
    doctor_review_required: bool
    reasoning_summary: str
    execution_time_seconds: Optional[float]


# ─────────────────────────────────────────
# COUNCIL MEMBERS
# ─────────────────────────────────────────

COUNCIL = [
    {
        "name":      "Dr. Gemma",
        "model":     "alibayram/medgemma:4b",
        "specialty": "General Medicine",
        "role":      "Primary Diagnostician",
        "weight":    1.5,
        "tokens":    2048,
    },
    {
        "name":      "Dr. OpenBio",
        "model":     "koesn/llama3-openbiollm-8b:latest",
        "specialty": "Biomedical Research",
        "role":      "Evidence Validator",
        "weight":    1.4,
        "tokens":    2048,
    },
    {
        "name":      "Dr. Mistral",
        "model":     "mistral:7b",
        "specialty": "Differential Diagnosis",
        "role":      "Devil's Advocate",
        "weight":    1.2,
        "tokens":    1536,
    },
]


# ─────────────────────────────────────────
# PROMPT BUILDER
# ─────────────────────────────────────────

class PromptBuilder:

    def _extract(self, ps: dict) -> dict:
        symptoms = [_to_str(s) for s in ps.get("symptoms", [])]
        history  = [_to_str(h) for h in ps.get("medical_history", [])]
        risks    = [_to_str(r) for r in ps.get("risk_factors", [])]
        meds     = []
        for m in ps.get("medications", []):
            meds.append(m.get("name", _to_str(m)) if isinstance(m, dict) else _to_str(m))
        labs = ""
        for lab in ps.get("lab_reports", []):
            if isinstance(lab, dict):
                flag = "ABNORMAL" if lab.get("is_abnormal") else "normal"
                labs += f"\n  - {lab.get('test_name','Unknown')}: {lab.get('value','N/A')} ({flag})"
        return {
            "symptoms":  ", ".join(symptoms) or "not specified",
            "history":   ", ".join(history) or "none",
            "risks":     ", ".join(risks) or "none",
            "meds":      ", ".join(meds) or "none",
            "labs":      labs or "none provided",
            "age":       ps.get("age", "unknown"),
            "gender":    ps.get("gender", "unknown"),
            "duration":  ps.get("symptom_duration", "unknown"),
        }

    def diagnosis_prompt(self, ps: dict, doctor: dict) -> str:
        p = self._extract(ps)
        return f"""You are {doctor['name']}, {doctor['specialty']}. Role: {doctor['role']}.
RULES: Output JSON only. NO text before/after. Use real condition names.
Patient: Age {p['age']}, {p['gender']}, Symptoms: {p['symptoms']}, Duration: {p['duration']}, History: {p['history']}, Meds: {p['meds']}, Labs: {p['labs']}

JSON schema to fill:
{{
  "doctor": "{doctor['name']}",
  "specialty": "{doctor['specialty']}",
  "conditions": [
    {{"condition": "Condition1", "probability": 60, "confidence": 65, "evidence": ["ev1"], "reasoning": "r1"}},
    {{"condition": "Condition2", "probability": 25, "confidence": 50, "evidence": ["ev2"], "reasoning": "r2"}},
    {{"condition": "Condition3", "probability": 15, "confidence": 40, "evidence": ["ev3"], "reasoning": "r3"}}
  ],
  "missing_data": ["data"],
  "urgent_flags": [],
  "reasoning_summary": "summary"
}}"""

    def debate_prompt(self, ps: dict, doctor: dict, all_outputs: list) -> str:
        p = self._extract(ps)
        others = ""
        my_top = "Unknown"
        for o in all_outputs:
            if o.get("conditions"):
                top = o["conditions"][0].get("condition", "Unknown")
            if o.get("doctor") == doctor["name"]:
                my_top = top
            else:
                others += f" {o['doctor']} says: {top}."

        return f"""Medical debate. You: {doctor['name']}. Your diagnosis: {my_top}. Others:{others}. Symptoms: {p['symptoms']}
Respond JSON only:
{{"doctor":"{doctor['name']}","agrees_with_majority":true,"disagreement_reason":"","updated_top_condition":"{my_top}","confidence_after_debate":75,"additional_insights":""}}"""


# ─────────────────────────────────────────
# LLM CLIENT
# ─────────────────────────────────────────

class CouncilLLMClient:

    async def query_async(self, prompt: str, model: str, num_predict: int = 2048, force_json: bool = True) -> str:
        try:
            client = ollama.AsyncClient()
            options = {
                "temperature":    0.1,
                "num_predict":    num_predict,
                "top_p":          0.9,
                "repeat_penalty": 1.1,
                "stop":           ["USER:", "Human:", "Assistant:"]
            }
            kwargs = {
                "model":   model,
                "prompt":  prompt,
                "options": options,
            }
            if force_json:
                kwargs["format"] = "json"

            response = await client.generate(**kwargs)
            return response.get("response", "{}")
        except Exception as exc:
            print(f"[Council] Error querying {model}: {exc}")
            return "{}"

    def query(self, prompt: str, model: str, num_predict: int = 2048, force_json: bool = True) -> str:
        return asyncio.run(self.query_async(prompt, model, num_predict, force_json))

    def parse_json(self, text: str) -> dict:
        if not text or not text.strip():
            return {}
        for attempt in [
            lambda t: json.loads(t.strip()),
            lambda t: json.loads(t[t.find("```json")+7:t.find("```",t.find("```json")+7)].strip()) if "```json" in t else None,
            lambda t: json.loads(t[t.find("```")+3:t.find("```",t.find("```")+3)].strip()) if "```" in t else None,
            lambda t: json.loads(t[t.find("{"):t.rfind("}")+1]) if "{" in t else None,
        ]:
            try:
                result = attempt(text)
                if result:
                    return result
            except Exception:
                pass
        # Final attempt — fix common issues
        try:
            s = text.find("{")
            e = text.rfind("}") + 1
            if s != -1 and e > s:
                chunk = text[s:e].replace("'", '"').replace("True","true").replace("False","false").replace("None","null")
                return json.loads(chunk)
        except Exception:
            pass
        print(f"[Council] JSON parse failed: {text[:200]}")
        return {}


# ─────────────────────────────────────────
# HALLUCINATION DETECTOR
# ─────────────────────────────────────────

class HallucinationDetector:

    def detect(self, council_outputs: List[dict]) -> Dict:
        valid = [o for o in council_outputs if o.get("conditions")]
        if len(valid) < 2:
            return {"outliers": [], "agreement_score": 0.5, "majority_condition": "unknown"}

        tops = [o["conditions"][0].get("condition","").lower().strip() for o in valid]
        counts = Counter(tops)
        majority, majority_count = counts.most_common(1)[0]

        outliers = []
        for o in valid:
            top = o["conditions"][0].get("condition","").lower().strip()
            if top != majority and majority_count >= 2:
                outliers.append({"doctor": o.get("doctor"), "diagnosis": o["conditions"][0].get("condition")})
                print(f"[Hallucination] ⚠️  {o.get('doctor')} outlier: {o['conditions'][0].get('condition')}")

        return {
            "outliers":           outliers,
            "majority_condition": majority,
            "agreement_score":    round(majority_count / len(tops), 2)
        }


# ─────────────────────────────────────────
# WEIGHTED CONSENSUS ENGINE
# ─────────────────────────────────────────

class WeightedConsensusEngine:

    def _get_conditions(self, doctor_name: str, council_outputs: list, debate_outputs: list) -> list:
        """Get best conditions — debate output if non-empty, else council output."""
        for o in debate_outputs:
            if o.get("doctor") == doctor_name:
                updated = [c for c in _safe_list(o.get("updated_conditions",[])) if isinstance(c, dict) and c.get("condition")]
                if updated:
                    return updated
        for o in council_outputs:
            if o.get("doctor") == doctor_name:
                return [c for c in _safe_list(o.get("conditions",[])) if isinstance(c, dict) and c.get("condition")]
        return []

    def build(self, council_outputs, debate_outputs, hallucination_report, patient_id, execution_time) -> FinalClinicalOutput:
        try:
            outlier_doctors = {o["doctor"] for o in hallucination_report.get("outliers", [])}
            scores: Dict[str, dict] = {}

            for doctor in COUNCIL:
                conditions = self._get_conditions(doctor["name"], council_outputs, debate_outputs)
                if not conditions:
                    print(f"[Consensus] No conditions for {doctor['name']} — skipping")
                    continue

                weight = doctor["weight"]
                if doctor["name"] in outlier_doctors:
                    weight *= 0.6
                for d in debate_outputs:
                    if d.get("doctor") == doctor["name"] and d.get("agrees_with_majority"):
                        weight *= 1.1
                        break

                for i, cond in enumerate(conditions[:3]):
                    name = _to_str(cond.get("condition","Unknown")).strip()
                    if not name or name in ("Unknown", ""):
                        continue
                    prob = max(0, min(100, _safe_float(cond.get("probability", 50), 50)))
                    conf = max(0, min(100, _safe_float(cond.get("confidence", 50), 50)))
                    pos  = [1.0, 0.6, 0.3][i]
                    score = prob * conf * weight * pos

                    if name not in scores:
                        scores[name] = {"total_score":0,"evidence":[],"reasoning":[],"probabilities":[],"confidences":[]}

                    scores[name]["total_score"]    += score
                    scores[name]["probabilities"].append(prob)
                    scores[name]["confidences"].append(conf)
                    for e in _safe_list(cond.get("evidence",[])):
                        ev = _to_str(e).strip()
                        if ev and ev not in scores[name]["evidence"]:
                            scores[name]["evidence"].append(ev)
                    r = _to_str(cond.get("reasoning","")).strip()
                    if r:
                        scores[name]["reasoning"].append(f"{doctor['name']}: {r}")

            sorted_conds = sorted(scores.items(), key=lambda x: x[1]["total_score"], reverse=True)

            final: List[ClinicalCondition] = []
            for name, data in sorted_conds[:3]:
                probs = data["probabilities"]
                confs = data["confidences"]
                final.append(ClinicalCondition(
                    condition   = name,
                    probability = round(sum(probs)/len(probs) if probs else 50, 1),
                    confidence  = round(sum(confs)/len(confs) if confs else 50, 1),
                    evidence    = data["evidence"][:5],
                    reasoning   = " | ".join(data["reasoning"][:2]) or "Council consensus"
                ))

            # ── Fallback to best single model if empty
            if not final:
                print("[Consensus] ⚠️  Empty — using best model fallback")
                best = max(
                    [o for o in council_outputs if o.get("conditions")],
                    key=lambda o: next((d["weight"] for d in COUNCIL if d["name"]==o.get("doctor")),0),
                    default=None
                )
                if best:
                    for c in best["conditions"][:3]:
                        final.append(ClinicalCondition(
                            condition   = _to_str(c.get("condition","Unknown")),
                            probability = _safe_float(c.get("probability",50),50),
                            confidence  = _safe_float(c.get("confidence",45),45),
                            evidence    = [_to_str(e) for e in _safe_list(c.get("evidence",[]))],
                            reasoning   = _to_str(c.get("reasoning","Fallback output"))
                        ))

            avg_conf = sum(c.confidence for c in final)/len(final) if final else 0.0

            missing = list({_to_str(x).strip() for o in council_outputs for x in _safe_list(o.get("missing_data",[])) if _to_str(x).strip()})
            flags: List[str] = []
            for o in council_outputs:
                for f in _safe_list(o.get("urgent_flags",[])):
                    s = _to_str(f).strip()
                    if s and s not in flags:
                        flags.append(s)
            if avg_conf < 50:
                flags.append("LOW CONFIDENCE — Doctor review strongly recommended")
            if outlier_doctors:
                flags.append(f"COUNCIL DISAGREEMENT — {len(outlier_doctors)} model(s) flagged as outliers")

            council_votes = {o.get("doctor"): (o["conditions"][0].get("condition","Unknown") if o.get("conditions") else "No output") for o in council_outputs}

            best_out = max([o for o in council_outputs if o.get("conditions")], key=lambda o: next((d["weight"] for d in COUNCIL if d["name"]==o.get("doctor")),0), default={})
            summary = _to_str(best_out.get("reasoning_summary","")) or f"Council of {len(COUNCIL)} AI specialists. Agreement: {hallucination_report.get('agreement_score',0)*100:.0f}%."

            return FinalClinicalOutput(
                patient_id               = patient_id,
                top_3_conditions         = final,
                consensus_confidence     = round(avg_conf, 1),
                agents_agreed            = len(outlier_doctors) == 0,
                council_votes            = council_votes,
                disagreement_details     = f"Outliers: {', '.join(outlier_doctors)}" if outlier_doctors else None,
                missing_data_suggestions = missing,
                safety_flags             = flags,
                doctor_review_required   = (avg_conf < 60 or bool(outlier_doctors) or bool(flags)),
                reasoning_summary        = summary,
                execution_time_seconds   = round(execution_time, 1)
            )

        except Exception as e:
            print(f"[Consensus] ❌ CRASH: {e}")
            traceback.print_exc()
            # Emergency fallback
            final = []
            best = max([o for o in council_outputs if o.get("conditions")], key=lambda o: next((d["weight"] for d in COUNCIL if d["name"]==o.get("doctor")),0), default=None)
            if best:
                for c in best.get("conditions",[])[:3]:
                    final.append(ClinicalCondition(
                        condition=_to_str(c.get("condition","Unknown")),
                        probability=_safe_float(c.get("probability",50),50),
                        confidence=_safe_float(c.get("confidence",45),45),
                        evidence=[_to_str(e) for e in _safe_list(c.get("evidence",[]))],
                        reasoning=_to_str(c.get("reasoning","Emergency fallback"))
                    ))
            return FinalClinicalOutput(
                patient_id=patient_id, top_3_conditions=final,
                consensus_confidence=45.0, agents_agreed=False, council_votes={},
                disagreement_details="Consensus error — single model fallback used",
                missing_data_suggestions=["Full assessment recommended"],
                safety_flags=["PARTIAL OUTPUT — Doctor review required"],
                doctor_review_required=True,
                reasoning_summary="Emergency fallback — consensus engine error",
                execution_time_seconds=round(execution_time,1)
            )


# ─────────────────────────────────────────
# MAIN CLINICAL REASONER
# ─────────────────────────────────────────

class ClinicalReasoner:

    def __init__(self):
        self.llm       = CouncilLLMClient()
        self.prompts   = PromptBuilder()
        self.detector  = HallucinationDetector()
        self.consensus = WeightedConsensusEngine()
        print(f"[Council] Initialized with {len(COUNCIL)} members:")
        for d in COUNCIL:
            print(f"  {d['name']} ({d['specialty']}) — {d['model']}")

    async def _run_doctor_async(self, doctor: dict, ps: dict) -> dict:
        print(f"[Council] {doctor['name']} analyzing...")
        t0 = time.time()
        raw = await self.llm.query_async(self.prompts.diagnosis_prompt(ps, doctor), doctor["model"], doctor["tokens"])
        output = self.llm.parse_json(raw)
        elapsed = round(time.time()-t0, 1)

        conditions = [c for c in _safe_list(output.get("conditions",[])) if isinstance(c,dict) and c.get("condition")]
        if not conditions:
            print(f"[Council] ⚠️  {doctor['name']} no conditions ({elapsed}s) — raw snippet: {raw[:100]}")
            return {"doctor":doctor["name"],"specialty":doctor["specialty"],"conditions":[],"missing_data":[],"urgent_flags":[],"reasoning_summary":"Parse failed"}

        output["conditions"] = conditions
        output["doctor"]     = doctor["name"]
        output["specialty"]  = doctor["specialty"]
        print(f"[Council] ✅ {doctor['name']} {elapsed}s — top: {conditions[0].get('condition','?')}")
        return output

    def _run_doctor(self, doctor: dict, ps: dict) -> dict:
        return asyncio.run(self._run_doctor_async(doctor, ps))

    async def _run_debate_async(self, doctor: dict, ps: dict, all_outputs: list) -> dict:
        print(f"[Council] {doctor['name']} debating...")
        raw = await self.llm.query_async(self.prompts.debate_prompt(ps, doctor, all_outputs), doctor["model"], 512)
        output = self.llm.parse_json(raw)
        return {
            "doctor":                doctor["name"],
            "agrees_with_majority":  bool(output.get("agrees_with_majority", True)),
            "disagreement_reason":   str(output.get("disagreement_reason", "")),
            "updated_top_condition": str(output.get("updated_top_condition", "")),
            "updated_conditions":    _safe_list(output.get("updated_conditions", [])),
            "confidence_after_debate": _safe_float(output.get("confidence_after_debate", 70), 70),
            "additional_insights":   str(output.get("additional_insights", ""))
        }

    def _run_debate(self, doctor: dict, ps: dict, all_outputs: list) -> dict:
        return asyncio.run(self._run_debate_async(doctor, ps, all_outputs))

    # ── Model key → COUNCIL entry ──
    MODEL_KEY_MAP = {
        "medgemma":   "Dr. Gemma",
        "openbiollm": "Dr. OpenBio",
        "mistral":    "Dr. Mistral",
    }

    def analyze_single(self, patient_state: dict, model_key: str) -> FinalClinicalOutput:
        """Run a single model (no debate/consensus). Used when user selects a specific model."""
        pid   = patient_state.get("patient_id", "unknown")
        start = time.time()
        doctor_name = self.MODEL_KEY_MAP.get(model_key)
        doctor = next((d for d in COUNCIL if d["name"] == doctor_name), None)

        if not doctor:
            return FinalClinicalOutput(
                patient_id=pid, top_3_conditions=[], consensus_confidence=0,
                agents_agreed=False, council_votes={},
                disagreement_details=f"Unknown model key: {model_key}",
                missing_data_suggestions=[], safety_flags=["INVALID MODEL"],
                doctor_review_required=True,
                reasoning_summary=f"Model '{model_key}' not found.",
                execution_time_seconds=0
            )

        print(f"\n[SingleModel] Running {doctor['name']} only ({doctor['model']})")
        output = self._run_doctor(doctor, patient_state)
        total  = round(time.time() - start, 1)

        conditions = output.get("conditions", [])[:3]
        final = [
            ClinicalCondition(
                condition   = _to_str(c.get("condition", "Unknown")),
                probability = _safe_float(c.get("probability", 50), 50),
                confidence  = _safe_float(c.get("confidence", 50), 50),
                evidence    = [_to_str(e) for e in _safe_list(c.get("evidence", []))],
                reasoning   = _to_str(c.get("reasoning", ""))
            )
            for c in conditions if isinstance(c, dict) and c.get("condition")
        ]

        avg_conf = sum(c.confidence for c in final) / len(final) if final else 0.0
        return FinalClinicalOutput(
            patient_id               = pid,
            top_3_conditions         = final,
            consensus_confidence     = round(avg_conf, 1),
            agents_agreed            = True,
            council_votes            = {doctor["name"]: final[0].condition if final else "No output"},
            disagreement_details     = None,
            missing_data_suggestions = [_to_str(x) for x in _safe_list(output.get("missing_data", []))],
            safety_flags             = [_to_str(x) for x in _safe_list(output.get("urgent_flags", []))],
            doctor_review_required   = avg_conf < 60,
            reasoning_summary        = _to_str(output.get("reasoning_summary", f"Analysis by {doctor['name']} ({doctor['specialty']})")),
            execution_time_seconds   = total
        )

    def analyze(self, patient_state: dict) -> FinalClinicalOutput:

        pid   = patient_state.get("patient_id", "unknown")
        start = time.time()

        print(f"\n[Council] {'='*40}")
        print(f"[Council] Patient: {pid}")
        print(f"[Council] {'='*40}")

        try:
            # ROUND 1 — Parallel diagnosis
            print(f"\n[Council] ROUND 1 — {len(COUNCIL)} models in parallel")
            
            async def run_round_1():
                tasks = [self._run_doctor_async(d, patient_state) for d in COUNCIL]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                outputs = []
                for idx, r in enumerate(results):
                    if isinstance(r, Exception):
                        doc = COUNCIL[idx]
                        print(f"[Council] ❌ {doc['name']} failed: {r}")
                        outputs.append({"doctor":doc["name"],"specialty":doc["specialty"],"conditions":[],"missing_data":[],"urgent_flags":[],"reasoning_summary":str(r)})
                    else:
                        outputs.append(r)
                return outputs

            council_outputs = asyncio.run(run_round_1())

            valid = [o for o in council_outputs if o.get("conditions")]
            print(f"[Council] Round 1: {len(valid)}/{len(COUNCIL)} succeeded in {round(time.time()-start,1)}s")

            if not valid:
                return FinalClinicalOutput(
                    patient_id=pid, top_3_conditions=[], consensus_confidence=0,
                    agents_agreed=False, council_votes={},
                    disagreement_details="All models failed",
                    missing_data_suggestions=["Complete clinical assessment required"],
                    safety_flags=["SYSTEM ERROR — Please try again"],
                    doctor_review_required=True,
                    reasoning_summary="All council members failed. Please try again.",
                    execution_time_seconds=round(time.time()-start,1)
                )

            # ROUND 2 — Hallucination detection
            print(f"\n[Council] ROUND 2 — Hallucination detection")
            h_report = self.detector.detect(council_outputs)
            print(f"[Council] Agreement: {h_report['agreement_score']*100:.0f}% | Majority: {h_report.get('majority_condition','?')}")

            # ROUND 3 — Parallel debate
            print(f"\n[Council] ROUND 3 — Parallel debate")
            r3 = time.time()
            
            async def run_round_3():
                tasks = [self._run_debate_async(d, patient_state, council_outputs) for d in COUNCIL]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                outputs = []
                for idx, r in enumerate(results):
                    if isinstance(r, Exception):
                        doc = COUNCIL[idx]
                        outputs.append({"doctor":doc["name"],"agrees_with_majority":True,"updated_conditions":[],"confidence_after_debate":60})
                    else:
                        outputs.append(r)
                return outputs

            debate_outputs = asyncio.run(run_round_3())
            print(f"[Council] Debate done in {round(time.time()-r3,1)}s")

            # ROUND 4 — Consensus
            print(f"\n[Council] ROUND 4 — Weighted consensus")
            total = round(time.time()-start, 1)
            result = self.consensus.build(council_outputs, debate_outputs, h_report, pid, total)

            print(f"\n[Council] {'='*40}")
            print(f"[Council] ✅ Done in {total}s | Confidence: {result.consensus_confidence}% | Agreed: {result.agents_agreed}")
            if result.top_3_conditions:
                print(f"[Council] Top: {result.top_3_conditions[0].condition}")
            print(f"[Council] {'='*40}\n")
            return result

        except Exception as e:
            print(f"[Council] ❌ FATAL: {e}")
            traceback.print_exc()
            return FinalClinicalOutput(
                patient_id=pid, top_3_conditions=[], consensus_confidence=0,
                agents_agreed=False, council_votes={},
                disagreement_details=str(e),
                missing_data_suggestions=["Manual assessment required"],
                safety_flags=["SYSTEM ERROR — Consult a doctor directly"],
                doctor_review_required=True,
                reasoning_summary=f"System error: {str(e)}. Please try again.",
                execution_time_seconds=round(time.time()-start,1)
            )