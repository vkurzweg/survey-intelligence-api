#!/usr/bin/env python3
"""
Batch 2: Cross-tabulation queries B2-01 through B2-20.
Output: ~/avasta_batch2_crosstabs.json
"""

import json
import os
import statistics
from collections import Counter, defaultdict

RESPONDENTS_PATH = "data/respondents.json"
OUTPUT_PATH = os.path.expanduser("~/avasta_batch2_crosstabs.json")
N = 600

STUDY_BRANDS_16 = {
    "Cognizant", "Accenture", "IBM Consulting", "Infosys", "Capgemini",
    "Wipro", "Tata Consultancy Services (TCS)", "EY", "HCL Technologies",
    "Deloitte", "McKinsey & Company", "Google (Cloud & Gemini)",
    "DXC Technology", "ServiceNow", "Microsoft (Azure & Copilot)",
    "Amazon Web Services (AWS)",
}

# Industry threshold for cross-tab inclusion
IND_MIN_N = 15

# Q43 capability gap score: code → score
Q43_SCORE = {1: 1.0, 2: 0.75, 3: 0.50, 4: 0.25, 5: 0.0}

# Q7 direction score: normalized label → score
DIR_SCORE_MAP = {
    "decrease significantly": 1,
    "decrease somewhat":      2,
    "stay the same":          3,
    "increase somewhat":      4,
    "increase significantly": 5,
}

# Q45 vendor count midpoint
Q45_MIDPOINT = {"1": 1.0, "2-3": 2.5, "4-6": 5.0, "7-10": 8.5, "10+": 12.0}


def pct(n, base):
    if base == 0:
        return None
    return round(n / base * 100, 1)


def normalize_label(s):
    return s.replace("\xa0", " ").strip() if s else ""


def mean_score(scores):
    if not scores:
        return None
    return round(statistics.mean(scores), 3)


def median_spend(values):
    if not values:
        return None
    return round(statistics.median(values), 0)


def mean_spend(values):
    if not values:
        return None
    return round(statistics.mean(values), 0)


# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------
with open(RESPONDENTS_PATH) as f:
    data = json.load(f)
assert len(data) == N

# Precompute industry groups (for cross-tabs with n≥15 threshold)
ind_groups = defaultdict(list)
for r in data:
    ind = r["profile"].get("industry")
    if ind and ind.get("label"):
        ind_groups[ind["label"]].append(r)

QUALIFYING_INDUSTRIES = {k: v for k, v in ind_groups.items() if len(v) >= IND_MIN_N}
ALL_INDUSTRIES_SORTED = sorted(ind_groups.items(), key=lambda x: -len(x[1]))

output = {}


# ===========================================================================
# B2-01: Q7 AI priority direction — full distribution (all respondents)
#        For each of the 3 priorities: % by direction code, mean direction score
# ===========================================================================
def b2_01():
    result = {"query": "B2-01", "title": "Q7 AI Priority Direction — Full Distribution", "base_n": N}
    priorities_order = [
        "Increasing productivity",
        "Enabling AI scaling",
        "Enabling agentic business processes, workflows and functions",
    ]
    dir_code_order = [
        ("Decrease significantly", 1),
        ("Decrease somewhat", 2),
        ("Stay the same", 3),
        ("Increase somewhat", 4),
        ("Increase significantly", 5),
    ]
    priority_data = {}
    for priority in priorities_order:
        code_counts = Counter()
        scores = []
        for r in data:
            for item in (r["responses"].get("ai_priority_direction") or []):
                if item.get("priority") == priority:
                    code = item.get("code")
                    label = normalize_label(item.get("label", ""))
                    code_counts[code] += 1
                    score = DIR_SCORE_MAP.get(label.lower())
                    if score:
                        scores.append(score)
        n_resp = sum(code_counts.values())
        priority_data[priority] = {
            "n": n_resp,
            "distribution": [
                {
                    "label": lbl,
                    "code": c,
                    "count": code_counts.get(c, 0),
                    "pct": pct(code_counts.get(c, 0), n_resp),
                }
                for lbl, c in dir_code_order
            ],
            "mean_direction_score": mean_score(scores),
            "score_scale_note": "1=Decrease significantly … 5=Increase significantly",
        }
    result["priorities"] = priority_data
    return result


# ===========================================================================
# B2-02: Q7 AI priority direction — by qualifying industry (n≥15)
#        Mean direction score per priority × industry
# ===========================================================================
def b2_02():
    result = {
        "query": "B2-02",
        "title": "Q7 AI Priority Direction — Mean Score by Industry (n≥15)",
        "base_n": N,
        "industry_min_n": IND_MIN_N,
    }
    priorities_order = [
        "Increasing productivity",
        "Enabling AI scaling",
        "Enabling agentic business processes, workflows and functions",
    ]
    industries_out = []
    for ind_label, ind_recs in sorted(QUALIFYING_INDUSTRIES.items(), key=lambda x: -len(x[1])):
        n_ind = len(ind_recs)
        priority_scores = {}
        for priority in priorities_order:
            scores = []
            for r in ind_recs:
                for item in (r["responses"].get("ai_priority_direction") or []):
                    if item.get("priority") == priority:
                        lbl = normalize_label(item.get("label", "")).lower()
                        score = DIR_SCORE_MAP.get(lbl)
                        if score:
                            scores.append(score)
            priority_scores[priority] = mean_score(scores)
        industries_out.append({
            "industry": ind_label,
            "n": n_ind,
            "mean_direction_scores": priority_scores,
        })
    result["industries"] = industries_out
    result["excluded_industries"] = [
        {"industry": k, "n": len(v)} for k, v in ALL_INDUSTRIES_SORTED if len(v) < IND_MIN_N
    ]
    return result


# ===========================================================================
# B2-03: Q10 AI investment plans — full distribution
# ===========================================================================
def b2_03():
    result = {"query": "B2-03", "title": "Q10 AI Investment Plans — Full Distribution", "base_n": N}
    code_order = [1, 2, 3, 4]
    labels_map = {}
    code_counts = Counter()
    for r in data:
        q10 = r["responses"].get("q10")
        if q10 and q10.get("code") is not None:
            c = q10["code"]
            code_counts[c] += 1
            labels_map[c] = q10.get("label", "")
    n_resp = sum(code_counts.values())
    result["n_valid"] = n_resp
    result["distribution"] = [
        {
            "code": c,
            "label": labels_map.get(c, ""),
            "count": code_counts.get(c, 0),
            "pct": pct(code_counts.get(c, 0), n_resp),
        }
        for c in sorted(code_counts.keys())
    ]
    return result


# ===========================================================================
# B2-04: Q10 AI investment plans — by qualifying industry (n≥15)
#        % per code × industry
# ===========================================================================
def b2_04():
    result = {
        "query": "B2-04",
        "title": "Q10 AI Investment Plans — Distribution by Industry (n≥15)",
        "base_n": N,
        "industry_min_n": IND_MIN_N,
    }
    # Get all codes/labels first
    labels_map = {}
    for r in data:
        q10 = r["responses"].get("q10")
        if q10 and q10.get("code") is not None:
            labels_map[q10["code"]] = q10.get("label", "")
    codes_sorted = sorted(labels_map.keys())

    industries_out = []
    for ind_label, ind_recs in sorted(QUALIFYING_INDUSTRIES.items(), key=lambda x: -len(x[1])):
        n_ind = len(ind_recs)
        code_counts = Counter()
        for r in ind_recs:
            q10 = r["responses"].get("q10")
            if q10 and q10.get("code") is not None:
                code_counts[q10["code"]] += 1
        n_valid = sum(code_counts.values())
        industries_out.append({
            "industry": ind_label,
            "n": n_ind,
            "n_valid": n_valid,
            "distribution": [
                {
                    "code": c,
                    "label": labels_map.get(c, ""),
                    "count": code_counts.get(c, 0),
                    "pct": pct(code_counts.get(c, 0), n_valid),
                }
                for c in codes_sorted
            ],
        })
    result["industries"] = industries_out
    result["excluded_industries"] = [
        {"industry": k, "n": len(v)} for k, v in ALL_INDUSTRIES_SORTED if len(v) < IND_MIN_N
    ]
    return result


# ===========================================================================
# B2-05: Q38 Dedicated AI budget — full distribution
# ===========================================================================
def b2_05():
    result = {"query": "B2-05", "title": "Q38 Dedicated AI Budget — Full Distribution", "base_n": N}
    labels_map = {}
    code_counts = Counter()
    for r in data:
        q38 = r["responses"].get("q38")
        if q38 and q38.get("code") is not None:
            c = q38["code"]
            code_counts[c] += 1
            labels_map[c] = q38.get("label", "")
    n_valid = sum(code_counts.values())
    result["n_valid"] = n_valid
    result["distribution"] = [
        {
            "code": c,
            "label": labels_map.get(c, ""),
            "count": code_counts.get(c, 0),
            "pct": pct(code_counts.get(c, 0), n_valid),
        }
        for c in sorted(code_counts.keys())
    ]
    return result


# ===========================================================================
# B2-06: Q38 Dedicated AI budget — by qualifying industry (n≥15)
# ===========================================================================
def b2_06():
    result = {
        "query": "B2-06",
        "title": "Q38 Dedicated AI Budget — Distribution by Industry (n≥15)",
        "base_n": N,
        "industry_min_n": IND_MIN_N,
    }
    labels_map = {}
    for r in data:
        q38 = r["responses"].get("q38")
        if q38 and q38.get("code") is not None:
            labels_map[q38["code"]] = q38.get("label", "")
    codes_sorted = sorted(labels_map.keys())

    industries_out = []
    for ind_label, ind_recs in sorted(QUALIFYING_INDUSTRIES.items(), key=lambda x: -len(x[1])):
        n_ind = len(ind_recs)
        code_counts = Counter()
        for r in ind_recs:
            q38 = r["responses"].get("q38")
            if q38 and q38.get("code") is not None:
                code_counts[q38["code"]] += 1
        n_valid = sum(code_counts.values())
        industries_out.append({
            "industry": ind_label,
            "n": n_ind,
            "n_valid": n_valid,
            "distribution": [
                {
                    "code": c,
                    "label": labels_map.get(c, ""),
                    "count": code_counts.get(c, 0),
                    "pct": pct(code_counts.get(c, 0), n_valid),
                }
                for c in codes_sorted
            ],
        })
    result["industries"] = industries_out
    result["excluded_industries"] = [
        {"industry": k, "n": len(v)} for k, v in ALL_INDUSTRIES_SORTED if len(v) < IND_MIN_N
    ]
    return result


# ===========================================================================
# B2-07: Q42 AI market evolution views — full distribution (multi-select)
#        % of respondents selecting each option (base = respondents with any Q42)
# ===========================================================================
def b2_07():
    result = {"query": "B2-07", "title": "Q42 AI Market Evolution Views — Full Distribution (multi-select)", "base_n": N}
    val_counts = Counter()
    n_resp = 0
    for r in data:
        q42 = r["responses"].get("q42") or []
        if q42:
            n_resp += 1
            for v in q42:
                if v and v.strip():
                    val_counts[v.strip()] += 1
    result["n_with_any_selection"] = n_resp
    result["note"] = "Pct = % of respondents selecting each option (multiple selections allowed)"
    result["distribution"] = [
        {"label": lbl, "count": cnt, "pct": pct(cnt, n_resp)}
        for lbl, cnt in sorted(val_counts.items(), key=lambda x: -x[1])
    ]
    return result


# ===========================================================================
# B2-08: Q42 AI market evolution views — by qualifying industry (n≥15)
#        % per option × industry (base = respondents in industry with any Q42)
# ===========================================================================
def b2_08():
    result = {
        "query": "B2-08",
        "title": "Q42 AI Market Evolution Views — Distribution by Industry (n≥15) (multi-select)",
        "base_n": N,
        "industry_min_n": IND_MIN_N,
    }
    # Global option list
    all_options = sorted(
        {v.strip() for r in data for v in (r["responses"].get("q42") or []) if v and v.strip()},
        key=lambda x: -sum(
            1 for r in data if x in [v.strip() for v in (r["responses"].get("q42") or []) if v]
        ),
    )

    industries_out = []
    for ind_label, ind_recs in sorted(QUALIFYING_INDUSTRIES.items(), key=lambda x: -len(x[1])):
        n_ind = len(ind_recs)
        val_counts = Counter()
        n_valid = 0
        for r in ind_recs:
            q42 = r["responses"].get("q42") or []
            if q42:
                n_valid += 1
                for v in q42:
                    if v and v.strip():
                        val_counts[v.strip()] += 1
        industries_out.append({
            "industry": ind_label,
            "n": n_ind,
            "n_with_any_selection": n_valid,
            "distribution": [
                {"label": opt, "count": val_counts.get(opt, 0), "pct": pct(val_counts.get(opt, 0), n_valid)}
                for opt in all_options
            ],
        })
    result["industries"] = industries_out
    result["excluded_industries"] = [
        {"industry": k, "n": len(v)} for k, v in ALL_INDUSTRIES_SORTED if len(v) < IND_MIN_N
    ]
    return result


# ===========================================================================
# B2-09: Q44 AI disruption level — full distribution
# ===========================================================================
def b2_09():
    result = {"query": "B2-09", "title": "Q44 AI Disruption Level — Full Distribution", "base_n": N}
    labels_map = {}
    code_counts = Counter()
    for r in data:
        q44 = r["responses"].get("q44")
        if q44 and q44.get("code") is not None:
            c = q44["code"]
            code_counts[c] += 1
            labels_map[c] = q44.get("label", "")
    n_valid = sum(code_counts.values())
    result["n_valid"] = n_valid
    result["distribution"] = [
        {
            "code": c,
            "label": labels_map.get(c, ""),
            "count": code_counts.get(c, 0),
            "pct": pct(code_counts.get(c, 0), n_valid),
        }
        for c in sorted(code_counts.keys())
    ]
    return result


# ===========================================================================
# B2-10: Q44 AI disruption level — by qualifying industry (n≥15)
# ===========================================================================
def b2_10():
    result = {
        "query": "B2-10",
        "title": "Q44 AI Disruption Level — Distribution by Industry (n≥15)",
        "base_n": N,
        "industry_min_n": IND_MIN_N,
    }
    labels_map = {}
    for r in data:
        q44 = r["responses"].get("q44")
        if q44 and q44.get("code") is not None:
            labels_map[q44["code"]] = q44.get("label", "")
    codes_sorted = sorted(labels_map.keys())

    industries_out = []
    for ind_label, ind_recs in sorted(QUALIFYING_INDUSTRIES.items(), key=lambda x: -len(x[1])):
        n_ind = len(ind_recs)
        code_counts = Counter()
        for r in ind_recs:
            q44 = r["responses"].get("q44")
            if q44 and q44.get("code") is not None:
                code_counts[q44["code"]] += 1
        n_valid = sum(code_counts.values())
        industries_out.append({
            "industry": ind_label,
            "n": n_ind,
            "n_valid": n_valid,
            "distribution": [
                {
                    "code": c,
                    "label": labels_map.get(c, ""),
                    "count": code_counts.get(c, 0),
                    "pct": pct(code_counts.get(c, 0), n_valid),
                }
                for c in codes_sorted
            ],
        })
    result["industries"] = industries_out
    result["excluded_industries"] = [
        {"industry": k, "n": len(v)} for k, v in ALL_INDUSTRIES_SORTED if len(v) < IND_MIN_N
    ]
    return result


# ===========================================================================
# B2-11: Q45 # AI vendors considered — full distribution + mean vendor count
# ===========================================================================
def b2_11():
    result = {"query": "B2-11", "title": "Q45 Number of AI Vendors Considered — Full Distribution", "base_n": N}
    label_order = ["1", "2-3", "4-6", "7-10", "10+"]
    labels_map = {}
    code_to_label = {}
    code_counts = Counter()
    midpoints = []
    for r in data:
        q45 = r["responses"].get("q45")
        if q45 and q45.get("code") is not None:
            c = q45["code"]
            lbl = q45.get("label", "")
            code_counts[c] += 1
            code_to_label[c] = lbl
            mp = Q45_MIDPOINT.get(lbl)
            if mp is not None:
                midpoints.append(mp)
    n_valid = sum(code_counts.values())
    result["n_valid"] = n_valid
    result["distribution"] = [
        {
            "code": c,
            "label": code_to_label.get(c, ""),
            "count": code_counts.get(c, 0),
            "pct": pct(code_counts.get(c, 0), n_valid),
        }
        for c in sorted(code_counts.keys())
    ]
    result["mean_vendor_count_midpoint"] = mean_score(midpoints)
    result["midpoint_note"] = "Midpoints: 1→1, 2-3→2.5, 4-6→5, 7-10→8.5, 10+→12"
    return result


# ===========================================================================
# B2-12: Q45 # AI vendors considered — by qualifying industry (n≥15)
#        % distribution + mean midpoint per industry
# ===========================================================================
def b2_12():
    result = {
        "query": "B2-12",
        "title": "Q45 Number of AI Vendors Considered — by Industry (n≥15)",
        "base_n": N,
        "industry_min_n": IND_MIN_N,
    }
    code_to_label = {}
    for r in data:
        q45 = r["responses"].get("q45")
        if q45 and q45.get("code") is not None:
            code_to_label[q45["code"]] = q45.get("label", "")
    codes_sorted = sorted(code_to_label.keys())

    industries_out = []
    for ind_label, ind_recs in sorted(QUALIFYING_INDUSTRIES.items(), key=lambda x: -len(x[1])):
        n_ind = len(ind_recs)
        code_counts = Counter()
        midpoints = []
        for r in ind_recs:
            q45 = r["responses"].get("q45")
            if q45 and q45.get("code") is not None:
                code_counts[q45["code"]] += 1
                lbl = q45.get("label", "")
                mp = Q45_MIDPOINT.get(lbl)
                if mp is not None:
                    midpoints.append(mp)
        n_valid = sum(code_counts.values())
        industries_out.append({
            "industry": ind_label,
            "n": n_ind,
            "n_valid": n_valid,
            "distribution": [
                {
                    "code": c,
                    "label": code_to_label.get(c, ""),
                    "count": code_counts.get(c, 0),
                    "pct": pct(code_counts.get(c, 0), n_valid),
                }
                for c in codes_sorted
            ],
            "mean_vendor_count_midpoint": mean_score(midpoints),
        })
    result["industries"] = industries_out
    result["excluded_industries"] = [
        {"industry": k, "n": len(v)} for k, v in ALL_INDUSTRIES_SORTED if len(v) < IND_MIN_N
    ]
    return result


# ===========================================================================
# B2-13: Employee count × Q43 capability gap
#        Mean gap score per emp_count segment
# ===========================================================================
def b2_13():
    result = {
        "query": "B2-13",
        "title": "Employee Count × Q43 Capability Gap Score",
        "base_n": N,
        "score_scale": "0=Very large gap … 1.0=No gap",
    }
    emp_labels_order = {}
    for r in data:
        ec = r["profile"].get("emp_count")
        if ec and ec.get("code") is not None:
            emp_labels_order[ec["code"]] = ec.get("label", "")

    emp_scores = defaultdict(list)
    emp_counts = Counter()
    for r in data:
        ec = r["profile"].get("emp_count")
        q43 = r["responses"].get("q43")
        if ec and ec.get("code") is not None and q43 and q43.get("code") is not None:
            emp_code = ec["code"]
            gap_score = Q43_SCORE.get(q43["code"])
            if gap_score is not None:
                emp_scores[emp_code].append(gap_score)
                emp_counts[emp_code] += 1

    rows = []
    for c in sorted(emp_labels_order.keys()):
        scores = emp_scores.get(c, [])
        rows.append({
            "emp_count_code": c,
            "emp_count_label": emp_labels_order.get(c, ""),
            "n": emp_counts.get(c, 0),
            "mean_gap_score": mean_score(scores),
        })
    result["rows"] = rows
    return result


# ===========================================================================
# B2-14: Revenue × Q43 capability gap
#        Mean gap score per revenue segment
# ===========================================================================
def b2_14():
    result = {
        "query": "B2-14",
        "title": "Revenue × Q43 Capability Gap Score",
        "base_n": N,
        "score_scale": "0=Very large gap … 1.0=No gap",
    }
    rev_labels = {}
    for r in data:
        rv = r["profile"].get("revenue")
        if rv and rv.get("code") is not None:
            rev_labels[rv["code"]] = rv.get("label", "")

    rev_scores = defaultdict(list)
    rev_counts = Counter()
    for r in data:
        rv = r["profile"].get("revenue")
        q43 = r["responses"].get("q43")
        if rv and rv.get("code") is not None and q43 and q43.get("code") is not None:
            rev_code = rv["code"]
            gap_score = Q43_SCORE.get(q43["code"])
            if gap_score is not None:
                rev_scores[rev_code].append(gap_score)
                rev_counts[rev_code] += 1

    rows = []
    for c in sorted(rev_labels.keys()):
        scores = rev_scores.get(c, [])
        rows.append({
            "revenue_code": c,
            "revenue_label": rev_labels.get(c, ""),
            "n": rev_counts.get(c, 0),
            "mean_gap_score": mean_score(scores),
        })
    result["rows"] = rows
    return result


# ===========================================================================
# B2-15: Employee count × AI spend (current)
#        Median and mean spend per emp_count segment; exclude 17 nulls
# ===========================================================================
def b2_15():
    result = {
        "query": "B2-15",
        "title": "Employee Count × AI Spend Current",
        "base_n": N,
        "note": "17 null ai_spend_current values excluded from spend stats",
    }
    emp_labels = {}
    for r in data:
        ec = r["profile"].get("emp_count")
        if ec and ec.get("code") is not None:
            emp_labels[ec["code"]] = ec.get("label", "")

    emp_spend = defaultdict(list)
    emp_n_total = Counter()
    emp_n_valid = Counter()
    for r in data:
        ec = r["profile"].get("emp_count")
        spend = r["responses"].get("ai_spend_current")
        if ec and ec.get("code") is not None:
            emp_code = ec["code"]
            emp_n_total[emp_code] += 1
            if spend is not None:
                emp_spend[emp_code].append(spend)
                emp_n_valid[emp_code] += 1

    rows = []
    for c in sorted(emp_labels.keys()):
        vals = emp_spend.get(c, [])
        rows.append({
            "emp_count_code": c,
            "emp_count_label": emp_labels.get(c, ""),
            "n_total": emp_n_total.get(c, 0),
            "n_valid_spend": emp_n_valid.get(c, 0),
            "median_spend": median_spend(vals),
            "mean_spend": mean_spend(vals),
        })
    result["rows"] = rows
    return result


# ===========================================================================
# B2-16: Revenue × AI spend (current)
#        Median and mean spend per revenue segment; exclude nulls
# ===========================================================================
def b2_16():
    result = {
        "query": "B2-16",
        "title": "Revenue × AI Spend Current",
        "base_n": N,
        "note": "17 null ai_spend_current values excluded from spend stats",
    }
    rev_labels = {}
    for r in data:
        rv = r["profile"].get("revenue")
        if rv and rv.get("code") is not None:
            rev_labels[rv["code"]] = rv.get("label", "")

    rev_spend = defaultdict(list)
    rev_n_total = Counter()
    rev_n_valid = Counter()
    for r in data:
        rv = r["profile"].get("revenue")
        spend = r["responses"].get("ai_spend_current")
        if rv and rv.get("code") is not None:
            rev_code = rv["code"]
            rev_n_total[rev_code] += 1
            if spend is not None:
                rev_spend[rev_code].append(spend)
                rev_n_valid[rev_code] += 1

    rows = []
    for c in sorted(rev_labels.keys()):
        vals = rev_spend.get(c, [])
        rows.append({
            "revenue_code": c,
            "revenue_label": rev_labels.get(c, ""),
            "n_total": rev_n_total.get(c, 0),
            "n_valid_spend": rev_n_valid.get(c, 0),
            "median_spend": median_spend(vals),
            "mean_spend": mean_spend(vals),
        })
    result["rows"] = rows
    return result


# ===========================================================================
# B2-17: AI adoption approach × Q43 capability gap
#        Distribution of gap codes + mean gap score per adoption approach
# ===========================================================================
def b2_17():
    result = {
        "query": "B2-17",
        "title": "AI Adoption Approach × Q43 Capability Gap",
        "base_n": N,
        "score_scale": "0=Very large gap … 1.0=No gap",
    }
    aap_labels = {}
    for r in data:
        aap = r["profile"].get("ai_adoption_approach")
        if aap and aap.get("code") is not None:
            aap_labels[aap["code"]] = aap.get("label", "")

    q43_labels = {}
    for r in data:
        q43 = r["responses"].get("q43")
        if q43 and q43.get("code") is not None:
            q43_labels[q43["code"]] = q43.get("label", "")

    aap_gap_counts = defaultdict(Counter)
    aap_scores = defaultdict(list)
    aap_n = Counter()
    for r in data:
        aap = r["profile"].get("ai_adoption_approach")
        q43 = r["responses"].get("q43")
        if aap and aap.get("code") is not None and q43 and q43.get("code") is not None:
            aap_code = aap["code"]
            q43_code = q43["code"]
            aap_n[aap_code] += 1
            aap_gap_counts[aap_code][q43_code] += 1
            gs = Q43_SCORE.get(q43_code)
            if gs is not None:
                aap_scores[aap_code].append(gs)

    rows = []
    for c in sorted(aap_labels.keys()):
        gap_dist = [
            {
                "gap_code": gc,
                "gap_label": q43_labels.get(gc, ""),
                "count": aap_gap_counts[c].get(gc, 0),
                "pct": pct(aap_gap_counts[c].get(gc, 0), aap_n.get(c, 0)),
            }
            for gc in sorted(q43_labels.keys())
        ]
        rows.append({
            "adoption_code": c,
            "adoption_label": aap_labels.get(c, ""),
            "n": aap_n.get(c, 0),
            "gap_distribution": gap_dist,
            "mean_gap_score": mean_score(aap_scores.get(c, [])),
        })
    result["rows"] = rows
    return result


# ===========================================================================
# B2-18: AI adoption approach × AI spend (current)
#        Median and mean spend per adoption approach; exclude nulls
# ===========================================================================
def b2_18():
    result = {
        "query": "B2-18",
        "title": "AI Adoption Approach × AI Spend Current",
        "base_n": N,
        "note": "17 null ai_spend_current values excluded from spend stats",
    }
    aap_labels = {}
    for r in data:
        aap = r["profile"].get("ai_adoption_approach")
        if aap and aap.get("code") is not None:
            aap_labels[aap["code"]] = aap.get("label", "")

    aap_spend = defaultdict(list)
    aap_n_total = Counter()
    aap_n_valid = Counter()
    for r in data:
        aap = r["profile"].get("ai_adoption_approach")
        spend = r["responses"].get("ai_spend_current")
        if aap and aap.get("code") is not None:
            aap_code = aap["code"]
            aap_n_total[aap_code] += 1
            if spend is not None:
                aap_spend[aap_code].append(spend)
                aap_n_valid[aap_code] += 1

    rows = []
    for c in sorted(aap_labels.keys()):
        vals = aap_spend.get(c, [])
        rows.append({
            "adoption_code": c,
            "adoption_label": aap_labels.get(c, ""),
            "n_total": aap_n_total.get(c, 0),
            "n_valid_spend": aap_n_valid.get(c, 0),
            "median_spend": median_spend(vals),
            "mean_spend": mean_spend(vals),
        })
    result["rows"] = rows
    return result


# ===========================================================================
# B2-19: Brand familiarity — retention/loyalty profile
#        For each of the 16 study brands:
#          currently_using, have_used_past, currently_considering, familiar_never_used,
#          heard_name_only, never_heard (pct of 600 per category)
#        Plus: repeat_loyalty = currently_using AND have_used_past (past→current)
#          consideration_funnel = (currently_using + currently_considering) / (aware)
# ===========================================================================
def b2_19():
    result = {
        "query": "B2-19",
        "title": "Brand Familiarity — Awareness and Engagement Profile (16 Study Brands)",
        "base_n": N,
        "note": "Fictitious control brand excluded. Pct of all 600 respondents.",
    }
    # Familiarity code map
    FAM_CODES = {
        1: "currently_using",
        2: "have_used_past",
        3: "currently_considering",
        4: "familiar_never_used",
        5: "heard_name_only",
        6: "never_heard",
    }

    brand_data = defaultdict(lambda: Counter())
    for r in data:
        for bf in r["profile"].get("brand_familiarity", []):
            brand = bf.get("brand")
            code = bf.get("code")
            if brand and brand in STUDY_BRANDS_16 and code is not None:
                brand_data[brand][code] += 1

    brands_out = []
    for brand in sorted(STUDY_BRANDS_16):
        counts = brand_data[brand]
        n_total = sum(counts.values())  # should be 600
        n_aware = n_total - counts.get(6, 0)  # exclude never_heard

        # Consideration funnel: (using + considering) / aware
        n_funnel_num = counts.get(1, 0) + counts.get(3, 0)
        consideration_funnel_pct = pct(n_funnel_num, n_aware) if n_aware > 0 else None

        brands_out.append({
            "brand": brand,
            "n_responses": n_total,
            "currently_using": {"count": counts.get(1, 0), "pct": pct(counts.get(1, 0), N)},
            "have_used_past": {"count": counts.get(2, 0), "pct": pct(counts.get(2, 0), N)},
            "currently_considering": {"count": counts.get(3, 0), "pct": pct(counts.get(3, 0), N)},
            "familiar_never_used": {"count": counts.get(4, 0), "pct": pct(counts.get(4, 0), N)},
            "heard_name_only": {"count": counts.get(5, 0), "pct": pct(counts.get(5, 0), N)},
            "never_heard": {"count": counts.get(6, 0), "pct": pct(counts.get(6, 0), N)},
            "n_aware": n_aware,
            "awareness_pct": pct(n_aware, N),
            "consideration_funnel_pct": consideration_funnel_pct,
            "consideration_funnel_note": "(currently_using + currently_considering) / aware",
        })

    # Sort by awareness desc
    brands_out.sort(key=lambda x: -x["awareness_pct"])
    result["brands"] = brands_out
    return result


# ===========================================================================
# B2-20: HQ location × Q43 capability gap + mean AI spend
#        Distribution of gap scores + mean spend per HQ location segment
# ===========================================================================
def b2_20():
    result = {
        "query": "B2-20",
        "title": "HQ Location × Q43 Capability Gap Score + AI Spend",
        "base_n": N,
        "gap_score_scale": "0=Very large gap … 1.0=No gap",
        "note": "17 null ai_spend_current values excluded from spend stats",
    }
    hq_labels = {}
    for r in data:
        hq = r["profile"].get("hq_location")
        if hq and hq.get("code") is not None:
            hq_labels[hq["code"]] = hq.get("label", "")

    q43_labels = {}
    for r in data:
        q43 = r["responses"].get("q43")
        if q43 and q43.get("code") is not None:
            q43_labels[q43["code"]] = q43.get("label", "")

    hq_gap_counts = defaultdict(Counter)
    hq_gap_scores = defaultdict(list)
    hq_spend = defaultdict(list)
    hq_n = Counter()
    hq_n_valid_spend = Counter()
    for r in data:
        hq = r["profile"].get("hq_location")
        q43 = r["responses"].get("q43")
        spend = r["responses"].get("ai_spend_current")
        if hq and hq.get("code") is not None:
            hq_code = hq["code"]
            hq_n[hq_code] += 1
            if q43 and q43.get("code") is not None:
                q43_code = q43["code"]
                hq_gap_counts[hq_code][q43_code] += 1
                gs = Q43_SCORE.get(q43_code)
                if gs is not None:
                    hq_gap_scores[hq_code].append(gs)
            if spend is not None:
                hq_spend[hq_code].append(spend)
                hq_n_valid_spend[hq_code] += 1

    rows = []
    for c in sorted(hq_labels.keys()):
        gap_dist = [
            {
                "gap_code": gc,
                "gap_label": q43_labels.get(gc, ""),
                "count": hq_gap_counts[c].get(gc, 0),
                "pct": pct(hq_gap_counts[c].get(gc, 0), hq_n.get(c, 0)),
            }
            for gc in sorted(q43_labels.keys())
        ]
        rows.append({
            "hq_code": c,
            "hq_label": hq_labels.get(c, ""),
            "n": hq_n.get(c, 0),
            "gap_distribution": gap_dist,
            "mean_gap_score": mean_score(hq_gap_scores.get(c, [])),
            "n_valid_spend": hq_n_valid_spend.get(c, 0),
            "median_spend": median_spend(hq_spend.get(c, [])),
            "mean_spend": mean_spend(hq_spend.get(c, [])),
        })
    result["rows"] = rows
    return result


# ===========================================================================
# Run all queries
# ===========================================================================
queries = [b2_01, b2_02, b2_03, b2_04, b2_05, b2_06, b2_07, b2_08,
           b2_09, b2_10, b2_11, b2_12, b2_13, b2_14, b2_15, b2_16,
           b2_17, b2_18, b2_19, b2_20]

for fn in queries:
    qid = fn.__name__.upper().replace("_", "-")
    print(f"\n{'='*70}")
    r = fn()
    output[r["query"]] = r
    print(f"{r['query']}: {r['title']}")

    # ---- Print summaries ----
    if r["query"] == "B2-01":
        for pname, pdata in r["priorities"].items():
            print(f"\n  Priority: {pname}")
            print(f"  Mean direction score: {pdata['mean_direction_score']}")
            for d in pdata["distribution"]:
                print(f"    [{d['code']}] {d['label']:<30} {d['count']:>4}  {d['pct']:>5}%")

    elif r["query"] == "B2-02":
        headers = ["Increasing productivity", "Enabling AI scaling",
                   "Enabling agentic business processes, workflows and functions"]
        abbrev = ["Productivity", "AI Scaling", "Agentic"]
        print(f"\n  {'Industry':<50} {'n':>4} " + " ".join(f"{a:>12}" for a in abbrev))
        print(f"  {'-'*90}")
        for row in r["industries"]:
            scores = [row["mean_direction_scores"].get(h) for h in headers]
            score_strs = [f"{s:>12.3f}" if s is not None else f"{'N/A':>12}" for s in scores]
            print(f"  {row['industry']:<50} {row['n']:>4} " + " ".join(score_strs))

    elif r["query"] in ("B2-03", "B2-05", "B2-09"):
        print(f"  n_valid: {r['n_valid']}")
        for d in r["distribution"]:
            print(f"    [{d['code']}] {d['label']:<65} {d['count']:>4}  {d['pct']:>5}%")

    elif r["query"] in ("B2-04", "B2-06", "B2-10"):
        # By industry — show compact summary
        print(f"  (Industry cross-tab — see JSON for full distribution)")
        for row in r["industries"]:
            print(f"    {row['industry']:<55} n={row['n']:>3} n_valid={row['n_valid']}")

    elif r["query"] == "B2-07":
        print(f"  n_with_any_selection: {r['n_with_any_selection']}")
        for d in r["distribution"]:
            print(f"    {d['label']:<55} {d['count']:>4}  {d['pct']:>5}%")

    elif r["query"] == "B2-08":
        print(f"  (Industry × multi-select — see JSON for full distribution)")
        for row in r["industries"]:
            print(f"    {row['industry']:<55} n={row['n']:>3} n_with_selections={row['n_with_any_selection']}")

    elif r["query"] == "B2-11":
        print(f"  n_valid: {r['n_valid']}  Mean vendor count (midpoint): {r['mean_vendor_count_midpoint']}")
        for d in r["distribution"]:
            print(f"    [{d['code']}] {d['label']:<12} {d['count']:>4}  {d['pct']:>5}%")

    elif r["query"] == "B2-12":
        print(f"  {'Industry':<50} {'n':>4} {'n_valid':>7} {'mean_midpoint':>13}")
        print(f"  {'-'*75}")
        for row in r["industries"]:
            mp = row["mean_vendor_count_midpoint"]
            print(f"  {row['industry']:<50} {row['n']:>4} {row['n_valid']:>7} {mp:>13.2f}" if mp else
                  f"  {row['industry']:<50} {row['n']:>4} {row['n_valid']:>7} {'N/A':>13}")

    elif r["query"] in ("B2-13", "B2-14"):
        lbl_key = "emp_count_label" if r["query"] == "B2-13" else "revenue_label"
        print(f"  {'Segment':<45} {'n':>4} {'mean_gap_score':>14}")
        print(f"  {'-'*65}")
        for row in r["rows"]:
            gs = row["mean_gap_score"]
            gs_str = f"{gs:.3f}" if gs is not None else "N/A"
            print(f"  {row[lbl_key]:<45} {row['n']:>4} {gs_str:>14}")

    elif r["query"] in ("B2-15", "B2-16"):
        lbl_key = "emp_count_label" if r["query"] == "B2-15" else "revenue_label"
        print(f"  {'Segment':<45} {'n':>4} {'n_valid':>7} {'median_$':>12} {'mean_$':>12}")
        print(f"  {'-'*82}")
        for row in r["rows"]:
            med = f"${row['median_spend']:,.0f}" if row['median_spend'] is not None else "N/A"
            mn = f"${row['mean_spend']:,.0f}" if row['mean_spend'] is not None else "N/A"
            print(f"  {row[lbl_key]:<45} {row['n_total']:>4} {row['n_valid_spend']:>7} {med:>12} {mn:>12}")

    elif r["query"] == "B2-17":
        print(f"  {'Adoption Approach':<55} {'n':>4} {'mean_gap':>9}")
        print(f"  {'-'*70}")
        for row in r["rows"]:
            gs = row["mean_gap_score"]
            gs_str = f"{gs:.3f}" if gs is not None else "N/A"
            print(f"  {row['adoption_label']:<55} {row['n']:>4} {gs_str:>9}")

    elif r["query"] == "B2-18":
        print(f"  {'Adoption Approach':<55} {'n':>4} {'n_valid':>7} {'median_$':>12} {'mean_$':>12}")
        print(f"  {'-'*92}")
        for row in r["rows"]:
            med = f"${row['median_spend']:,.0f}" if row['median_spend'] is not None else "N/A"
            mn = f"${row['mean_spend']:,.0f}" if row['mean_spend'] is not None else "N/A"
            print(f"  {row['adoption_label']:<55} {row['n_total']:>4} {row['n_valid_spend']:>7} {med:>12} {mn:>12}")

    elif r["query"] == "B2-19":
        print(f"\n  {'Brand':<45} {'Aware%':>7} {'Using%':>7} {'Past%':>6} {'Consid%':>8} {'Funnel%':>8}")
        print(f"  {'-'*82}")
        for b in r["brands"]:
            print(f"  {b['brand']:<45} {b['awareness_pct']:>7.1f} {b['currently_using']['pct']:>7.1f} "
                  f"{b['have_used_past']['pct']:>6.1f} {b['currently_considering']['pct']:>8.1f} "
                  f"{b['consideration_funnel_pct'] if b['consideration_funnel_pct'] is not None else 'N/A':>8}")

    elif r["query"] == "B2-20":
        print(f"\n  {'HQ Location':<60} {'n':>4} {'mean_gap':>9} {'n_spend':>8} {'median_$':>14} {'mean_$':>14}")
        print(f"  {'-'*110}")
        for row in r["rows"]:
            gs = row["mean_gap_score"]
            gs_str = f"{gs:.3f}" if gs is not None else "N/A"
            med = f"${row['median_spend']:,.0f}" if row['median_spend'] is not None else "N/A"
            mn = f"${row['mean_spend']:,.0f}" if row['mean_spend'] is not None else "N/A"
            print(f"  {row['hq_label']:<60} {row['n']:>4} {gs_str:>9} {row['n_valid_spend']:>8} {med:>14} {mn:>14}")

# ===========================================================================
# Write output
# ===========================================================================
with open(OUTPUT_PATH, "w") as f:
    json.dump(output, f, indent=2)

print(f"\n{'='*70}")
print(f"All 20 queries complete. Written to {OUTPUT_PATH}")
print(f"File size: {os.path.getsize(OUTPUT_PATH):,} bytes")
