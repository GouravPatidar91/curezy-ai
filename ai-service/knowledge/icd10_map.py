"""
knowledge/icd10_map.py — ICD-10 Canonical Name Normalizer (Phase 2.3)
Maps common condition name variants to their WHO canonical ICD-10 name.
Prevents "Flu" and "Influenza" from being treated as different diagnoses
in the consensus engine.
"""

from typing import Optional, Tuple
import difflib


# ─────────────────────────────────────────────────────────────────────────────
# ICD-10 CANONICAL MAP
# Format: canonical_name → [variant names, abbreviations, common misspellings]
# ─────────────────────────────────────────────────────────────────────────────

ICD10_CANONICAL: dict = {
    # ── Respiratory ──────────────────────────────────────────────────────────
    "Influenza":                               ["flu", "influenza a", "influenza b", "seasonal flu", "the flu", "grippe"],
    "COVID-19":                                ["covid", "coronavirus", "sars-cov-2", "covid19", "covid 19"],
    "Community-Acquired Pneumonia":            ["pneumonia", "cap", "lobar pneumonia", "bacterial pneumonia", "viral pneumonia", "atypical pneumonia"],
    "Viral Upper Respiratory Infection":       ["uri", "cold", "common cold", "viral uri", "urti", "viral urti", "upper respiratory infection", "viral respiratory infection"],
    "Acute Bronchitis":                        ["bronchitis", "chest infection", "acute chest infection"],
    "Asthma Exacerbation":                     ["asthma attack", "asthma exacerbation", "acute asthma", "severe asthma"],
    "COPD Exacerbation":                       ["copd", "chronic bronchitis", "emphysema exacerbation"],
    "Acute Sinusitis":                         ["sinusitis", "sinus infection", "rhinosinusitis", "acute rhinosinusitis"],
    "Pulmonary Embolism":                      ["pe", "pulmonary embolus", "pulmonary thromboembolism", "lung clot"],

    # ── Neurological ─────────────────────────────────────────────────────────
    "Bacterial Meningitis":                    ["meningitis", "bacterial meningitis", "purulent meningitis", "septic meningitis"],
    "Viral Meningitis":                        ["aseptic meningitis", "viral meningitis", "lymphocytic meningitis"],
    "Migraine":                                ["migraine headache", "migraine without aura", "classical migraine", "migraine attack"],
    "Migraine with Aura":                      ["aura migraine", "classical migraine with aura", "hemiplegic migraine"],
    "Tension Headache":                        ["tension type headache", "tension-type headache", "tth", "muscle contraction headache"],
    "Subarachnoid Hemorrhage":                 ["sah", "subarachnoid haemorrhage", "brain bleed", "subarachnoid bleed"],
    "Acute Ischemic Stroke":                   ["stroke", "cva", "cerebrovascular accident", "ischemic stroke", "tia", "transient ischemic attack"],
    "Benign Paroxysmal Positional Vertigo":    ["bppv", "positional vertigo", "ear crystals", "otolith vertigo"],
    "Vestibular Neuritis":                     ["labyrinthitis", "vestibular neuronitis", "inner ear infection", "acute vestibular neuritis"],

    # ── Cardiac ──────────────────────────────────────────────────────────────
    "Acute Myocardial Infarction":             ["heart attack", "mi", "ami", "stemi", "nstemi", "myocardial infarct", "myocardial infarction"],
    "Unstable Angina":                         ["acs", "acute coronary syndrome", "unstable angina pectoris"],
    "Atrial Fibrillation":                     ["afib", "af", "a fib", "atrial fibrillation", "irregular heartbeat"],
    "Heart Failure":                           ["congestive heart failure", "chf", "decompensated heart failure", "cardiac failure"],
    "Hypertensive Emergency":                  ["malignant hypertension", "hypertensive crisis", "hypertensive urgency", "hypertensive emergency"],

    # ── Gastrointestinal ─────────────────────────────────────────────────────
    "Viral Gastroenteritis":                   ["stomach flu", "gastro", "gastroenteritis", "stomach bug", "norovirus", "rotavirus", "intestinal flu"],
    "Acute Appendicitis":                      ["appendicitis", "inflamed appendix"],
    "Acute Pancreatitis":                      ["pancreatitis", "inflamed pancreas"],
    "Acute Cholecystitis":                     ["cholecystitis", "gallbladder infection", "gallbladder inflammation"],
    "Peptic Ulcer Disease":                    ["peptic ulcer", "gastric ulcer", "duodenal ulcer", "stomach ulcer"],
    "Gastroesophageal Reflux Disease":         ["gerd", "gord", "acid reflux", "acid indigestion", "heartburn"],
    "Irritable Bowel Syndrome":                ["ibs", "irritable colon", "spastic colon"],
    "Inflammatory Bowel Disease":             ["ibd", "crohn's", "crohns disease", "ulcerative colitis"],

    # ── Infectious ───────────────────────────────────────────────────────────
    "Urinary Tract Infection":                 ["uti", "bladder infection", "cystitis", "urine infection", "urinary infection"],
    "Pyelonephritis":                          ["kidney infection", "upper uti", "renal infection"],
    "Sepsis":                                  ["blood poisoning", "bacteraemia", "septicaemia", "septicemia", "systemic infection"],
    "Infectious Mononucleosis":                ["mono", "epstein barr", "ebv", "kissing disease", "glandular fever"],
    "Dengue Fever":                            ["dengue", "dengue hemorrhagic fever", "breakbone fever"],
    "Malaria":                                 ["malarial fever", "plasmodium infection"],
    "Lyme Disease":                            ["lyme borreliosis", "tick disease"],

    # ── Musculoskeletal ───────────────────────────────────────────────────────
    "Rheumatoid Arthritis":                    ["ra", "inflammatory arthritis", "rheumatoid joint disease"],
    "Osteoarthritis":                          ["oa", "degenerative joint disease", "wear and tear arthritis"],
    "Gout":                                    ["gouty arthritis", "hyperuricemia", "uric acid arthritis"],
    "Systemic Lupus Erythematosus":            ["sle", "lupus", "systemic lupus"],

    # ── Endocrine/Metabolic ───────────────────────────────────────────────────
    "Type 2 Diabetes Mellitus":                ["t2dm", "type 2 diabetes", "diabetes", "adult-onset diabetes", "non-insulin dependent diabetes"],
    "Hypothyroidism":                          ["underactive thyroid", "thyroid deficiency", "hashimoto's thyroiditis"],
    "Hyperthyroidism":                         ["overactive thyroid", "thyrotoxicosis", "graves disease"],
    "Anemia":                                  ["anaemia", "iron deficiency anaemia", "iron deficiency anemia", "low hemoglobin", "low haemoglobin"],
}

# Build reverse lookup (variant → canonical)
_REVERSE_MAP: dict = {}
for canonical, variants in ICD10_CANONICAL.items():
    _REVERSE_MAP[canonical.lower()] = canonical
    for variant in variants:
        _REVERSE_MAP[variant.lower()] = canonical


def normalize_condition_name(condition: str) -> str:
    """
    Normalize a condition name to its WHO ICD-10 canonical form.
    Uses exact match first, then fuzzy matching.
    Returns the canonical name or the original if no match found.
    """
    if not condition:
        return condition

    lower = condition.lower().strip()

    # Exact match
    if lower in _REVERSE_MAP:
        return _REVERSE_MAP[lower]

    # Fuzzy match (threshold 0.75)
    all_keys = list(_REVERSE_MAP.keys())
    matches = difflib.get_close_matches(lower, all_keys, n=1, cutoff=0.75)
    if matches:
        return _REVERSE_MAP[matches[0]]

    # Partial match (substring check)
    for key, canonical in _REVERSE_MAP.items():
        if lower in key or key in lower:
            return canonical

    return condition  # Return original if no match


def normalize_conditions_list(conditions: list) -> list:
    """Normalize all condition names in a council output conditions list."""
    result = []
    for c in conditions:
        if isinstance(c, dict):
            original_name = c.get("condition", "")
            canonical     = normalize_condition_name(original_name)
            if canonical != original_name:
                print(f"[ICD10] Normalized: '{original_name}' → '{canonical}'")
            result.append({**c, "condition": canonical})
        else:
            result.append(c)
    return result
