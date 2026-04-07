#!/usr/bin/env python3
"""
Batch 3: Brand battery queries B3-01 through B3-14.
Output: ~/avasta_batch3_brands.json
All brand-level metrics filter on shown: true AND response_status: "answered".
"""

import json
import os
import statistics
from collections import Counter, defaultdict

RESPONDENTS_PATH = "data/respondents.json"
OUTPUT_PATH = os.path.expanduser("~/avasta_batch3_brands.json")
N = 600
SMALL_N = 15  # flag threshold

STUDY_BRANDS_16 = [
    "Cognizant", "Accenture", "IBM Consulting", "Infosys", "Capgemini",
    "Wipro", "Tata Consultancy Services (TCS)", "EY", "HCL Technologies",
    "Deloitte", "McKinsey & Company", "Google (Cloud & Gemini)",
    "DXC Technology", "ServiceNow", "Microsoft (Azure & Copilot)",
    "Amazon Web Services (AWS)",
]
STUDY_BRANDS_SET = set(STUDY_BRANDS_16)

Q24_ATTRIBUTES = [
    "Industry domain expertise",
    "Innovation & thought leadership",
    "Proven AI case studies",
    "Pricing",
    "Implementation speed",
    "Institutional knowledge",
    "Ecosystem partnerships",
    "Solution customisation",
    "Collaboration & cultural fit",
    "Strategic consulting",
    "Geographic presence",
    "Talent & quality",
]

Q20_CATEGORIES = [
    "Cloud infrastructure company",
    "Software-as-a-service (SaaS) provider",
    "Management consultancy",
    "Technology consultancy",
    "IT services firm",
    "AI startup",
    "AI model company",
]


def r2(x):
    return round(x, 2) if x is not None else None


def r3(x):
    return round(x, 3) if x is not None else None


def avg(vals):
    return statistics.mean(vals) if vals else None


def flag_n(n):
    return f"⚠ n={n}<{SMALL_N}" if n < SMALL_N else f"n={n}"


# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------
with open(RESPONDENTS_PATH) as f:
    data = json.load(f)
assert len(data) == N

output = {}
sep = "=" * 70


def section(qid, title):
    print(f"\n{sep}")
    print(f"=== {qid}: {title} ===")
    print(sep)


# ===========================================================================
# B3-01: Q1 Current TSP performance ratings — per brand
#        Semantic score = avg(code) − 4
# ===========================================================================
def b3_01():
    brand_codes = defaultdict(list)
    for r in data:
        for bs in r.get("brand_scores", []):
            if not bs.get("shown"):
                continue
            field = bs.get("tsp_rating_now", {})
            if isinstance(field, dict) and field.get("response_status") == "answered":
                code = field.get("code")
                if code is not None:
                    brand_codes[bs["brand"]].append(code)

    rows = []
    for brand in STUDY_BRANDS_16:
        codes = brand_codes.get(brand, [])
        n = len(codes)
        avg_code = avg(codes)
        sem = r2(avg_code - 4) if avg_code is not None else None
        rows.append({"brand": brand, "n": n, "avg_raw_code": r3(avg_code), "semantic_score": sem})
    rows.sort(key=lambda x: (x["semantic_score"] is None, -(x["semantic_score"] or 0)))
    return {"query": "B3-01", "title": "Q1 Current TSP Performance Ratings", "rows": rows,
            "note": "Semantic score = avg_raw_code − 4 (scale: −3 to +3)"}


# ===========================================================================
# B3-02: Q2 TSP performance rating 2 years ago — per brand
# ===========================================================================
def b3_02():
    brand_codes = defaultdict(list)
    for r in data:
        for bs in r.get("brand_scores", []):
            if not bs.get("shown"):
                continue
            field = bs.get("tsp_rating_2yrs_ago", {})
            if isinstance(field, dict) and field.get("response_status") == "answered":
                code = field.get("code")
                if code is not None:
                    brand_codes[bs["brand"]].append(code)

    rows = []
    for brand in STUDY_BRANDS_16:
        codes = brand_codes.get(brand, [])
        n = len(codes)
        avg_code = avg(codes)
        sem = r2(avg_code - 4) if avg_code is not None else None
        rows.append({"brand": brand, "n": n, "avg_raw_code": r3(avg_code), "semantic_score": sem})
    rows.sort(key=lambda x: (x["semantic_score"] is None, -(x["semantic_score"] or 0)))
    return {"query": "B3-02", "title": "Q2 TSP Performance Rating 2 Years Ago", "rows": rows,
            "note": "Semantic score = avg_raw_code − 4 (scale: −3 to +3)"}


# ===========================================================================
# B3-03: Q3 TSP performance rating 2 years from now — per brand
# ===========================================================================
def b3_03():
    brand_codes = defaultdict(list)
    for r in data:
        for bs in r.get("brand_scores", []):
            if not bs.get("shown"):
                continue
            field = bs.get("tsp_rating_2yrs_future", {})
            if isinstance(field, dict) and field.get("response_status") == "answered":
                code = field.get("code")
                if code is not None:
                    brand_codes[bs["brand"]].append(code)

    rows = []
    for brand in STUDY_BRANDS_16:
        codes = brand_codes.get(brand, [])
        n = len(codes)
        avg_code = avg(codes)
        sem = r2(avg_code - 4) if avg_code is not None else None
        rows.append({"brand": brand, "n": n, "avg_raw_code": r3(avg_code), "semantic_score": sem})
    rows.sort(key=lambda x: (x["semantic_score"] is None, -(x["semantic_score"] or 0)))
    return {"query": "B3-03", "title": "Q3 TSP Performance Rating 2 Years From Now", "rows": rows,
            "note": "Semantic score = avg_raw_code − 4 (scale: −3 to +3)"}


# ===========================================================================
# B3-04: Trajectory = Q3 semantic − Q1 semantic
# ===========================================================================
def b3_04(b301_rows, b303_rows):
    q1_map = {r["brand"]: r["semantic_score"] for r in b301_rows}
    q3_map = {r["brand"]: r["semantic_score"] for r in b303_rows}
    n_map_q1 = {r["brand"]: r["n"] for r in b301_rows}

    rows = []
    for brand in STUDY_BRANDS_16:
        q1 = q1_map.get(brand)
        q3 = q3_map.get(brand)
        traj = r2(q3 - q1) if q1 is not None and q3 is not None else None
        rows.append({"brand": brand, "q1_semantic": q1, "q3_semantic": q3, "trajectory": traj,
                     "n_q1": n_map_q1.get(brand, 0)})
    rows.sort(key=lambda x: (x["trajectory"] is None, -(x["trajectory"] or 0)))
    return {"query": "B3-04", "title": "Brand Trajectory (Q3 − Q1 Semantic Score)", "rows": rows,
            "note": "Positive trajectory = expected improvement; negative = expected decline"}


# ===========================================================================
# B3-05: Q23 Overall AI perception score — per brand
#        Values stored directly as −3 to +3; no transformation needed.
#        Filter: brand must be shown (consistent with brand_scores shown logic).
# ===========================================================================
def b3_05():
    # Build shown-brand set per respondent from brand_scores
    shown_per_resp = {}
    for r in data:
        shown_per_resp[r["record"]] = {bs["brand"] for bs in r.get("brand_scores", []) if bs.get("shown")}

    brand_vals = defaultdict(list)
    for r in data:
        shown = shown_per_resp.get(r["record"], set())
        for entry in (r["responses"].get("q23") or []):
            brand = entry.get("brand")
            val = entry.get("value")
            if brand and val is not None and brand in shown:
                brand_vals[brand].append(val)

    rows = []
    for brand in STUDY_BRANDS_16:
        vals = brand_vals.get(brand, [])
        n = len(vals)
        mean_val = avg(vals)
        rows.append({"brand": brand, "n": n, "avg_score": r2(mean_val),
                     "small_n_flag": n < SMALL_N})
    rows.sort(key=lambda x: (x["avg_score"] is None, -(x["avg_score"] or 0)))
    return {"query": "B3-05", "title": "Q23 Overall AI Perception Score", "rows": rows,
            "note": "Values already on −3 to +3 scale; no transformation applied. Filtered to shown brands."}


# ===========================================================================
# B3-06: Q24 Brand attribute ratings — per brand per attribute
# ===========================================================================
def b3_06():
    # brand → attribute → [values]
    brand_attr_vals = defaultdict(lambda: defaultdict(list))
    for r in data:
        for bs in r.get("brand_scores", []):
            if not bs.get("shown"):
                continue
            for attr_entry in (bs.get("attribute_ratings") or []):
                if attr_entry.get("response_status") != "answered":
                    continue
                attr = attr_entry.get("attribute")
                val = attr_entry.get("value")
                if attr and val is not None:
                    brand_attr_vals[bs["brand"]][attr].append(val)

    rows = []
    for brand in STUDY_BRANDS_16:
        attr_avgs = {}
        attr_ns = {}
        for attr in Q24_ATTRIBUTES:
            vals = brand_attr_vals[brand].get(attr, [])
            attr_ns[attr] = len(vals)
            attr_avgs[attr] = r2(avg(vals))

        valid_avgs = {a: v for a, v in attr_avgs.items() if v is not None}
        strongest = max(valid_avgs, key=valid_avgs.get) if valid_avgs else None
        weakest = min(valid_avgs, key=valid_avgs.get) if valid_avgs else None

        rows.append({
            "brand": brand,
            "attribute_scores": {a: {"avg": attr_avgs[a], "n": attr_ns[a]} for a in Q24_ATTRIBUTES},
            "strongest_attribute": strongest,
            "strongest_score": attr_avgs.get(strongest),
            "weakest_attribute": weakest,
            "weakest_score": attr_avgs.get(weakest),
        })

    return {"query": "B3-06", "title": "Q24 Brand Attribute Ratings (−3 to +3)", "rows": rows,
            "attributes": Q24_ATTRIBUTES,
            "note": "Values stored directly as −3 to +3; no transformation applied. Only answered responses included."}


# ===========================================================================
# B3-07: Q27 Purchase intent — per brand
#        Intent score = avg(code) − 1 (0–5 scale)
#        High intent = code ≥ 5 (labels "4" or "5 — Almost certainly")
# ===========================================================================
def b3_07():
    brand_codes = defaultdict(list)
    for r in data:
        for bs in r.get("brand_scores", []):
            if not bs.get("shown"):
                continue
            field = bs.get("purchase_intent", {})
            if isinstance(field, dict) and field.get("response_status") == "answered":
                code = field.get("code")
                if code is not None:
                    brand_codes[bs["brand"]].append(code)

    rows = []
    for brand in STUDY_BRANDS_16:
        codes = brand_codes.get(brand, [])
        n = len(codes)
        avg_code = avg(codes)
        intent_score = r2(avg_code - 1) if avg_code is not None else None
        high_intent_n = sum(1 for c in codes if c >= 5)
        high_intent_pct = round(high_intent_n / n * 100, 1) if n > 0 else None
        rows.append({
            "brand": brand,
            "n": n,
            "avg_raw_code": r3(avg_code),
            "intent_score": intent_score,
            "high_intent_n": high_intent_n,
            "high_intent_pct": high_intent_pct,
            "small_n_flag": n < SMALL_N,
        })
    rows.sort(key=lambda x: (x["intent_score"] is None, -(x["intent_score"] or 0)))
    return {"query": "B3-07", "title": "Q27 Purchase Intent (0–5 scale)", "rows": rows,
            "note": "Intent score = avg_raw_code − 1. High intent = code ≥ 5 (label '4' or '5-Almost certainly')."}


# ===========================================================================
# B3-08: Q25 Brand ranking 2 years ago — per brand
# ===========================================================================
def b3_08():
    brand_ranks = defaultdict(list)
    brand_rank1 = Counter()
    for r in data:
        for bs in r.get("brand_scores", []):
            if not bs.get("shown"):
                continue
            field = bs.get("rank_2yrs_ago", {})
            if isinstance(field, dict) and field.get("response_status") == "answered":
                rank = field.get("rank")
                if rank is not None:
                    brand_ranks[bs["brand"]].append(rank)
                    if rank == 1:
                        brand_rank1[bs["brand"]] += 1

    rows = []
    for brand in STUDY_BRANDS_16:
        ranks = brand_ranks.get(brand, [])
        n = len(ranks)
        avg_rank = r2(avg(ranks))
        pct_rank1 = round(brand_rank1[brand] / n * 100, 1) if n > 0 else None
        rows.append({
            "brand": brand,
            "n": n,
            "avg_rank": avg_rank,
            "pct_ranked_1st": pct_rank1,
            "small_n_flag": n < SMALL_N,
        })
    rows.sort(key=lambda x: (x["avg_rank"] is None, x["avg_rank"] or 99))
    return {
        "query": "B3-08",
        "title": "Q25 Brand Ranking 2 Years Ago",
        "rows": rows,
        "note": "Lower avg rank = better. Rankings are relative within each respondent's shown brand set (3–6 brands), so avg ranks are not directly comparable across brands with very different evaluator pools.",
    }


# ===========================================================================
# B3-09: Q26 Brand ranking 2 years from now
#        Momentum = avg rank Q25 − avg rank Q26 (positive = improving)
# ===========================================================================
def b3_09(b308_rows):
    brand_ranks = defaultdict(list)
    brand_rank1 = Counter()
    for r in data:
        for bs in r.get("brand_scores", []):
            if not bs.get("shown"):
                continue
            field = bs.get("rank_2yrs_future", {})
            if isinstance(field, dict) and field.get("response_status") == "answered":
                rank = field.get("rank")
                if rank is not None:
                    brand_ranks[bs["brand"]].append(rank)
                    if rank == 1:
                        brand_rank1[bs["brand"]] += 1

    past_avg = {r["brand"]: r["avg_rank"] for r in b308_rows}

    rows = []
    for brand in STUDY_BRANDS_16:
        ranks = brand_ranks.get(brand, [])
        n = len(ranks)
        avg_rank = r2(avg(ranks))
        pct_rank1 = round(brand_rank1[brand] / n * 100, 1) if n > 0 else None
        past = past_avg.get(brand)
        momentum = r2(past - avg_rank) if past is not None and avg_rank is not None else None
        rows.append({
            "brand": brand,
            "n": n,
            "avg_rank_future": avg_rank,
            "avg_rank_past": past,
            "momentum": momentum,
            "pct_ranked_1st_future": pct_rank1,
            "small_n_flag": n < SMALL_N,
        })
    rows.sort(key=lambda x: (x["avg_rank_future"] is None, x["avg_rank_future"] or 99))
    return {
        "query": "B3-09",
        "title": "Q26 Brand Ranking 2 Years From Now + Momentum",
        "rows": rows,
        "note": "Momentum = avg_rank_past − avg_rank_future (positive = expected to rank better in future). Lower rank number = better.",
    }


# ===========================================================================
# B3-10: Q20 Brand category perception — per brand
# ===========================================================================
def b3_10():
    brand_cat_counts = defaultdict(Counter)
    brand_n = Counter()
    for r in data:
        for bs in r.get("brand_scores", []):
            if not bs.get("shown"):
                continue
            bcp = bs.get("brand_category_perception", {})
            if isinstance(bcp, dict) and bcp.get("response_status") == "answered":
                brand_n[bs["brand"]] += 1
                for cat in (bcp.get("selected_categories") or []):
                    brand_cat_counts[bs["brand"]][cat] += 1

    rows = []
    for brand in STUDY_BRANDS_16:
        n = brand_n[brand]
        cat_counts = brand_cat_counts[brand]
        cat_dist = [
            {"category": cat, "count": cat_counts.get(cat, 0),
             "pct": round(cat_counts.get(cat, 0) / n * 100, 1) if n > 0 else None}
            for cat in Q20_CATEGORIES
        ]
        cat_dist_sorted = sorted(cat_dist, key=lambda x: -x["count"])
        top3 = [c["category"] for c in cat_dist_sorted[:3]]
        rows.append({
            "brand": brand,
            "n": n,
            "category_distribution": cat_dist,
            "top_3_categories": top3,
            "small_n_flag": n < SMALL_N,
        })
    rows.sort(key=lambda x: -x["n"])
    return {"query": "B3-10", "title": "Q20 Brand Category Perception", "rows": rows,
            "categories": Q20_CATEGORIES}


# ===========================================================================
# B3-11: Brand awareness funnel — all 5 levels
# ===========================================================================
def b3_11():
    # Level 1: Aware (S9 codes 1–5)
    # Level 2: Familiar/considering (S9 codes 1–4)
    # Level 3: Currently using (S9 code 1)
    lvl1 = Counter()
    lvl2 = Counter()
    lvl3 = Counter()
    for r in data:
        for bf in (r["profile"].get("brand_familiarity") or []):
            brand = bf.get("brand")
            code = bf.get("code")
            if brand and code is not None:
                if code <= 5:
                    lvl1[brand] += 1
                if code <= 4:
                    lvl2[brand] += 1
                if code == 1:
                    lvl3[brand] += 1

    # Level 4: High purchase intent (Q27 code ≥ 5 among shown)
    lvl4_num = Counter()
    lvl4_den = Counter()
    for r in data:
        for bs in r.get("brand_scores", []):
            if not bs.get("shown"):
                continue
            pi = bs.get("purchase_intent", {})
            if isinstance(pi, dict) and pi.get("response_status") == "answered":
                lvl4_den[bs["brand"]] += 1
                if (pi.get("code") or 0) >= 5:
                    lvl4_num[bs["brand"]] += 1

    # Level 5: Primary preference (Q28)
    lvl5 = Counter()
    for r in data:
        pt = r["responses"].get("preferred_tsp")
        if pt and pt.get("label"):
            lvl5[pt["label"]] += 1

    rows = []
    for brand in STUDY_BRANDS_16:
        n1 = lvl1[brand]
        n2 = lvl2[brand]
        n3 = lvl3[brand]
        n4_num = lvl4_num[brand]
        n4_den = lvl4_den[brand]
        n5 = lvl5[brand]
        rows.append({
            "brand": brand,
            "lvl1_aware": {"n": n1, "pct_of_600": round(n1 / N * 100, 1)},
            "lvl2_familiar_or_considering": {"n": n2, "pct_of_600": round(n2 / N * 100, 1)},
            "lvl3_current_user": {"n": n3, "pct_of_600": round(n3 / N * 100, 1)},
            "lvl4_high_intent": {
                "n": n4_num,
                "n_shown": n4_den,
                "pct_of_shown": round(n4_num / n4_den * 100, 1) if n4_den > 0 else None,
            },
            "lvl5_primary_preference": {"n": n5, "pct_of_600": round(n5 / N * 100, 1)},
        })
    rows.sort(key=lambda x: -x["lvl1_aware"]["pct_of_600"])
    return {
        "query": "B3-11",
        "title": "Brand Awareness Funnel (New Metric)",
        "rows": rows,
        "note": "Lvl1-3 and Lvl5 base=600; Lvl4 base=shown respondents. New metric not in prior data reference.",
    }


# ===========================================================================
# B3-12: Cognizant vs. market average on Q24 attributes
# ===========================================================================
def b3_12(b306_result):
    rows_06 = b306_result["rows"]
    cognizant_row = next((r for r in rows_06 if r["brand"] == "Cognizant"), None)

    gaps = []
    for attr in Q24_ATTRIBUTES:
        cog_score = cognizant_row["attribute_scores"][attr]["avg"] if cognizant_row else None
        market_scores = []
        for row in rows_06:
            s = row["attribute_scores"][attr]["avg"]
            if s is not None:
                market_scores.append(s)
        market_avg = r2(avg(market_scores)) if market_scores else None
        gap = r2(cog_score - market_avg) if cog_score is not None and market_avg is not None else None
        gaps.append({
            "attribute": attr,
            "cognizant_score": cog_score,
            "market_avg_score": market_avg,
            "gap_vs_market": gap,
            "cognizant_n": cognizant_row["attribute_scores"][attr]["n"] if cognizant_row else 0,
        })

    gaps.sort(key=lambda x: (x["gap_vs_market"] is None, x["gap_vs_market"] or 0))
    return {
        "query": "B3-12",
        "title": "Cognizant vs. Market Average — Q24 Attribute Gaps",
        "rows": gaps,
        "note": "Gap = Cognizant − market average. Negative = below market. Sorted: largest deficit first.",
    }


# ===========================================================================
# B3-13: Q1 Current performance — Cognizant by industry
#        Industries with n≥10 Cognizant evaluators full; <10 flagged
# ===========================================================================
def b3_13():
    MIN_N = 10
    ind_codes = defaultdict(list)
    for r in data:
        ind = r["profile"].get("industry", {})
        ind_label = ind.get("label") if ind else None
        if not ind_label:
            continue
        for bs in r.get("brand_scores", []):
            if bs.get("brand") != "Cognizant" or not bs.get("shown"):
                continue
            field = bs.get("tsp_rating_now", {})
            if isinstance(field, dict) and field.get("response_status") == "answered":
                code = field.get("code")
                if code is not None:
                    ind_codes[ind_label].append(code)

    rows = []
    for ind_label, codes in sorted(ind_codes.items(), key=lambda x: -len(x[1])):
        n = len(codes)
        avg_code = avg(codes)
        sem = r2(avg_code - 4) if avg_code is not None else None
        rows.append({
            "industry": ind_label,
            "n": n,
            "semantic_score": sem,
            "small_n_flag": n < MIN_N,
        })
    rows.sort(key=lambda x: (x["semantic_score"] is None, -(x["semantic_score"] or 0)))
    return {
        "query": "B3-13",
        "title": "Q1 Cognizant Performance by Industry",
        "rows": rows,
        "note": f"Semantic score = avg_raw_code − 4. Industries with n<{MIN_N} Cognizant evaluators flagged.",
        "min_n_for_reliability": MIN_N,
    }


# ===========================================================================
# B3-14: Q27 Purchase intent by S9 familiarity level — per brand
# ===========================================================================
def b3_14():
    FAM_LABELS = {
        1: "Currently using",
        2: "Have used in past",
        3: "Currently considering",
        4: "Familiar never used",
        5: "Heard name only",
    }
    MIN_N_FLAG = 10

    # Build familiarity lookup: (record, brand) → S9 code
    fam_lookup = {}
    for r in data:
        for bf in (r["profile"].get("brand_familiarity") or []):
            brand = bf.get("brand")
            code = bf.get("code")
            if brand and code is not None:
                fam_lookup[(r["record"], brand)] = code

    # brand → fam_code → [intent codes]
    brand_fam_intent = defaultdict(lambda: defaultdict(list))
    for r in data:
        for bs in r.get("brand_scores", []):
            if not bs.get("shown"):
                continue
            pi = bs.get("purchase_intent", {})
            if isinstance(pi, dict) and pi.get("response_status") == "answered":
                intent_code = pi.get("code")
                if intent_code is None:
                    continue
                brand = bs["brand"]
                fam_code = fam_lookup.get((r["record"], brand))
                if fam_code is not None:
                    brand_fam_intent[brand][fam_code].append(intent_code)

    rows = []
    for brand in STUDY_BRANDS_16:
        fam_breakdown = {}
        for fam_code, fam_label in FAM_LABELS.items():
            codes = brand_fam_intent[brand].get(fam_code, [])
            n = len(codes)
            avg_code = avg(codes)
            intent_score = r2(avg_code - 1) if avg_code is not None else None
            fam_breakdown[fam_label] = {
                "fam_code": fam_code,
                "n": n,
                "intent_score": intent_score,
                "small_n_flag": n < MIN_N_FLAG,
            }
        rows.append({"brand": brand, "familiarity_breakdown": fam_breakdown})

    return {
        "query": "B3-14",
        "title": "Q27 Purchase Intent by S9 Familiarity Level",
        "rows": rows,
        "note": f"Intent score = avg_raw_code − 1 (0–5 scale). Cells with n<{MIN_N_FLAG} flagged.",
    }


# ---------------------------------------------------------------------------
# Run all queries
# ---------------------------------------------------------------------------
r01 = b3_01()
r02 = b3_02()
r03 = b3_03()
r04 = b3_04(r01["rows"], r03["rows"])
r05 = b3_05()
r06 = b3_06()
r07 = b3_07()
r08 = b3_08()
r09 = b3_09(r08["rows"])
r10 = b3_10()
r11 = b3_11()
r12 = b3_12(r06)
r13 = b3_13()
r14 = b3_14()

all_results = [r01, r02, r03, r04, r05, r06, r07, r08, r09, r10, r11, r12, r13, r14]


# ---------------------------------------------------------------------------
# Print output
# ---------------------------------------------------------------------------
def print_b301_style(res, label="Semantic score"):
    section(res["query"], res["title"])
    print(f"  {'Brand':<48} {'n':>5}  {'Avg code':>9}  {label:>14}")
    print(f"  {'-'*82}")
    for row in res["rows"]:
        n_str = flag_n(row["n"])
        print(f"  {row['brand']:<48} {n_str:>8}  {(row['avg_raw_code'] or 0):>9.3f}  {(row['semantic_score'] or 0):>14.2f}")
    print(f"\n  Note: {res['note']}")


print_b301_style(r01)
print_b301_style(r02)
print_b301_style(r03)

# B3-04 Trajectory
section("B3-04", r04["title"])
print(f"  {'Brand':<48} {'Q1':>6}  {'Q3':>6}  {'Trajectory':>11}")
print(f"  {'-'*73}")
for row in r04["rows"]:
    print(f"  {row['brand']:<48} {(row['q1_semantic'] or 0):>6.2f}  {(row['q3_semantic'] or 0):>6.2f}  {(row['trajectory'] or 0):>+11.2f}")
print(f"\n  Note: {r04['note']}")

# B3-05 Q23 Perception
section("B3-05", r05["title"])
print(f"  {'Brand':<48} {'n':>8}  {'Avg score (−3 to +3)':>20}")
print(f"  {'-'*80}")
for row in r05["rows"]:
    n_str = flag_n(row["n"])
    flag = " ⚠" if row["small_n_flag"] else ""
    print(f"  {row['brand']:<48} {n_str:>8}  {(row['avg_score'] or 0):>20.2f}{flag}")
print(f"\n  Note: {r05['note']}")

# B3-06 Attribute ratings
section("B3-06", r06["title"])
ATTR_ABBREV = [
    "IndDomain", "Innovation", "AICases", "Pricing", "ImplSpd",
    "InstitKnow", "EcoPartner", "SolCust", "Collab", "StratConsult",
    "GeoPresn", "Talent",
]
print(f"  {'Brand':<35}" + "".join(f" {a:>9}" for a in ATTR_ABBREV) + f"  {'Strongest':<25}  {'Weakest'}")
print(f"  {'-'*170}")
for row in sorted(r06["rows"], key=lambda x: x["brand"]):
    scores = [row["attribute_scores"].get(a, {}).get("avg") for a in Q24_ATTRIBUTES]
    score_strs = [f"{s:>9.2f}" if s is not None else f"{'N/A':>9}" for s in scores]
    print(f"  {row['brand']:<35}" + "".join(score_strs) +
          f"  {(row['strongest_attribute'] or 'N/A'):<25}  {row['weakest_attribute'] or 'N/A'}")
print(f"\n  Note: {r06['note']}")

# B3-07 Purchase intent
section("B3-07", r07["title"])
print(f"  {'Brand':<48} {'n':>8}  {'Avg code':>9}  {'Intent(0-5)':>11}  {'HighIntent%':>11}")
print(f"  {'-'*95}")
for row in r07["rows"]:
    n_str = flag_n(row["n"])
    flag = " ⚠" if row["small_n_flag"] else ""
    print(f"  {row['brand']:<48} {n_str:>8}  {(row['avg_raw_code'] or 0):>9.3f}  "
          f"{(row['intent_score'] or 0):>11.2f}  {(row['high_intent_pct'] or 0):>11.1f}%{flag}")
print(f"\n  Note: {r07['note']}")

# B3-08 Ranking past
section("B3-08", r08["title"])
print(f"  {'Brand':<48} {'n':>8}  {'Avg rank':>9}  {'% Ranked #1':>12}")
print(f"  {'-'*80}")
for row in r08["rows"]:
    n_str = flag_n(row["n"])
    print(f"  {row['brand']:<48} {n_str:>8}  {(row['avg_rank'] or 0):>9.2f}  {(row['pct_ranked_1st'] or 0):>12.1f}%")
print(f"\n  Note: {r08['note']}")

# B3-09 Ranking future + momentum
section("B3-09", r09["title"])
print(f"  {'Brand':<48} {'n':>8}  {'AvgRkFut':>9}  {'AvgRkPast':>10}  {'Momentum':>9}  {'%#1Fut':>7}")
print(f"  {'-'*100}")
for row in r09["rows"]:
    n_str = flag_n(row["n"])
    mom = row["momentum"]
    mom_str = f"{mom:>+9.2f}" if mom is not None else f"{'N/A':>9}"
    print(f"  {row['brand']:<48} {n_str:>8}  {(row['avg_rank_future'] or 0):>9.2f}  "
          f"{(row['avg_rank_past'] or 0):>10.2f}  {mom_str}  {(row['pct_ranked_1st_future'] or 0):>7.1f}%")
print(f"\n  Note: {r09['note']}")

# B3-10 Category perception
section("B3-10", r10["title"])
CAT_ABBREV = ["CloudInfra", "SaaS", "MgmtConsult", "TechConsult", "ITSvcs", "AIStartup", "AIModel"]
print(f"  {'Brand':<40} {'n':>5}" + "".join(f" {a:>11}" for a in CAT_ABBREV) + "  Top-3")
print(f"  {'-'*160}")
for row in r10["rows"]:
    cat_pcts = [f"{d['pct']:>11.1f}%" if d['pct'] is not None else f"{'N/A':>12}"
                for d in row["category_distribution"]]
    top3 = " / ".join(row["top_3_categories"])
    print(f"  {row['brand']:<40} {row['n']:>5}" + "".join(cat_pcts) + f"  {top3}")

# B3-11 Awareness funnel
section("B3-11", r11["title"])
print(f"  {'Brand':<40} {'Aware%':>7}  {'Fam%':>6}  {'Using%':>7}  {'HighInt%(shown)':>16}  {'Pref%':>6}")
print(f"  {'-'*95}")
for row in r11["rows"]:
    hi = row["lvl4_high_intent"]["pct_of_shown"]
    hi_str = f"{hi:>16.1f}%" if hi is not None else f"{'N/A':>17}"
    print(f"  {row['brand']:<40} "
          f"{row['lvl1_aware']['pct_of_600']:>7.1f}%  "
          f"{row['lvl2_familiar_or_considering']['pct_of_600']:>6.1f}%  "
          f"{row['lvl3_current_user']['pct_of_600']:>7.1f}%  "
          f"{hi_str}  "
          f"{row['lvl5_primary_preference']['pct_of_600']:>6.1f}%")
print(f"\n  Note: {r11['note']}")

# B3-12 Cognizant vs market
section("B3-12", r12["title"])
print(f"  {'Attribute':<35} {'Cognizant':>10}  {'MktAvg':>8}  {'Gap':>8}  {'n_Cog':>6}")
print(f"  {'-'*72}")
for row in r12["rows"]:
    gap = row["gap_vs_market"]
    gap_str = f"{gap:>+8.2f}" if gap is not None else f"{'N/A':>8}"
    print(f"  {row['attribute']:<35} {(row['cognizant_score'] or 0):>10.2f}  "
          f"{(row['market_avg_score'] or 0):>8.2f}  {gap_str}  {row['cognizant_n']:>6}")
print(f"\n  Note: {r12['note']}")

# B3-13 Cognizant by industry
section("B3-13", r13["title"])
print(f"  {'Industry':<55} {'n':>5}  {'Semantic score':>14}")
print(f"  {'-'*76}")
for row in r13["rows"]:
    flag = " ⚠ small n" if row["small_n_flag"] else ""
    print(f"  {row['industry']:<55} {row['n']:>5}  {(row['semantic_score'] or 0):>14.2f}{flag}")
print(f"\n  Note: {r13['note']}")

# B3-14 Intent by familiarity
section("B3-14", r14["title"])
FAM_ORDER = ["Currently using", "Have used in past", "Currently considering",
             "Familiar never used", "Heard name only"]
FAM_ABBREV = ["Using", "PastUsr", "Consid", "FamNvr", "HeardOnly"]
print(f"  {'Brand':<48}" + "".join(f" {a:>10}" for a in FAM_ABBREV))
print(f"  {'-'*100}")
for row in r14["rows"]:
    fb = row["familiarity_breakdown"]
    scores = []
    for fam_lbl in FAM_ORDER:
        cell = fb.get(fam_lbl, {})
        s = cell.get("intent_score")
        n = cell.get("n", 0)
        if s is not None:
            marker = "⚠" if cell.get("small_n_flag") else " "
            scores.append(f"{s:>9.2f}{marker}")
        else:
            scores.append(f"{'N/A':>10}")
    print(f"  {row['brand']:<48}" + "".join(scores))
print(f"\n  Note: {r14['note']}")
print(f"  ⚠ = n<10 for that cell")

# ---------------------------------------------------------------------------
# Write output
# ---------------------------------------------------------------------------
for res in all_results:
    output[res["query"]] = res

with open(OUTPUT_PATH, "w") as f:
    json.dump(output, f, indent=2)

print(f"\n{sep}")
print(f"All 14 queries complete. Written to {OUTPUT_PATH}")
print(f"File size: {os.path.getsize(OUTPUT_PATH):,} bytes")
