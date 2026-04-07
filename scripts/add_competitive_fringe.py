#!/usr/bin/env python3
"""
Add brand_awareness.competitive_fringe to all 600 records.
Source: profile.unaided_brands_raw (untouched by this script).
"""

import json
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

NOISE = {
    "magneto", "byte technolap", "gerans", "athena idx", "drll", "office",
    "ntiva", "etq", "supplyrisk", "axon", "convergeone", "pilot",
}

# Competitive fringe map: lowercase-stripped input → canonical name
FRINGE_MAP = {
    # Oracle
    "oracle":                       "Oracle",
    "oracle cloud":                 "Oracle",
    "oracle cloud infrastructure":  "Oracle",
    # Salesforce
    "salesforce":                   "Salesforce",
    "salesforce.com":               "Salesforce",
    # Cisco
    "cisco":                        "Cisco",
    "cisco systems":                "Cisco",
    # SAP
    "sap":                          "SAP",
    "sap se":                       "SAP",
    # Dell
    "dell":                         "Dell Technologies",
    "dell technologies":            "Dell Technologies",
    # PwC
    "pwc":                          "PwC",
    "pricewaterhousecoopers":       "PwC",
    "pwc digital services":         "PwC",
    # KPMG
    "kpmg":                         "KPMG",
    # NVIDIA
    "nvidia":                       "NVIDIA",
    # Adobe
    "adobe":                        "Adobe",
    # Apple
    "apple":                        "Apple",
    "apple inc":                    "Apple",
    # Fujitsu
    "fujitsu":                      "Fujitsu",
    # HP/HPE
    "hp":                           "HP/HPE",
    "hpe":                          "HP/HPE",
    "hewlett packard":              "HP/HPE",
    "hewlett packard enterprise":   "HP/HPE",
    # Siemens
    "siemens":                      "Siemens",
    # Kyndryl
    "kyndryl":                      "Kyndryl",
    "kyndryl holdings ltd":         "Kyndryl",
    # Workday
    "workday":                      "Workday",
    # Alibaba Cloud
    "alibaba cloud":                "Alibaba Cloud",
    "alibaba":                      "Alibaba Cloud",
    # Rackspace
    "rackspace":                    "Rackspace Technology",
    "rackspace technology":         "Rackspace Technology",
    # VMware
    "vmware":                       "VMware",
    # Thoughtworks
    "thoughtworks":                 "Thoughtworks",
    # EPAM
    "epam":                         "EPAM Systems",
    "epam systems":                 "EPAM Systems",
    # AT&T
    "at&t":                         "AT&T",
    "att":                          "AT&T",
    # Meta
    "meta":                         "Meta",
    "meta platforms":               "Meta",
    # UST
    "ust":                          "UST",
}

# Lowercase raw → canonical study brand, for recognising un-normalised study
# brand strings that appear in unaided_brands_raw (e.g. "IBM", "AWS", "ibm").
STUDY_RAW_MAP = {
    # IBM
    "ibm": "IBM Consulting", "ibm consulting": "IBM Consulting",
    "ibm global services": "IBM Consulting", "ibm<": "IBM Consulting", "bm": "IBM Consulting",
    # Accenture
    "accenture": "Accenture", "accenture inc": "Accenture",
    "ccenture": "Accenture", "accentuee": "Accenture",
    # Microsoft
    "microsoft": "Microsoft (Azure & Copilot)", "microsoft azure": "Microsoft (Azure & Copilot)",
    "azure": "Microsoft (Azure & Copilot)", "microsoft cloud": "Microsoft (Azure & Copilot)",
    "icrosoft": "Microsoft (Azure & Copilot)", "smicrosoft": "Microsoft (Azure & Copilot)",
    "microsoft/azure & copilot": "Microsoft (Azure & Copilot)", "mucrisoft": "Microsoft (Azure & Copilot)",
    # AWS / Amazon
    "aws": "Amazon Web Services (AWS)", "amazon": "Amazon Web Services (AWS)",
    "amazon web services": "Amazon Web Services (AWS)",
    "amazon web service": "Amazon Web Services (AWS)",
    "amazon web services (aws)": "Amazon Web Services (AWS)",
    # Google
    "google": "Google (Cloud & Gemini)", "google cloud": "Google (Cloud & Gemini)",
    "goigle": "Google (Cloud & Gemini)", "goggle": "Google (Cloud & Gemini)",
    "goolge": "Google (Cloud & Gemini)", "google gemini": "Google (Cloud & Gemini)",
    # Deloitte
    "deloitte": "Deloitte", "deolitte": "Deloitte", "delottie": "Deloitte",
    "deloite": "Deloitte", "deloitte, openly": "Deloitte", "deloitte digital": "Deloitte",
    # Infosys
    "infosys": "Infosys", "inofsys": "Infosys", "infosys ltd": "Infosys",
    # Cognizant
    "cognizant": "Cognizant", "cognizant technology": "Cognizant",
    # Wipro
    "wipro": "Wipro", "wipro ltd": "Wipro",
    # Capgemini
    "capgemini": "Capgemini", "capgemini se": "Capgemini",
    # TCS
    "tcs": "Tata Consultancy Services (TCS)", "tata": "Tata Consultancy Services (TCS)",
    "tata consulting": "Tata Consultancy Services (TCS)",
    "tata consultancy": "Tata Consultancy Services (TCS)",
    "tata consultancy services (tcs)": "Tata Consultancy Services (TCS)",
    # EY
    "ey": "EY", "ey consulting": "EY", "ernst & young": "EY", "ernst and young": "EY",
    # HCL
    "hcl technologies": "HCL Technologies", "hcl": "HCL Technologies",
    "hcltech": "HCL Technologies", "hcl tech": "HCL Technologies",
    # McKinsey
    "mckinsey & company": "McKinsey & Company", "mckinsey": "McKinsey & Company",
    "mckinsey and company": "McKinsey & Company",
    # DXC
    "dxc technology": "DXC Technology", "dxc": "DXC Technology", "dtx": "DXC Technology",
    # ServiceNow
    "servicenow": "ServiceNow", "service now": "ServiceNow",
}


def classify_raw(s: str):
    """
    Return (canonical, kind) where kind is 'study', 'fringe', or 'noise'/'unknown'.
    """
    key = s.strip().lower()

    # Noise list
    if key in NOISE:
        return None, "noise"

    # Study brand (already canonical or maps via STUDY_RAW_MAP)
    if s.strip() in STUDY_BRANDS_16:
        return s.strip(), "study"
    if key in STUDY_RAW_MAP:
        return STUDY_RAW_MAP[key], "study"

    # Competitive fringe
    if key in FRINGE_MAP:
        return FRINGE_MAP[key], "fringe"

    return None, "unknown"


def main():
    with open(RESPONDENTS_PATH) as f:
        data = json.load(f)
    assert len(data) == N

    # Snapshot of raw field before any writes (for integrity check)
    raw_snapshot = {r["_id"]: list(r["profile"].get("unaided_brands_raw") or [])
                    for r in data}

    records_with_fringe = 0
    fringe_freq = Counter()
    field_added = 0

    for r in data:
        raw_brands = r["profile"].get("unaided_brands_raw") or []
        fringe = []
        for b in raw_brands:
            if not b or not b.strip():
                continue
            canonical, kind = classify_raw(b.strip())
            if kind == "fringe":
                fringe.append(canonical)
                fringe_freq[canonical] += 1

        r["brand_awareness"]["competitive_fringe"] = fringe
        field_added += 1
        if fringe:
            records_with_fringe += 1

    # Verify unaided_brands_raw is untouched
    raw_intact = all(
        r["profile"].get("unaided_brands_raw") == raw_snapshot[r["_id"]]
        for r in data
    )

    # -----------------------------------------------------------------------
    # Report
    # -----------------------------------------------------------------------
    print("=" * 60)
    print("COMPETITIVE FRINGE — RESULTS")
    print("=" * 60)
    print(f"brand_awareness.competitive_fringe added to: {field_added}/600")
    print(f"Records with ≥1 fringe mention:              {records_with_fringe}")
    print(f"Records with empty []:                       {N - records_with_fringe}")
    print(f"profile.unaided_brands_raw untouched:        {raw_intact}")

    print()
    print("Fringe brand frequency table (respondent mentions, sorted descending):")
    print(f"  {'Brand':<30} {'Mentions':>8}")
    print(f"  {'-'*40}")
    for brand, cnt in fringe_freq.most_common():
        print(f"  {brand:<30} {cnt:>8}")
    print(f"  {'-'*40}")
    print(f"  {'TOTAL':<30} {sum(fringe_freq.values()):>8}")

    with open(RESPONDENTS_PATH, "w") as f:
        json.dump(data, f, indent=2)
    print()
    print(f"All {len(data)} records intact. Written to {RESPONDENTS_PATH}")


if __name__ == "__main__":
    main()
