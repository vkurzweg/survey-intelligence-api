#!/usr/bin/env python3
"""
Targeted fix: correct missed normalizations in profile.unaided_brands.
profile.unaided_brands_raw is NOT touched.
"""

import json
import re
import os
from collections import Counter

RESPONDENTS_PATH = "data/respondents.json"
N = 600

STUDY_BRANDS_16 = {
    "Cognizant", "Accenture", "IBM Consulting", "Infosys", "Capgemini",
    "Wipro", "Tata Consultancy Services (TCS)", "EY", "HCL Technologies",
    "Deloitte", "McKinsey & Company", "Google (Cloud & Gemini)",
    "DXC Technology", "ServiceNow", "Microsoft (Azure & Copilot)",
    "Amazon Web Services (AWS)",
}

# ---------------------------------------------------------------------------
# Normalization map: lowercase-stripped input → canonical name
# Derived exactly from the task specification.
# ---------------------------------------------------------------------------
NORM_MAP = {
    # Google
    "goolge":           "Google (Cloud & Gemini)",
    "gogle":            "Google (Cloud & Gemini)",
    "goggle":           "Google (Cloud & Gemini)",
    "google cloud":     "Google (Cloud & Gemini)",
    "google gemini":    "Google (Cloud & Gemini)",
    "google":           "Google (Cloud & Gemini)",
    # HCL
    "hcltech":          "HCL Technologies",
    "hcl tech":         "HCL Technologies",
    "hcl tech":         "HCL Technologies",   # 'hcl tech' normalised
    "hcl":              "HCL Technologies",
    # ServiceNow
    "service now":      "ServiceNow",
    "servicenow":       "ServiceNow",
    # Deloitte
    "deloite":          "Deloitte",
    "deloitte & touche":"Deloitte",
    "deloitte":         "Deloitte",
    "deloitte digital": "Deloitte",     # sub-brand, fold to parent
    # IBM
    "ibm<":             "IBM Consulting",
    "bm":               "IBM Consulting",
    "ibm consulting":   "IBM Consulting",
    "ibm":              "IBM Consulting",
    # Microsoft
    "icrosoft":                  "Microsoft (Azure & Copilot)",
    "smicrosoft":                "Microsoft (Azure & Copilot)",
    "microsft":                  "Microsoft (Azure & Copilot)",
    "micosoft":                  "Microsoft (Azure & Copilot)",
    "microsoft":                 "Microsoft (Azure & Copilot)",
    "microsoft azure":           "Microsoft (Azure & Copilot)",
    "ms azure":                  "Microsoft (Azure & Copilot)",
    "azure":                     "Microsoft (Azure & Copilot)",
    "microsoft cloud":           "Microsoft (Azure & Copilot)",
    "microsoft/azure & copilot": "Microsoft (Azure & Copilot)",
    # Infosys
    "inofsys":          "Infosys",
    "infosys ltd":      "Infosys",
    "infosys":          "Infosys",
    # TCS
    "tcs":                   "Tata Consultancy Services (TCS)",
    "tata consulting":        "Tata Consultancy Services (TCS)",
    "tata consultancy":       "Tata Consultancy Services (TCS)",
    # Accenture
    "accenture inc":    "Accenture",
    "accenture":        "Accenture",
    # Cognizant
    "cognizant technology": "Cognizant",
    "cognizant":            "Cognizant",
    # Capgemini
    "capgemini se":     "Capgemini",
    "capgemini":        "Capgemini",
    # AWS
    "amazon":                    "Amazon Web Services (AWS)",
    "amazon web services":       "Amazon Web Services (AWS)",
    "amazon web service":        "Amazon Web Services (AWS)",   # singular typo
    "aws":                       "Amazon Web Services (AWS)",
    # Wipro
    "wipro ltd":        "Wipro",
    "wipro":            "Wipro",
    # EY
    "ey consulting":    "EY",
    "ernst & young":    "EY",
    "ernst and young":  "EY",
    "ey":               "EY",
    # McKinsey
    "mckinsey":              "McKinsey & Company",
    "mckinsey and company":  "McKinsey & Company",
    # DXC
    "dxc":              "DXC Technology",
}

# Compile a set for quick "already canonical" check
CANONICAL_LOWER = {b.lower() for b in STUDY_BRANDS_16}

# Regex for "Brand N: <name>" pattern
BRAND_N_RE = re.compile(r"^brand\s+\d+\s*:\s*(.+)$", re.IGNORECASE)


def normalize_one(s: str) -> str:
    """
    Return canonical name if the string matches a normalization rule,
    otherwise return the original string unchanged.
    """
    stripped = s.strip()
    key = stripped.lower()

    # Already a canonical study brand → no change needed
    if key in CANONICAL_LOWER:
        return stripped

    # "Brand N: <name>" pattern — recurse on the extracted name
    m = BRAND_N_RE.match(stripped)
    if m:
        inner = m.group(1).strip()
        return normalize_one(inner)

    # Direct lookup
    if key in NORM_MAP:
        return NORM_MAP[key]

    return stripped  # unchanged


def main():
    with open(RESPONDENTS_PATH) as f:
        data = json.load(f)
    assert len(data) == N

    records_updated = 0
    replacements_made = 0
    replacement_log = Counter()   # (old, new) → count

    for r in data:
        old_brands = r["profile"].get("unaided_brands") or []
        new_brands = []
        changed = False
        for b in old_brands:
            if not b or not b.strip():
                new_brands.append(b)
                continue
            canonical = normalize_one(b)
            if canonical != b:
                replacement_log[(b, canonical)] += 1
                replacements_made += 1
                changed = True
            new_brands.append(canonical)
        if changed:
            r["profile"]["unaided_brands"] = new_brands
            records_updated += 1

    # -----------------------------------------------------------------------
    # Report
    # -----------------------------------------------------------------------
    print("=" * 60)
    print("NORMALIZATION FIX — RESULTS")
    print("=" * 60)
    print(f"Records updated:        {records_updated}")
    print(f"Individual replacements:{replacements_made}")
    print()
    print("Replacements applied (old → new):")
    for (old, new), cnt in sorted(replacement_log.items(), key=lambda x: -x[1]):
        print(f"  {repr(old):<45} → {repr(new)}  (×{cnt})")

    # -----------------------------------------------------------------------
    # Re-run B1-11 unaided frequency table with corrected data
    # -----------------------------------------------------------------------
    print()
    print("=" * 60)
    print("B1-11 (CORRECTED): Unaided brand awareness frequency table")
    print("=" * 60)

    total_mentions = Counter()
    first_mentions = Counter()
    brands_per_resp = Counter()
    remaining_non_study = Counter()

    for r in data:
        normalized = [b for b in (r["profile"].get("unaided_brands") or [])
                      if b and b.strip()]
        brands_per_resp[len(normalized)] += 1
        for b in normalized:
            total_mentions[b] += 1
            if b not in STUDY_BRANDS_16:
                remaining_non_study[b] += 1

        # First mention: use slot_1 from verbatims, mapped through current normalized list
        raw_list = r["profile"].get("unaided_brands_raw") or []
        norm_list = normalized
        raw_slot1 = r["verbatims"].get("unaided_raw", {}).get("slot_1")
        if raw_slot1 and raw_slot1.strip():
            norm_map_local = {}
            for i, raw in enumerate(raw_list):
                if i < len(norm_list):
                    norm_map_local[raw.strip().lower()] = norm_list[i]
            norm_first = norm_map_local.get(raw_slot1.strip().lower(), normalize_one(raw_slot1.strip()))
            first_mentions[norm_first] += 1

    resp_with_mention = sum(1 for r in data if (r["profile"].get("unaided_brands") or []))
    print(f"Total respondents with ≥1 mention: {resp_with_mention}")
    print()
    print(f"  {'Brand':<48} {'Total':>6}  {'First':>6}  {'Study?':>6}")
    print(f"  {'-'*72}")
    for brand, cnt in sorted(total_mentions.items(), key=lambda x: -x[1]):
        fm = first_mentions.get(brand, 0)
        study = "YES" if brand in STUDY_BRANDS_16 else "no"
        print(f"  {brand:<48} {cnt:>6}  {fm:>6}  {study:>6}")

    print()
    print("Distribution of brands named per respondent:")
    for k in sorted(brands_per_resp):
        c = brands_per_resp[k]
        print(f"  {k} brand(s): {c} respondents ({c/N*100:.1f}%)")

    # -----------------------------------------------------------------------
    # Remaining non-study strings
    # -----------------------------------------------------------------------
    print()
    print("=" * 60)
    print("REMAINING NON-STUDY STRINGS IN profile.unaided_brands")
    print("=" * 60)
    if remaining_non_study:
        print(f"  {'String':<48} {'Count':>6}")
        print(f"  {'-'*56}")
        for b, cnt in sorted(remaining_non_study.items(), key=lambda x: -x[1]):
            print(f"  {b:<48} {cnt:>6}")
        print(f"\n  Total distinct non-study strings: {len(remaining_non_study)}")
        print(f"  Total non-study mentions:          {sum(remaining_non_study.values())}")
    else:
        print("  None — all values now map to one of the 16 study brands.")

    # -----------------------------------------------------------------------
    # Write and confirm
    # -----------------------------------------------------------------------
    with open(RESPONDENTS_PATH, "w") as f:
        json.dump(data, f, indent=2)

    print()
    print("=" * 60)
    print(f"All {len(data)} records confirmed intact.")
    print(f"Written to {RESPONDENTS_PATH}")


if __name__ == "__main__":
    main()
