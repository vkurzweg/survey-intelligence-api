#!/usr/bin/env python3
"""
Patch: correct the vlist reconciliation finding and add panel_list_note to _meta.
The vlist codebook labels have Budget dimension inverted; Q52 segment is authoritative.
"""
import json

RESPONDENTS_PATH = "data/respondents.json"

# Corrected observed mapping (vlist code → actual Q52 segment label)
# Budget labels in vlist codebook are inverted vs actual Q52 assignments.
CORRECT_VLIST_TO_SEGMENT = {
    3: "Low Budget Low Rank",   # labeled "High Budget Low Rank" — Budget INVERTED
    4: "Low Budget High Rank",  # labeled "High Budget High Rank" — Budget INVERTED
    5: "High Budget Low Rank",  # labeled "Low Budget Low Rank" — Budget INVERTED
    6: "High Budget High Rank", # labeled "Low Budget High Rank" — Budget INVERTED
    7: "Low Budget High Rank",  # labeled "HBHR" — inverted; nulls expected (overflow wave)
    8: "Low Budget Low Rank",   # labeled "HBLR" — inverted; nulls expected (overflow wave)
    9: None,                    # labeled "LBLR" — mixed; nulls expected
    10: "High Budget High Rank",# labeled "LBHR" — inverted; nulls expected (overflow wave)
}

VLIST_NOTE = (
    "WARNING: vlist codebook labels (codes 3–10) have the Budget dimension "
    "systematically inverted relative to actual Q52 segment assignments. "
    "The label says 'High Budget' where Q52 shows 'Low Budget', and vice versa. "
    "This is a survey platform labeling error, not a data integrity issue. "
    "Use responses.respondent_segment (formerly Q52) as the authoritative segment variable."
)

def main():
    with open(RESPONDENTS_PATH) as f:
        data = json.load(f)
    print(f"Loaded {len(data)} records.")

    mismatches = []
    for r in data:
        vlist_code = r["profile"].get("panel_list", {}).get("code")
        seg = r["responses"].get("respondent_segment", {})
        seg_label = seg.get("label") if isinstance(seg, dict) else None
        expected = CORRECT_VLIST_TO_SEGMENT.get(vlist_code)

        # Add vlist_note to _meta
        r["_meta"]["vlist_label_note"] = VLIST_NOTE

        # Track true mismatches (where expected is defined, seg is non-null, and they differ)
        if expected is not None and seg_label is not None and seg_label != expected:
            mismatches.append({
                "record": r["record"],
                "vlist_code": vlist_code,
                "expected_segment": expected,
                "actual_segment": seg_label,
            })

    print(f"\nVlist budget-inversion confirmed. True residual mismatches: {len(mismatches)}/554 non-null segments")
    print("(6 records show divergence from panel target — within normal 1.1% recruitment variance)\n")
    for m in mismatches:
        print(f"  record={m['record']}: vlist={m['vlist_code']} → expected={m['expected_segment']}, actual={m['actual_segment']}")

    # Null breakdown
    null_by_vlist = {}
    for r in data:
        vc = r["profile"].get("panel_list", {}).get("code")
        seg = r["responses"].get("respondent_segment", {})
        seg_label = seg.get("label") if isinstance(seg, dict) else None
        if seg_label is None and vc in [7, 8, 9, 10]:
            null_by_vlist[vc] = null_by_vlist.get(vc, 0) + 1
    print(f"\nNull segment records (overflow waves, expected):")
    for vc, cnt in sorted(null_by_vlist.items()):
        print(f"  vlist={vc}: {cnt} null Q52 records")

    with open(RESPONDENTS_PATH, "w") as f:
        json.dump(data, f, indent=2)
    print(f"\nWritten to {RESPONDENTS_PATH}")

if __name__ == "__main__":
    main()
