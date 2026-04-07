#!/usr/bin/env python3
"""
Batch 4: Cognizant-specific queries B4-01 through B4-08.
Output: ~/avasta_batch4_cognizant.json
"""

import json
import os
import statistics
from collections import Counter, defaultdict

RESPONDENTS_PATH = "data/respondents.json"
OUTPUT_PATH = os.path.expanduser("~/avasta_batch4_cognizant.json")
N = 600
SMALL_N = 15
FULL_SAMPLE_Q43_MEAN = 0.553   # from B2-13/B2-14 context
FULL_SAMPLE_MEDIAN_SPEND = 11_000_000

STUDY_BRANDS_16 = [
    "Cognizant", "Accenture", "IBM Consulting", "Infosys", "Capgemini",
    "Wipro", "Tata Consultancy Services (TCS)", "EY", "HCL Technologies",
    "Deloitte", "McKinsey & Company", "Google (Cloud & Gemini)",
    "DXC Technology", "ServiceNow", "Microsoft (Azure & Copilot)",
    "Amazon Web Services (AWS)",
]

Q43_SCORE = {1: 1.0, 2: 0.75, 3: 0.50, 4: 0.25, 5: 0.0}

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

IND_MIN_N = 15   # full-sample threshold for B4-04
COG_EVAL_MIN_N = 10  # Cognizant evaluator threshold for B4-05


def r2(x):
    return round(x, 2) if x is not None else None


def r3(x):
    return round(x, 3) if x is not None else None


def avg(vals):
    return statistics.mean(vals) if vals else None


def flag(n, thresh=SMALL_N):
    return f" ⚠ n<{thresh}" if n < thresh else ""


def sep(qid, title):
    bar = "=" * 70
    print(f"\n{bar}")
    print(f"=== {qid}: {title} ===")
    print(bar)


# ---------------------------------------------------------------------------
with open(RESPONDENTS_PATH) as f:
    data = json.load(f)
assert len(data) == N

# ---------------------------------------------------------------------------
# Precompute per-respondent helpers
# ---------------------------------------------------------------------------

# brand_familiarity lookup: record → brand → S9 code
fam_lookup = {}
for r in data:
    fam_lookup[r["record"]] = {}
    for bf in r["profile"].get("brand_familiarity") or []:
        if bf.get("brand"):
            fam_lookup[r["record"]][bf["brand"]] = bf.get("code")

# Cognizant brand_scores lookup: record → {shown, q1_code, q27_code, attr_ratings}
cog_bs = {}
for r in data:
    for bs in r.get("brand_scores", []):
        if bs["brand"] != "Cognizant":
            continue
        q1_field = bs.get("tsp_rating_now", {})
        q27_field = bs.get("purchase_intent", {})
        cog_bs[r["record"]] = {
            "shown": bs.get("shown", False),
            "q1_code": q1_field.get("code") if isinstance(q1_field, dict) and q1_field.get("response_status") == "answered" else None,
            "q27_code": q27_field.get("code") if isinstance(q27_field, dict) and q27_field.get("response_status") == "answered" else None,
            "attribute_ratings": bs.get("attribute_ratings", []),
        }

# Q43 score lookup: record → score
q43_score_lookup = {}
for r in data:
    q43 = r["responses"].get("q43")
    if q43 and q43.get("code") is not None:
        q43_score_lookup[r["record"]] = Q43_SCORE.get(q43["code"])

output = {}


# ===========================================================================
# B4-01: Cognizant Q1 by function
# ===========================================================================
def b4_01():
    func_q1 = defaultdict(list)
    func_q27 = defaultdict(list)

    for r in data:
        cbs = cog_bs.get(r["record"], {})
        if not cbs.get("shown") or cbs.get("q1_code") is None:
            continue
        q1_sem = cbs["q1_code"] - 4
        q27_score = cbs["q27_code"] - 1 if cbs.get("q27_code") is not None else None
        for func in r["profile"].get("functions") or []:
            func_q1[func].append(q1_sem)
            if q27_score is not None:
                func_q27[func].append(q27_score)

    rows = []
    for func in sorted(func_q1.keys()):
        n = len(func_q1[func])
        q1_avg = avg(func_q1[func])
        q27_avg = avg(func_q27[func])
        rows.append({
            "function": func,
            "n": n,
            "q1_semantic": r2(q1_avg),
            "q27_intent": r2(q27_avg),
            "small_n": n < SMALL_N,
        })
    rows.sort(key=lambda x: (x["q1_semantic"] is None, -(x["q1_semantic"] or 0)))
    return {"query": "B4-01", "title": "Cognizant Q1 Performance by Function", "rows": rows}


# ===========================================================================
# B4-02: Cognizant Q1 by seniority
# ===========================================================================
def b4_02():
    sen_q1 = defaultdict(list)
    sen_q27 = defaultdict(list)
    sen_codes = {}

    for r in data:
        cbs = cog_bs.get(r["record"], {})
        if not cbs.get("shown") or cbs.get("q1_code") is None:
            continue
        sen = r["profile"].get("seniority", {})
        label = sen.get("label") if sen else None
        code = sen.get("code") if sen else None
        if not label:
            continue
        sen_codes[label] = code
        q1_sem = cbs["q1_code"] - 4
        q27_score = cbs["q27_code"] - 1 if cbs.get("q27_code") is not None else None
        sen_q1[label].append(q1_sem)
        if q27_score is not None:
            sen_q27[label].append(q27_score)

    rows = []
    for label in sorted(sen_q1.keys(), key=lambda x: sen_codes.get(x, 99)):
        n = len(sen_q1[label])
        rows.append({
            "seniority": label,
            "n": n,
            "q1_semantic": r2(avg(sen_q1[label])),
            "q27_intent": r2(avg(sen_q27[label])),
            "small_n": n < SMALL_N,
        })
    rows.sort(key=lambda x: (x["q1_semantic"] is None, -(x["q1_semantic"] or 0)))
    return {"query": "B4-02", "title": "Cognizant Q1 Performance by Seniority", "rows": rows}


# ===========================================================================
# B4-03: Cognizant attribute ratings — current users vs. non-users
# ===========================================================================
def b4_03():
    user_vals = defaultdict(list)    # S9 code 1
    nonuser_vals = defaultdict(list) # S9 codes 2-5

    for r in data:
        cbs = cog_bs.get(r["record"], {})
        if not cbs.get("shown"):
            continue
        s9_code = fam_lookup.get(r["record"], {}).get("Cognizant")
        is_user = s9_code == 1
        is_nonuser = s9_code in {2, 3, 4, 5}
        if not is_user and not is_nonuser:
            continue
        for attr_entry in cbs.get("attribute_ratings", []):
            if attr_entry.get("response_status") != "answered":
                continue
            attr = attr_entry.get("attribute")
            val = attr_entry.get("value")
            if attr and val is not None:
                if is_user:
                    user_vals[attr].append(val)
                else:
                    nonuser_vals[attr].append(val)

    rows = []
    for attr in Q24_ATTRIBUTES:
        u_vals = user_vals.get(attr, [])
        nu_vals = nonuser_vals.get(attr, [])
        u_avg = avg(u_vals)
        nu_avg = avg(nu_vals)
        diff = r2(u_avg - nu_avg) if u_avg is not None and nu_avg is not None else None
        rows.append({
            "attribute": attr,
            "users_n": len(u_vals),
            "users_avg": r2(u_avg),
            "nonusers_n": len(nu_vals),
            "nonusers_avg": r2(nu_avg),
            "diff_user_minus_nonuser": diff,
        })
    rows.sort(key=lambda x: (x["diff_user_minus_nonuser"] is None, -(x["diff_user_minus_nonuser"] or 0)))
    return {
        "query": "B4-03",
        "title": "Cognizant Attribute Ratings: Current Users vs. Non-Users",
        "rows": rows,
        "note": "Users = S9 code 1. Non-users = S9 codes 2-5. Diff = users minus non-users.",
    }


# ===========================================================================
# B4-04: Cognizant consideration funnel by industry (full-sample n≥15)
# ===========================================================================
def b4_04():
    # Full sample industry counts
    ind_all = defaultdict(list)
    for r in data:
        ind = r["profile"].get("industry", {})
        lbl = ind.get("label") if ind else None
        if lbl:
            ind_all[lbl].append(r)

    rows = []
    for ind_label, ind_recs in sorted(ind_all.items(), key=lambda x: -len(x[1])):
        n_ind = len(ind_recs)
        aware = fam_nick = user = pref = 0
        for r in ind_recs:
            s9 = fam_lookup.get(r["record"], {}).get("Cognizant")
            if s9 is not None and s9 <= 5:
                aware += 1
            if s9 is not None and s9 <= 4:
                fam_nick += 1
            if s9 == 1:
                user += 1
            if r["responses"].get("preferred_tsp", {}).get("label") == "Cognizant":
                pref += 1
        rows.append({
            "industry": ind_label,
            "n_industry": n_ind,
            "n_aware": aware,
            "pct_aware": round(aware / n_ind * 100, 1),
            "n_familiar": fam_nick,
            "pct_familiar": round(fam_nick / n_ind * 100, 1),
            "n_current_user": user,
            "pct_current_user": round(user / n_ind * 100, 1),
            "n_primary_pref": pref,
            "pct_primary_pref": round(pref / n_ind * 100, 1),
            "below_threshold": n_ind < IND_MIN_N,
        })
    rows.sort(key=lambda x: -x["pct_current_user"])
    return {
        "query": "B4-04",
        "title": "Cognizant Consideration Funnel by Industry",
        "rows": rows,
        "note": f"Industries below n={IND_MIN_N} in full sample flagged.",
    }


# ===========================================================================
# B4-05: Cognizant Q1 performance + Q27 intent + industry Q43 context
# ===========================================================================
def b4_05():
    # Per-industry: Cognizant evaluators q1/q27, and full-industry Q43
    ind_q1 = defaultdict(list)
    ind_q27 = defaultdict(list)
    ind_q43_all = defaultdict(list)  # all respondents in industry

    for r in data:
        ind = r["profile"].get("industry", {})
        ind_lbl = ind.get("label") if ind else None
        if not ind_lbl:
            continue
        q43 = r["responses"].get("q43")
        if q43 and q43.get("code") is not None:
            gs = Q43_SCORE.get(q43["code"])
            if gs is not None:
                ind_q43_all[ind_lbl].append(gs)
        cbs = cog_bs.get(r["record"], {})
        if cbs.get("shown") and cbs.get("q1_code") is not None:
            ind_q1[ind_lbl].append(cbs["q1_code"] - 4)
            if cbs.get("q27_code") is not None:
                ind_q27[ind_lbl].append(cbs["q27_code"] - 1)

    rows = []
    for ind_lbl, q1_vals in sorted(ind_q1.items(), key=lambda x: -len(x[1])):
        n = len(q1_vals)
        q27_vals = ind_q27.get(ind_lbl, [])
        q43_vals = ind_q43_all.get(ind_lbl, [])
        rows.append({
            "industry": ind_lbl,
            "n_cog_evaluators": n,
            "q1_semantic": r2(avg(q1_vals)),
            "q27_intent": r2(avg(q27_vals)),
            "industry_q43_mean": r2(avg(q43_vals)),
            "small_n": n < COG_EVAL_MIN_N,
        })
    rows.sort(key=lambda x: (x["q1_semantic"] is None, -(x["q1_semantic"] or 0)))
    return {
        "query": "B4-05",
        "title": "Cognizant Q1 Performance by Industry (Extended, n≥10 evaluators)",
        "rows": rows,
        "note": f"Industries with n<{COG_EVAL_MIN_N} Cognizant evaluators flagged.",
    }


# ===========================================================================
# B4-06: Profile of Cognizant Q28 primary preference selectors
# ===========================================================================
def b4_06():
    pref_recs = [r for r in data if r["responses"].get("preferred_tsp", {}).get("label") == "Cognizant"]
    profiles = []
    for r in pref_recs:
        ind = r["profile"].get("industry", {})
        sen = r["profile"].get("seniority", {})
        hq = r["profile"].get("hq_location", {})
        emp = r["profile"].get("emp_count", {})
        rev = r["profile"].get("revenue", {})
        q43 = r["responses"].get("q43", {})
        spend = r["responses"].get("ai_spend_current")
        s9_code = fam_lookup.get(r["record"], {}).get("Cognizant")
        cbs = cog_bs.get(r["record"], {})
        q1_sem = r2(cbs["q1_code"] - 4) if cbs.get("shown") and cbs.get("q1_code") is not None else None
        q27_int = r2(cbs["q27_code"] - 1) if cbs.get("shown") and cbs.get("q27_code") is not None else None

        profiles.append({
            "record": r["record"],
            "industry": ind.get("label") if ind else None,
            "seniority": sen.get("label") if sen else None,
            "functions": r["profile"].get("functions") or [],
            "hq_location": hq.get("label") if hq else None,
            "emp_count": emp.get("label") if emp else None,
            "revenue": rev.get("label") if rev else None,
            "q43_gap_label": q43.get("label") if q43 else None,
            "ai_spend_current": spend,
            "s9_cognizant_code": s9_code,
            "q1_semantic": q1_sem,
            "q27_intent": q27_int,
            "shown_in_battery": cbs.get("shown", False),
        })
    return {
        "query": "B4-06",
        "title": "Profile of Cognizant Q28 Primary Preference Selectors",
        "n": len(profiles),
        "records": profiles,
    }


# ===========================================================================
# B4-07: Cognizant current users — full profile
# ===========================================================================
def b4_07():
    user_recs = []
    for r in data:
        s9 = fam_lookup.get(r["record"], {}).get("Cognizant")
        if s9 == 1:
            user_recs.append(r)

    n_users = len(user_recs)

    # Industry, seniority, function, HQ, emp, revenue distributions
    ind_dist = Counter()
    sen_dist = Counter()
    func_dist = Counter()
    hq_dist = Counter()
    emp_dist = Counter()
    rev_dist = Counter()
    q43_scores_users = []
    spend_users = []
    shown_count = 0
    q1_vals_shown = []
    q27_vals_shown = []
    pref_count = 0

    for r in user_recs:
        ind_dist[r["profile"].get("industry", {}).get("label", "Unknown")] += 1
        sen_dist[r["profile"].get("seniority", {}).get("label", "Unknown")] += 1
        for f in (r["profile"].get("functions") or []):
            func_dist[f] += 1
        hq_dist[r["profile"].get("hq_location", {}).get("label", "Unknown")] += 1
        emp_dist[r["profile"].get("emp_count", {}).get("label", "Unknown")] += 1
        rev_dist[r["profile"].get("revenue", {}).get("label", "Unknown")] += 1

        q43 = r["responses"].get("q43", {})
        if q43 and q43.get("code") is not None:
            gs = Q43_SCORE.get(q43["code"])
            if gs is not None:
                q43_scores_users.append(gs)
        spend = r["responses"].get("ai_spend_current")
        if spend is not None:
            spend_users.append(spend)

        cbs = cog_bs.get(r["record"], {})
        if cbs.get("shown"):
            shown_count += 1
            if cbs.get("q1_code") is not None:
                q1_vals_shown.append(cbs["q1_code"] - 4)
            if cbs.get("q27_code") is not None:
                q27_vals_shown.append(cbs["q27_code"] - 1)

        if r["responses"].get("preferred_tsp", {}).get("label") == "Cognizant":
            pref_count += 1

    # Full-sample Q43 for reference
    full_q43 = [Q43_SCORE[r["responses"]["q43"]["code"]]
                for r in data if r["responses"].get("q43") and Q43_SCORE.get(r["responses"]["q43"].get("code")) is not None]
    full_spend = [r["responses"]["ai_spend_current"] for r in data if r["responses"].get("ai_spend_current") is not None]

    return {
        "query": "B4-07",
        "title": "Cognizant Current Users — Full Profile",
        "n_current_users": n_users,
        "industry_distribution": dict(sorted(ind_dist.items(), key=lambda x: -x[1])),
        "seniority_distribution": dict(sorted(sen_dist.items(), key=lambda x: -x[1])),
        "function_distribution": dict(sorted(func_dist.items(), key=lambda x: -x[1])),
        "hq_distribution": dict(sorted(hq_dist.items(), key=lambda x: -x[1])),
        "emp_count_distribution": dict(sorted(emp_dist.items(), key=lambda x: -x[1])),
        "revenue_distribution": dict(sorted(rev_dist.items(), key=lambda x: -x[1])),
        "q43_mean_users": r3(avg(q43_scores_users)),
        "q43_mean_full_sample": r3(avg(full_q43)),
        "median_spend_users": round(statistics.median(spend_users)) if spend_users else None,
        "mean_spend_users": round(avg(spend_users)) if spend_users else None,
        "median_spend_full_sample": round(statistics.median(full_spend)) if full_spend else None,
        "n_shown_in_battery": shown_count,
        "q1_mean_shown_users": r2(avg(q1_vals_shown)),
        "q27_mean_shown_users": r2(avg(q27_vals_shown)),
        "n_selected_as_q28_preference": pref_count,
    }


# ===========================================================================
# B4-08: Awareness-to-preference conversion rate — all 16 brands
# ===========================================================================
def b4_08():
    aware_n = Counter()
    pref_n = Counter()

    for r in data:
        for bf in r["profile"].get("brand_familiarity") or []:
            brand = bf.get("brand")
            code = bf.get("code")
            if brand and code is not None and code <= 5:
                aware_n[brand] += 1
        pt = r["responses"].get("preferred_tsp", {})
        if pt and pt.get("label"):
            pref_n[pt["label"]] += 1

    rows = []
    for brand in STUDY_BRANDS_16:
        aw = aware_n.get(brand, 0)
        pr = pref_n.get(brand, 0)
        conv = round(pr / aw * 100, 2) if aw > 0 else None
        rows.append({
            "brand": brand,
            "aware_n": aw,
            "aware_pct_of_600": round(aw / N * 100, 1),
            "pref_n": pr,
            "pref_pct_of_600": round(pr / N * 100, 1),
            "conversion_pct": conv,
        })
    rows.sort(key=lambda x: (x["conversion_pct"] is None, -(x["conversion_pct"] or 0)))
    return {
        "query": "B4-08",
        "title": "Awareness-to-Preference Conversion Rate — All 16 Brands",
        "rows": rows,
        "note": "Conversion = pref_n / aware_n. Sorted by conversion rate descending.",
    }


# ---------------------------------------------------------------------------
# Run all
# ---------------------------------------------------------------------------
r01 = b4_01()
r02 = b4_02()
r03 = b4_03()
r04 = b4_04()
r05 = b4_05()
r06 = b4_06()
r07 = b4_07()
r08 = b4_08()

all_results = [r01, r02, r03, r04, r05, r06, r07, r08]

# ---------------------------------------------------------------------------
# Print
# ---------------------------------------------------------------------------

# B4-01
sep("B4-01", r01["title"])
print(f"  {'Function':<55} {'n':>5}  {'Q1 sem':>7}  {'Q27 int':>8}")
print(f"  {'-'*80}")
for row in r01["rows"]:
    f_str = flag(row["n"])
    print(f"  {row['function']:<55} {row['n']:>5}  {(row['q1_semantic'] or 0):>7.2f}  {(row['q27_intent'] or 0):>8.2f}{f_str}")

# B4-02
sep("B4-02", r02["title"])
print(f"  {'Seniority':<65} {'n':>5}  {'Q1 sem':>7}  {'Q27 int':>8}")
print(f"  {'-'*90}")
for row in r02["rows"]:
    f_str = flag(row["n"])
    print(f"  {row['seniority']:<65} {row['n']:>5}  {(row['q1_semantic'] or 0):>7.2f}  {(row['q27_intent'] or 0):>8.2f}{f_str}")

# B4-03
sep("B4-03", r03["title"])
print(f"  {'Attribute':<35} {'Users n':>8} {'Users avg':>10}  {'NonUsr n':>9} {'NonUsr avg':>11}  {'Diff(U-NU)':>11}")
print(f"  {'-'*90}")
for row in r03["rows"]:
    d = row["diff_user_minus_nonuser"]
    d_str = f"{d:>+11.2f}" if d is not None else f"{'N/A':>11}"
    print(f"  {row['attribute']:<35} {row['users_n']:>8} {(row['users_avg'] or 0):>10.2f}  "
          f"{row['nonusers_n']:>9} {(row['nonusers_avg'] or 0):>11.2f}  {d_str}")
print(f"\n  Note: {r03['note']}")

# B4-04
sep("B4-04", r04["title"])
print(f"  {'Industry':<55} {'n':>4}  {'Aware%':>7}  {'Fam%':>6}  {'User%':>6}  {'Pref%':>6}")
print(f"  {'-'*90}")
for row in r04["rows"]:
    bflag = "  ⚠ below threshold" if row["below_threshold"] else ""
    print(f"  {row['industry']:<55} {row['n_industry']:>4}  {row['pct_aware']:>7.1f}%  "
          f"{row['pct_familiar']:>6.1f}%  {row['pct_current_user']:>6.1f}%  {row['pct_primary_pref']:>6.1f}%{bflag}")
print(f"\n  Note: {r04['note']}")

# B4-05
sep("B4-05", r05["title"])
print(f"  {'Industry':<55} {'n_eval':>7}  {'Q1 sem':>7}  {'Q27 int':>8}  {'Ind Q43':>8}")
print(f"  {'-'*93}")
for row in r05["rows"]:
    f_str = flag(row["n_cog_evaluators"], COG_EVAL_MIN_N)
    print(f"  {row['industry']:<55} {row['n_cog_evaluators']:>7}  {(row['q1_semantic'] or 0):>7.2f}  "
          f"{(row['q27_intent'] or 0):>8.2f}  {(row['industry_q43_mean'] or 0):>8.2f}{f_str}")
print(f"\n  Note: {r05['note']}")

# B4-06
sep("B4-06", r06["title"])
print(f"  n = {r06['n']} respondents selected Cognizant as primary Q28 preference\n")
for rec in r06["records"]:
    print(f"  Record: {rec['record']}")
    print(f"    Industry:      {rec['industry']}")
    print(f"    Seniority:     {rec['seniority']}")
    print(f"    Functions:     {', '.join(rec['functions'])}")
    print(f"    HQ location:   {rec['hq_location']}")
    print(f"    Emp count:     {rec['emp_count']}")
    print(f"    Revenue:       {rec['revenue']}")
    print(f"    Q43 gap:       {rec['q43_gap_label']}")
    spend = rec['ai_spend_current']
    print(f"    AI spend:      ${spend:,.0f}" if spend is not None else "    AI spend:      N/A")
    print(f"    S9 Cognizant:  code {rec['s9_cognizant_code']}")
    print(f"    Shown in battery: {rec['shown_in_battery']}")
    print(f"    Q1 semantic:   {rec['q1_semantic']}")
    print(f"    Q27 intent:    {rec['q27_intent']}")
    print()

# B4-07
sep("B4-07", r07["title"])
res = r07
print(f"  Total current users (S9=1): {res['n_current_users']}")
print(f"  Shown in battery:           {res['n_shown_in_battery']}/{res['n_current_users']}")
print(f"  Selected Q28 preference:    {res['n_selected_as_q28_preference']}/{res['n_current_users']}")
print()
print(f"  Q43 mean gap score — users: {res['q43_mean_users']}  vs full sample: {res['q43_mean_full_sample']}")
print(f"  AI spend — users median:  ${res['median_spend_users']:>12,.0f}  mean: ${res['mean_spend_users']:>12,.0f}")
print(f"  AI spend — full sample median: ${res['median_spend_full_sample']:>12,.0f}")
print()
print(f"  Shown-user Q1 avg:  {res['q1_mean_shown_users']}")
print(f"  Shown-user Q27 avg: {res['q27_mean_shown_users']}")
print()
print("  Industry distribution:")
for k, v in res["industry_distribution"].items():
    print(f"    {k:<55} {v:>4}")
print()
print("  Seniority distribution:")
for k, v in res["seniority_distribution"].items():
    print(f"    {k:<65} {v:>4}")
print()
print("  Function distribution (multi-select):")
for k, v in res["function_distribution"].items():
    print(f"    {k:<55} {v:>4}")
print()
print("  HQ location:")
for k, v in res["hq_distribution"].items():
    print(f"    {k:<65} {v:>4}")
print()
print("  Employee count:")
for k, v in res["emp_count_distribution"].items():
    print(f"    {k:<30} {v:>4}")
print()
print("  Revenue:")
for k, v in res["revenue_distribution"].items():
    print(f"    {k:<40} {v:>4}")

# B4-08
sep("B4-08", r08["title"])
print(f"  {'Brand':<48} {'Aware n':>8} {'Aware%':>7}  {'Pref n':>7} {'Pref%':>6}  {'Conv%':>7}  Cognizant?")
print(f"  {'-'*105}")
for row in r08["rows"]:
    is_cog = " <-- Cognizant" if row["brand"] == "Cognizant" else ""
    conv_str = f"{row['conversion_pct']:>7.2f}%" if row["conversion_pct"] is not None else f"{'N/A':>8}"
    print(f"  {row['brand']:<48} {row['aware_n']:>8} {row['aware_pct_of_600']:>7.1f}%  "
          f"{row['pref_n']:>7} {row['pref_pct_of_600']:>6.1f}%  {conv_str}{is_cog}")
print(f"\n  Note: {r08['note']}")

# ---------------------------------------------------------------------------
for res in all_results:
    output[res["query"]] = res

with open(OUTPUT_PATH, "w") as f:
    json.dump(output, f, indent=2)

bar = "=" * 70
print(f"\n{bar}")
print(f"All 8 queries complete. Written to {OUTPUT_PATH}")
print(f"File size: {os.path.getsize(OUTPUT_PATH):,} bytes")
