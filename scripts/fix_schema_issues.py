#!/usr/bin/env python3
"""
Fix script for 6 identified schema issues in insightops_v1 respondents data.
Operates on data/respondents.json and writes updated file in-place.
"""

import json
import statistics
from collections import Counter
from copy import deepcopy

RESPONDENTS_PATH = "data/respondents.json"

# ---------------------------------------------------------------------------
# Brand normalization map for S8 unaided mentions
# Keys are lowercase-stripped variants; values are canonical names
# ---------------------------------------------------------------------------
BRAND_NORM_MAP = {
    # IBM
    "ibm": "IBM Consulting",
    "ibm consulting": "IBM Consulting",
    "ibm global services": "IBM Consulting",
    # Accenture
    "accenture": "Accenture",
    "ccenture": "Accenture",
    "accentuee": "Accenture",
    # Microsoft
    "microsoft": "Microsoft (Azure & Copilot)",
    "microsoft azure": "Microsoft (Azure & Copilot)",
    "microsoft azure": "Microsoft (Azure & Copilot)",
    "azure": "Microsoft (Azure & Copilot)",
    "mucrisoft": "Microsoft (Azure & Copilot)",
    # AWS / Amazon
    "aws": "Amazon Web Services (AWS)",
    "amazon": "Amazon Web Services (AWS)",
    "amazon web services": "Amazon Web Services (AWS)",
    "amazon web services (aws)": "Amazon Web Services (AWS)",
    # Google
    "google": "Google (Cloud & Gemini)",
    "google cloud": "Google (Cloud & Gemini)",
    "goigle": "Google (Cloud & Gemini)",
    "goggle": "Google (Cloud & Gemini)",
    # Deloitte
    "deloitte": "Deloitte",
    "deolitte": "Deloitte",
    "delottie": "Deloitte",
    "deloitte, openly": "Deloitte",
    # Infosys
    "infosys": "Infosys",
    # Cognizant
    "cognizant": "Cognizant",
    # Wipro
    "wipro": "Wipro",
    # Capgemini
    "capgemini": "Capgemini",
    # TCS
    "tcs": "Tata Consultancy Services (TCS)",
    "tata": "Tata Consultancy Services (TCS)",
    "tata consultancy services (tcs)": "Tata Consultancy Services (TCS)",
    # EY
    "ey": "EY",
    # HCL
    "hcl technologies": "HCL Technologies",
    "hcl": "HCL Technologies",
    # McKinsey
    "mckinsey & company": "McKinsey & Company",
    # DXC
    "dxc technology": "DXC Technology",
    "dtx": "DXC Technology",
    # ServiceNow
    "servicenow": "ServiceNow",
    # Salesforce
    "salesforce": "Salesforce",
    # PwC
    "pwc": "PwC",
    # Dell
    "dell": "Dell Technologies",
    "dell technologies": "Dell Technologies",
    # KPMG
    "kpmg": "KPMG",
    # Oracle
    "oracle": "Oracle",
    # Cisco
    "cisco": "Cisco",
    # SAP
    "sap": "SAP",
    # Nvidia
    "nvidia": "NVIDIA",
    # Meta
    "meta": "Meta",
    # Adobe
    "adobe": "Adobe",
    # Workday
    "workday": "Workday",
    # Apple
    "apple": "Apple",
}


def normalize_brand(raw: str) -> str:
    """Return canonical brand name, or the title-cased raw value if unrecognized."""
    key = raw.strip().lower()
    return BRAND_NORM_MAP.get(key, raw.strip())


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    with open(RESPONDENTS_PATH) as f:
        data = json.load(f)

    print(f"Loaded {len(data)} records.\n")

    # -----------------------------------------------------------------------
    # ISSUE 1: S6 function label audit (read-only)
    # -----------------------------------------------------------------------
    print("=" * 60)
    print("ISSUE 1: S6 function label audit")
    print("=" * 60)

    VALID_FUNCTIONS = {
        "Executive or Senior Leadership",
        "Information Technology (IT)",
        "Cloud Infrastructure and Platform Services",
        "Enterprise Architecture",
        "AI, Machine Learning & Data Science",
        "Business Intelligence & Analytics",
        "Software Engineering / Application Development",
        "Risk & Compliance",
        "Cybersecurity",
        "Innovation/R&D",
        "Operations",
        "Supply Chain & Logistics",
        "Marketing & Sales",
        "Finance",
        "Customer Support",
        "Project Management",
        "Strategy/Business Intelligence",
        "Product Development",
        "Procurement",
        "Human Resources",
        "Legal",
        "Other (please specify)",
    }

    all_func_values = []
    for r in data:
        all_func_values.extend(r["profile"].get("functions") or [])

    func_counter = Counter(all_func_values)
    invalid = {v for v in func_counter if v not in VALID_FUNCTIONS}
    affected = sum(1 for r in data if any(f not in VALID_FUNCTIONS for f in (r["profile"].get("functions") or [])))

    if invalid:
        print(f"INVALID labels found: {invalid}")
        print(f"Records affected: {affected}")
    else:
        print("All function labels are valid. No changes needed.")
        print(f"Distinct valid labels present: {len(func_counter)}")
        print(f"Total function tag occurrences: {len(all_func_values)}")

    # -----------------------------------------------------------------------
    # ISSUE 2: S8 unaided brand awareness → profile.unaided_brands
    # -----------------------------------------------------------------------
    print()
    print("=" * 60)
    print("ISSUE 2: S8 unaided brand awareness — import to profile")
    print("=" * 60)

    updated_s8 = 0
    brand_count_dist = Counter()
    all_normalized = []

    for r in data:
        ba = r.get("brand_awareness", {})
        raw_brands = [b.strip() for b in (ba.get("unaided_mentions_raw") or []) if b and b.strip()]

        # Store raw
        r["profile"]["unaided_brands_raw"] = raw_brands

        # Normalize
        normalized = [normalize_brand(b) for b in raw_brands]
        r["profile"]["unaided_brands"] = normalized

        # Also populate brand_awareness.unaided_mentions (was null)
        r["brand_awareness"]["unaided_mentions"] = normalized

        brand_count_dist[len(normalized)] += 1
        all_normalized.extend(normalized)
        updated_s8 += 1

    top20 = Counter(all_normalized).most_common(20)

    print(f"Records updated: {updated_s8}")
    print()
    print("Distribution of brands mentioned per respondent:")
    for k in sorted(brand_count_dist):
        print(f"  {k} brand(s): {brand_count_dist[k]} respondents")
    print()
    print("Top 20 brands after normalization:")
    for rank, (brand, cnt) in enumerate(top20, 1):
        print(f"  {rank:2d}. {brand}: {cnt}")

    # -----------------------------------------------------------------------
    # ISSUE 3: S9 aided familiarity → profile.brand_familiarity
    # -----------------------------------------------------------------------
    print()
    print("=" * 60)
    print("ISSUE 3: S9 aided brand familiarity — add profile.brand_familiarity")
    print("=" * 60)

    REAL_BRANDS_ORDER = [
        "Cognizant", "Accenture", "IBM Consulting", "Infosys", "Capgemini",
        "Wipro", "Tata Consultancy Services (TCS)", "EY", "HCL Technologies",
        "Deloitte", "McKinsey & Company", "Google (Cloud & Gemini)",
        "DXC Technology", "ServiceNow", "Microsoft (Azure & Copilot)",
        "Amazon Web Services (AWS)",
    ]
    FICTITIOUS_BRAND = "Supercalifragilisticexpialidocious Incorporated"
    ALL_BRANDS = REAL_BRANDS_ORDER + [FICTITIOUS_BRAND]

    CODE_LABELS = {
        1: "Currently using",
        2: "Have used in the past",
        3: "Currently considering using",
        4: "Familiar with their offerings but never used",
        5: "Heard the name only",
        6: "Never heard of",
    }

    updated_s9 = 0
    brand_dist = {b: Counter() for b in ALL_BRANDS}

    for r in data:
        aided = r.get("brand_awareness", {}).get("aided_familiarity") or []
        # Build lookup by brand name
        aided_lookup = {entry["brand"]: entry for entry in aided}

        brand_familiarity = []
        for brand in ALL_BRANDS:
            entry = aided_lookup.get(brand)
            if entry:
                code = entry.get("code")
                label = entry.get("label") or CODE_LABELS.get(code)
                brand_familiarity.append({
                    "brand": brand,
                    "code": code,
                    "label": label,
                })
                if code is not None:
                    brand_dist[brand][code] += 1
            else:
                # Brand not shown or missing — treat as never heard of
                brand_familiarity.append({
                    "brand": brand,
                    "code": None,
                    "label": None,
                })

        r["profile"]["brand_familiarity"] = brand_familiarity
        updated_s9 += 1

    print(f"Records updated: {updated_s9}")
    print()
    print("Brand familiarity distribution (counts at each code 1–6):")
    header = f"{'Brand':<48} {'c1':>5} {'c2':>5} {'c3':>5} {'c4':>5} {'c5':>5} {'c6':>5}"
    print(header)
    print("-" * len(header))
    for brand in ALL_BRANDS:
        dist = brand_dist[brand]
        row = f"{brand:<48}"
        for c in range(1, 7):
            row += f" {dist.get(c, 0):>5}"
        fictitious_note = " ← CONTROL" if brand == FICTITIOUS_BRAND else ""
        print(row + fictitious_note)

    # -----------------------------------------------------------------------
    # ISSUE 4: profile.job_title — audit
    # -----------------------------------------------------------------------
    print()
    print("=" * 60)
    print("ISSUE 4: profile.job_title — audit")
    print("=" * 60)

    non_null_jt = [r for r in data if r["profile"].get("job_title") is not None]
    null_jt = [r for r in data if r["profile"].get("job_title") is None]
    pct_non_null = len(non_null_jt) / len(data) * 100

    print(f"Non-null job_title: {len(non_null_jt)} ({pct_non_null:.1f}%)")
    print(f"Null job_title: {len(null_jt)} ({100 - pct_non_null:.1f}%)")
    print()

    if pct_non_null < 10:
        # Remove the field
        removed_jt = 0
        for r in data:
            if "job_title" in r["profile"]:
                del r["profile"]["job_title"]
                removed_jt += 1
        print(f"Field removed from {removed_jt} documents (below 10% threshold).")
    else:
        # Report sample values — keep field
        samples = [r["profile"]["job_title"] for r in non_null_jt[:10]]
        print(f"Field retained ({pct_non_null:.1f}% non-null — above 10% threshold).")
        print("Sample values:")
        for v in samples:
            print(f"  {repr(v)}")
        print()
        print("Note: This field maps to Q51 ('What is your job title?') in the survey instrument.")

    # -----------------------------------------------------------------------
    # ISSUE 5: responses.ai_budget_planned — audit and document
    # -----------------------------------------------------------------------
    print()
    print("=" * 60)
    print("ISSUE 5: responses.ai_budget_planned — audit")
    print("=" * 60)

    vals = [r["responses"].get("ai_budget_planned") for r in data if r["responses"].get("ai_budget_planned") is not None]
    nums = [v for v in vals if isinstance(v, (int, float))]

    print(f"Non-null count: {len(nums)}")
    print(f"Min: {min(nums):,}  Max: {max(nums):,}  Mean: {statistics.mean(nums):,.1f}  Median: {statistics.median(nums):,.0f}")
    print()
    print("Histogram (value ranges):")
    ranges = [(0, 1000), (1000, 5000), (5000, 10000), (10000, 50000), (50000, 200000)]
    for lo, hi in ranges:
        cnt = sum(1 for v in nums if lo <= v < hi)
        print(f"  [{lo:>6,} – {hi:>7,}): {cnt}")

    print()
    print("Cross-reference: ai_budget_planned vs Q41 (budget growth band)")
    q41_vs_budget = Counter()
    for r in data:
        bp = r["responses"].get("ai_budget_planned")
        q41 = r["responses"].get("q41")
        if q41 and isinstance(q41, dict):
            label = q41.get("label", "?")
            q41_vs_budget[label] += 1
    for label, cnt in q41_vs_budget.most_common():
        print(f"  {label}: {cnt}")

    print()
    print("FINDING: ai_budget_planned is MISLABELED.")
    print("  This field actually maps to Q47 ('Please provide your best estimate of")
    print("  how many employees your organization has across all locations globally.').")
    print("  Values (1,000–180,000) represent employee headcount, not budget.")
    print("  Recommend: rename field to 'employee_count_self_reported' and add to profile.")
    print()

    # Perform the fix: rename to correct name and move to profile
    renamed_count = 0
    for r in data:
        if "ai_budget_planned" in r["responses"]:
            val = r["responses"].pop("ai_budget_planned")
            r["profile"]["employee_count_self_reported"] = val
            renamed_count += 1

    print(f"FIXED: Moved 'ai_budget_planned' → 'profile.employee_count_self_reported' on {renamed_count} records.")

    # -----------------------------------------------------------------------
    # ISSUE 6: responses.q52 — identify and document
    # -----------------------------------------------------------------------
    print()
    print("=" * 60)
    print("ISSUE 6: responses.q52 — identify and document")
    print("=" * 60)

    q52_code_dist = Counter()
    for r in data:
        q52 = r["responses"].get("q52")
        if isinstance(q52, dict):
            q52_code_dist[q52.get("code")] += 1

    print("Distinct q52 code values and counts:")
    for code, cnt in sorted(q52_code_dist.items(), key=lambda x: (x[0] is None, x[0])):
        label = {1: "High Budget High Rank", 2: "Low Budget High Rank",
                 3: "High Budget Low Rank", 4: "Low Budget Low Rank"}.get(code, "None/Unassigned")
        print(f"  code={code} ({label}): {cnt}")

    print()
    samples = [(r["_id"], r["responses"]["q52"]) for r in data if isinstance(r["responses"].get("q52"), dict)][:10]
    print("Sample 10 records:")
    for rid, v in samples:
        print(f"  {rid}: code={v.get('code')}, label={repr(v.get('label'))}")

    print()
    print("FINDING: q52 is a computed respondent segmentation variable (Q52 = 'Segment').")
    print("  It cross-classifies respondents by AI budget level (High/Low) and brand")
    print("  familiarity/ranking (High/Low Rank). This is an analytical derived field,")
    print("  not an unanswered question. It should be retained but renamed.")
    print()

    # Rename to 'respondent_segment'
    renamed_q52 = 0
    for r in data:
        if "q52" in r["responses"]:
            r["responses"]["respondent_segment"] = r["responses"].pop("q52")
            renamed_q52 += 1

    print(f"FIXED: Renamed 'responses.q52' → 'responses.respondent_segment' on {renamed_q52} records.")

    # -----------------------------------------------------------------------
    # Final validation
    # -----------------------------------------------------------------------
    print()
    print("=" * 60)
    print("FINAL VALIDATION")
    print("=" * 60)
    print(f"Total records in file: {len(data)}")
    assert len(data) == 600, "Record count mismatch!"

    # Verify all records have expected new fields
    with_unaided = sum(1 for r in data if "unaided_brands" in r["profile"])
    with_unaided_raw = sum(1 for r in data if "unaided_brands_raw" in r["profile"])
    with_brand_fam = sum(1 for r in data if "brand_familiarity" in r["profile"])
    with_emp = sum(1 for r in data if "employee_count_self_reported" in r["profile"])
    with_segment = sum(1 for r in data if "respondent_segment" in r["responses"])
    remaining_q52 = sum(1 for r in data if "q52" in r["responses"])
    remaining_budget_planned = sum(1 for r in data if "ai_budget_planned" in r["responses"])

    print(f"profile.unaided_brands populated: {with_unaided}/600")
    print(f"profile.unaided_brands_raw populated: {with_unaided_raw}/600")
    print(f"profile.brand_familiarity populated: {with_brand_fam}/600")
    print(f"profile.employee_count_self_reported populated: {with_emp}/600")
    print(f"responses.respondent_segment populated: {with_segment}/600")
    print(f"responses.q52 remaining (should be 0): {remaining_q52}")
    print(f"responses.ai_budget_planned remaining (should be 0): {remaining_budget_planned}")

    # Write updated file
    with open(RESPONDENTS_PATH, "w") as f:
        json.dump(data, f, indent=2)
    print()
    print("Updated data written to", RESPONDENTS_PATH)


if __name__ == "__main__":
    main()
