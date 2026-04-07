#!/usr/bin/env python3
"""
Batch 1 analytical queries — screener and demographic outputs.
Writes ~/avasta_batch1_screeners.json and prints to terminal.
"""

import json
import os
import statistics
from collections import Counter, defaultdict

RESPONDENTS_PATH = "data/respondents.json"
OUTPUT_PATH = os.path.expanduser("~/avasta_batch1_screeners.json")
N = 600

FICTITIOUS_BRAND = "Supercalifragilisticexpialidocious Incorporated"

STUDY_BRANDS_16 = {
    "Cognizant", "Accenture", "IBM Consulting", "Infosys", "Capgemini",
    "Wipro", "Tata Consultancy Services (TCS)", "EY", "HCL Technologies",
    "Deloitte", "McKinsey & Company", "Google (Cloud & Gemini)",
    "DXC Technology", "ServiceNow", "Microsoft (Azure & Copilot)",
    "Amazon Web Services (AWS)",
}

def pct(n, base=N):
    return round(n / base * 100, 1)

def fmt_row(label, count, base=N):
    return {"label": label, "n": count, "pct_of_600": pct(count, base)}

def normalize_label(s):
    """Strip non-breaking spaces and normalise whitespace."""
    if s is None:
        return None
    return s.replace("\xa0", " ").strip()

# ---------------------------------------------------------------------------

def run_queries(data):
    results = {}
    lines = []  # terminal output lines

    def header(code, title):
        h = f"\n{'='*60}\n=== {code}: {title} ===\n{'='*60}"
        lines.append(h)

    def row(label, count, base=N, extra=""):
        s = f"  {label:<55} {count:>5}  {pct(count,base):>5.1f}%{extra}"
        lines.append(s)

    def divider():
        lines.append(f"  {'-'*72}")

    # -----------------------------------------------------------------------
    # B1-01: S1 HQ Location
    # -----------------------------------------------------------------------
    header("B1-01", "S1 HQ Location distribution")
    counts = Counter(r["profile"]["hq_location"]["label"] for r in data
                     if r["profile"].get("hq_location"))
    rows = sorted(counts.items(), key=lambda x: -x[1])
    result = [fmt_row(l, c) for l, c in rows]
    for l, c in rows:
        row(l, c)
    results["B1-01"] = {"query": "S1 HQ Location", "n_base": N, "rows": result}

    # -----------------------------------------------------------------------
    # B1-02: S2 Employee count banded — in band order by code
    # -----------------------------------------------------------------------
    header("B1-02", "S2 Employee count (banded) distribution")
    emp_by_code = {}
    for r in data:
        ec = r["profile"].get("emp_count")
        if ec:
            emp_by_code.setdefault(ec["code"], {"label": ec["label"], "n": 0})
            emp_by_code[ec["code"]]["n"] += 1
    result = []
    for code in sorted(emp_by_code):
        l, c = emp_by_code[code]["label"], emp_by_code[code]["n"]
        row(l, c)
        result.append(fmt_row(l, c))
    results["B1-02"] = {"query": "S2 Employee count banded", "n_base": N, "rows": result}

    # -----------------------------------------------------------------------
    # B1-03: S3 Revenue — in band order by code
    # -----------------------------------------------------------------------
    header("B1-03", "S3 Revenue distribution")
    rev_by_code = {}
    for r in data:
        rv = r["profile"].get("revenue")
        if rv:
            rev_by_code.setdefault(rv["code"], {"label": rv["label"], "n": 0})
            rev_by_code[rv["code"]]["n"] += 1
    result = []
    for code in sorted(rev_by_code):
        l, c = rev_by_code[code]["label"], rev_by_code[code]["n"]
        row(l, c)
        result.append(fmt_row(l, c))
    results["B1-03"] = {"query": "S3 Revenue", "n_base": N, "rows": result}

    # -----------------------------------------------------------------------
    # B1-04: S6 Function distribution (multi-select)
    # -----------------------------------------------------------------------
    header("B1-04", "S6 Function distribution (multi-select)")
    func_counts = Counter()
    func_selection_counts = []
    for r in data:
        funcs = r["profile"].get("functions") or []
        func_selection_counts.append(len(funcs))
        for f in funcs:
            func_counts[f] += 1

    rows = sorted(func_counts.items(), key=lambda x: -x[1])
    result_rows = []
    lines.append(f"  {'Function':<55} {'n':>5}  {'% of 600':>8}")
    divider()
    for l, c in rows:
        row(l, c)
        result_rows.append(fmt_row(l, c))

    # Stats on selection count
    mn = min(func_selection_counts)
    mx = max(func_selection_counts)
    mean_ = round(statistics.mean(func_selection_counts), 2)
    median_ = statistics.median(func_selection_counts)
    lines.append(f"\n  Functions selected per respondent: min={mn}, max={mx}, mean={mean_}, median={median_}")
    results["B1-04"] = {
        "query": "S6 Function distribution",
        "n_base": N,
        "rows": result_rows,
        "functions_per_respondent": {"min": mn, "max": mx, "mean": mean_, "median": median_},
    }

    # -----------------------------------------------------------------------
    # B1-05: S11 AI adoption approach
    # -----------------------------------------------------------------------
    header("B1-05", "S11 AI adoption approach distribution")
    counts = Counter(r["profile"]["ai_adoption_approach"]["label"] for r in data
                     if r["profile"].get("ai_adoption_approach"))
    rows = sorted(counts.items(), key=lambda x: -x[1])
    result = [fmt_row(l, c) for l, c in rows]
    for l, c in rows:
        row(l, c)
    results["B1-05"] = {"query": "S11 AI adoption approach", "n_base": N, "rows": result}

    # -----------------------------------------------------------------------
    # B1-06: S12 TSP engagement plan
    # -----------------------------------------------------------------------
    header("B1-06", "S12 TSP engagement plan distribution")
    counts = Counter(r["profile"]["tsp_engagement_plan"]["label"] for r in data
                     if r["profile"].get("tsp_engagement_plan"))
    rows = sorted(counts.items(), key=lambda x: -x[1])
    result = [fmt_row(l, c) for l, c in rows]
    for l, c in rows:
        row(l, c)
    results["B1-06"] = {"query": "S12 TSP engagement plan", "n_base": N, "rows": result}

    # -----------------------------------------------------------------------
    # B1-07: Q47 Employee count self-reported (open numeric)
    # -----------------------------------------------------------------------
    header("B1-07", "Q47 Employee count self-reported distribution")
    vals = [r["profile"].get("employee_count_self_reported") for r in data]
    nums = [v for v in vals if v is not None]
    null_count = sum(1 for v in vals if v is None)

    mean_ = round(statistics.mean(nums), 1)
    median_ = statistics.median(nums)
    lines.append(f"  n non-null: {len(nums)}  |  null: {null_count}")
    lines.append(f"  min: {min(nums):,}  max: {max(nums):,}  mean: {mean_:,.1f}  median: {median_:,.0f}")
    lines.append("")

    bands = [
        ("<1,000",        lambda v: v < 1000),
        ("1,000–2,499",   lambda v: 1000 <= v <= 2499),
        ("2,500–4,999",   lambda v: 2500 <= v <= 4999),
        ("5,000–9,999",   lambda v: 5000 <= v <= 9999),
        ("10,000–49,999", lambda v: 10000 <= v <= 49999),
        ("50,000+",       lambda v: v >= 50000),
    ]
    band_rows = []
    for label, fn in bands:
        c = sum(1 for v in nums if fn(v))
        row(label, c)
        band_rows.append(fmt_row(label, c))
    lines.append(f"  null / not provided: {null_count}")

    results["B1-07"] = {
        "query": "Q47 Employee count self-reported",
        "n_non_null": len(nums), "n_null": null_count,
        "stats": {"min": int(min(nums)), "max": int(max(nums)), "mean": mean_, "median": float(median_)},
        "bands": band_rows,
    }

    # -----------------------------------------------------------------------
    # B1-08: Q48 Organisation age (code order: youngest → oldest)
    # -----------------------------------------------------------------------
    header("B1-08", "Q48 Organisation age distribution")
    q48_by_code = {}
    for r in data:
        q = r["responses"].get("q48")
        if q:
            q48_by_code.setdefault(q["code"], {"label": q["label"], "n": 0})
            q48_by_code[q["code"]]["n"] += 1
    result = []
    for code in sorted(q48_by_code):
        l, c = q48_by_code[code]["label"], q48_by_code[code]["n"]
        row(l, c)
        result.append(fmt_row(l, c))
    results["B1-08"] = {"query": "Q48 Organisation age", "n_base": N, "rows": result}

    # -----------------------------------------------------------------------
    # B1-09: Q49 Revenue change — grew most → shrank most → not sure
    # -----------------------------------------------------------------------
    header("B1-09", "Q49 Revenue growth over past 3 years")
    # Custom ordering: 5,4,3,2,1,6,7,8,9,10,11,12
    Q49_ORDER = [5, 4, 3, 2, 1, 6, 7, 8, 9, 10, 11, 12]
    q49_by_code = {}
    for r in data:
        q = r["responses"].get("q49")
        if q:
            q49_by_code.setdefault(q["code"], {"label": q["label"], "n": 0})
            q49_by_code[q["code"]]["n"] += 1
    result = []
    for code in Q49_ORDER:
        if code in q49_by_code:
            l, c = q49_by_code[code]["label"], q49_by_code[code]["n"]
            row(l, c)
            result.append(fmt_row(l, c))
    results["B1-09"] = {"query": "Q49 Revenue growth past 3 years", "n_base": N, "rows": result}

    # -----------------------------------------------------------------------
    # B1-10: Q50 Primary cloud environment
    # -----------------------------------------------------------------------
    header("B1-10", "Q50 Primary cloud environment")
    OTHER_RECORDS = {105: "IBM", 298: "Wipro", 750: "Accenture", 865: "IBM", 873: "Accenture"}
    q50_by_code = {}
    for r in data:
        q = r["responses"].get("q50")
        if q:
            q50_by_code.setdefault(q["code"], {"label": q["label"], "n": 0})
            q50_by_code[q["code"]]["n"] += 1
    rows = sorted(q50_by_code.items(), key=lambda x: -x[1]["n"])
    result = []
    for code, d in rows:
        flag = "  *** see note ***" if code == 5 else ""
        row(d["label"], d["n"], extra=flag)
        result.append({**fmt_row(d["label"], d["n"]), "note": "5 respondents entered TSP names (not cloud platforms)" if code == 5 else None})
    lines.append(f"\n  Other-specify entries (code 5): IBM ×2, Wipro ×1, Accenture ×2")
    lines.append(  "  (These respondents likely misread the question as asking about TSP, not cloud platform)")
    results["B1-10"] = {"query": "Q50 Primary cloud environment", "n_base": N, "rows": result,
                         "other_specify_note": OTHER_RECORDS}

    # -----------------------------------------------------------------------
    # B1-11: S8 Unaided brand awareness
    # -----------------------------------------------------------------------
    header("B1-11", "S8 Unaided brand awareness — top-of-mind frequency")

    total_mentions = Counter()
    first_mentions = Counter()
    brands_per_resp = Counter()
    unrecognized = Counter()

    for r in data:
        normalized = [b for b in (r["brand_awareness"].get("unaided_mentions") or [])
                      if b and b.strip()]
        brands_per_resp[len(normalized)] += 1
        for b in normalized:
            total_mentions[b] += 1
            if b not in STUDY_BRANDS_16:
                unrecognized[b] += 1

        # First mention: slot_1 from verbatims, normalized
        raw_slot1 = r["verbatims"].get("unaided_raw", {}).get("slot_1")
        if raw_slot1 and raw_slot1.strip():
            # Map raw slot1 to normalized form using the unaided_mentions list
            norm_map = {}
            raw_list = r["brand_awareness"].get("unaided_mentions_raw") or []
            norm_list = normalized
            for i, raw in enumerate(raw_list):
                if i < len(norm_list):
                    norm_map[raw.strip().lower()] = norm_list[i]
            norm_first = norm_map.get(raw_slot1.strip().lower(), raw_slot1.strip())
            first_mentions[norm_first] += 1

    # Total respondents with ≥1 mention
    resp_with_mention = sum(1 for r in data if (r["brand_awareness"].get("unaided_mentions") or []))

    lines.append(f"\n  Total respondents with ≥1 mention: {resp_with_mention}")
    lines.append(f"\n  Total mentions by brand (any position):")
    lines.append(f"  {'Brand':<48} {'Total':>6}  {'First':>6}")
    divider()

    all_brand_rows = []
    for brand, cnt in sorted(total_mentions.items(), key=lambda x: -x[1]):
        fm = first_mentions.get(brand, 0)
        study_flag = "" if brand in STUDY_BRANDS_16 else "  [non-study]"
        lines.append(f"  {brand:<48} {cnt:>6}  {fm:>6}{study_flag}")
        all_brand_rows.append({"brand": brand, "total_mentions": cnt, "first_mentions": fm,
                                "is_study_brand": brand in STUDY_BRANDS_16})

    lines.append(f"\n  Brands named per respondent:")
    dist_rows = []
    for k in sorted(brands_per_resp):
        c = brands_per_resp[k]
        lines.append(f"    {k} brand(s): {c} respondents ({pct(c):.1f}%)")
        dist_rows.append({"n_brands_named": k, "respondents": c, "pct_of_600": pct(c)})

    if unrecognized:
        lines.append(f"\n  Non-study-brand mentions (did not normalize to 1 of 16 study brands):")
        unrec_rows = []
        for b, c in sorted(unrecognized.items(), key=lambda x: -x[1]):
            lines.append(f"    {b}: {c}")
            unrec_rows.append({"brand": b, "count": c})
    else:
        unrec_rows = []
        lines.append(f"\n  All unaided mentions normalized to study brands (no unrecognized strings).")

    results["B1-11"] = {
        "query": "S8 Unaided brand awareness",
        "respondents_with_mention": resp_with_mention,
        "brand_frequency": all_brand_rows,
        "brands_per_respondent_distribution": dist_rows,
        "non_study_brand_mentions": unrec_rows,
    }

    # -----------------------------------------------------------------------
    # B1-12: S9 Aided brand familiarity — 6-code distribution per brand
    # -----------------------------------------------------------------------
    header("B1-12", "S9 Aided brand familiarity — 6-code distribution (16 real brands)")

    CODE_LABELS = {
        1: "c1: Currently using",
        2: "c2: Have used in the past",
        3: "c3: Currently considering",
        4: "c4: Familiar, never used",
        5: "c5: Heard name only",
        6: "c6: Never heard of",
    }

    brand_dist = {b: Counter() for b in STUDY_BRANDS_16}
    for r in data:
        for entry in (r["profile"].get("brand_familiarity") or []):
            b = entry.get("brand")
            if b and b != FICTITIOUS_BRAND and b in STUDY_BRANDS_16:
                code = entry.get("code")
                if code is not None:
                    brand_dist[b][code] += 1

    # Sort by total familiar % desc (c1+c2+c3+c4+c5)
    def familiar_pct(b):
        return sum(brand_dist[b][c] for c in [1,2,3,4,5]) / N * 100

    sorted_brands = sorted(STUDY_BRANDS_16, key=lambda b: -familiar_pct(b))

    lines.append(f"\n  {'Brand':<48} {'c1':>5} {'c2':>5} {'c3':>5} {'c4':>5} {'c5':>5} {'c6':>5}  {'Familiar%':>9}  {'Usr%':>6}  {'NHO%':>6}")
    divider()

    brand_rows = []
    for b in sorted_brands:
        d = brand_dist[b]
        c1,c2,c3,c4,c5,c6 = d[1],d[2],d[3],d[4],d[5],d[6]
        fam = c1+c2+c3+c4+c5
        usr = c1+c2
        nho = c6
        lines.append(
            f"  {b:<48} {c1:>5} {c2:>5} {c3:>5} {c4:>5} {c5:>5} {c6:>5}"
            f"  {pct(fam):>8.1f}%  {pct(usr):>5.1f}%  {pct(nho):>5.1f}%"
        )
        brand_rows.append({
            "brand": b,
            "c1_currently_using": c1, "c2_have_used": c2, "c3_considering": c3,
            "c4_familiar_never_used": c4, "c5_heard_name": c5, "c6_never_heard": c6,
            "familiar_n": fam, "familiar_pct": round(pct(fam), 1),
            "current_or_past_user_n": usr, "current_or_past_user_pct": round(pct(usr), 1),
            "never_heard_n": nho, "never_heard_pct": round(pct(nho), 1),
        })

    lines.append(f"\n  Columns: c1=Currently using | c2=Have used past | c3=Considering | c4=Familiar never used | c5=Heard name | c6=Never heard")
    lines.append(  "  Familiar% = c1+c2+c3+c4+c5 | Usr% = c1+c2 | NHO% = c6")
    results["B1-12"] = {"query": "S9 Aided brand familiarity", "n_base": N, "brands": brand_rows}

    # -----------------------------------------------------------------------
    # B1-13: Q7 AI priority direction
    # -----------------------------------------------------------------------
    header("B1-13", "Q7 AI priority direction (change in importance over 2 years)")

    PRIORITIES = [
        "Increasing productivity",
        "Enabling AI scaling",
        "Enabling agentic business processes, workflows and functions",
    ]
    DIR_SCORE_MAP = {
        "decrease significantly": 1, "decrease somewhat": 2,
        "stay the same": 3,
        "increase somewhat": 4, "increase significantly": 5,
    }
    DIR_ORDER = ["Decrease significantly", "Decrease somewhat", "Stay the same",
                 "Increase somewhat", "Increase significantly"]

    priority_data = {p: Counter() for p in PRIORITIES}
    for r in data:
        for item in (r["responses"].get("ai_priority_direction") or []):
            p = item.get("priority")
            if p in priority_data:
                label_norm = normalize_label(item.get("label", "")).lower()
                priority_data[p][label_norm] += 1

    result_priorities = []
    for p in PRIORITIES:
        dist = priority_data[p]
        total_scored = 0
        score_sum = 0
        code_counts = {}
        for raw_label, cnt in dist.items():
            score = DIR_SCORE_MAP.get(raw_label)
            if score:
                score_sum += score * cnt
                total_scored += cnt
                code_counts[raw_label.title()] = cnt

        avg_score = round(score_sum / total_scored, 3) if total_scored else None
        lines.append(f"\n  Priority: {p}")
        lines.append(f"  {'Response':<35} {'n':>5}  {'%':>6}  Score")
        divider()
        dir_rows = []
        for dl in DIR_ORDER:
            c = dist.get(dl.lower(), 0)
            score = DIR_SCORE_MAP.get(dl.lower(), "")
            lines.append(f"  {dl:<35} {c:>5}  {pct(c):>5.1f}%  ({score})")
            dir_rows.append({"label": dl, "score_value": score, "n": c, "pct_of_600": pct(c)})
        lines.append(f"  Average direction score: {avg_score} (1=Decrease sig. → 5=Increase sig.)")
        result_priorities.append({"priority": p, "distribution": dir_rows, "avg_score": avg_score})

    results["B1-13"] = {"query": "Q7 AI priority direction", "n_base": N, "priorities": result_priorities}

    # -----------------------------------------------------------------------
    # B1-14: Q10 AI capability evolution outlook
    # -----------------------------------------------------------------------
    header("B1-14", "Q10 AI capability evolution outlook")
    counts = Counter(r["responses"]["q10"]["label"] for r in data if r["responses"].get("q10"))
    rows = sorted(counts.items(), key=lambda x: -x[1])
    result = [fmt_row(l, c) for l, c in rows]
    for l, c in rows:
        row(l, c)
    results["B1-14"] = {"query": "Q10 AI capability evolution", "n_base": N, "rows": result}

    # -----------------------------------------------------------------------
    # B1-15: Q38 Formal AI budget declaration
    # -----------------------------------------------------------------------
    header("B1-15", "Q38 Formal AI budget declaration")
    counts = Counter(r["responses"]["q38"]["label"] for r in data if r["responses"].get("q38"))
    rows = sorted(counts.items(), key=lambda x: -x[1])
    result = [fmt_row(l, c) for l, c in rows]
    for l, c in rows:
        row(l, c)
    results["B1-15"] = {"query": "Q38 Formal AI budget declaration", "n_base": N, "rows": result}

    # -----------------------------------------------------------------------
    # B1-16: Q42 TSP market evolution expectations (multi-select)
    # -----------------------------------------------------------------------
    header("B1-16", "Q42 TSP market evolution expectations (multi-select)")
    option_counts = Counter()
    options_per_resp = []
    for r in data:
        opts = r["responses"].get("q42") or []
        options_per_resp.append(len(opts))
        for o in opts:
            option_counts[o] += 1

    rows = sorted(option_counts.items(), key=lambda x: -x[1])
    result_rows = []
    lines.append(f"  {'Option':<55} {'n':>5}  {'% of 600':>8}")
    divider()
    for l, c in rows:
        row(l, c)
        result_rows.append(fmt_row(l, c))

    avg_opts = round(statistics.mean(options_per_resp), 2)
    lines.append(f"\n  Avg options selected per respondent: {avg_opts}")
    results["B1-16"] = {
        "query": "Q42 TSP market evolution", "n_base": N, "rows": result_rows,
        "avg_options_per_respondent": avg_opts,
    }

    # -----------------------------------------------------------------------
    # B1-17: Q44 AI industry disruption outlook
    # -----------------------------------------------------------------------
    header("B1-17", "Q44 AI industry disruption outlook")
    counts = Counter(r["responses"]["q44"]["label"] for r in data if r["responses"].get("q44"))
    rows = sorted(counts.items(), key=lambda x: -x[1])
    result = [fmt_row(l, c) for l, c in rows]
    for l, c in rows:
        row(l, c)
    results["B1-17"] = {"query": "Q44 AI industry disruption", "n_base": N, "rows": result}

    # -----------------------------------------------------------------------
    # B1-18: Q45 Number of people involved in TSP decision (code order: 1→10+)
    # -----------------------------------------------------------------------
    header("B1-18", "Q45 Number of stakeholders involved in TSP hiring decision")
    q45_by_code = {}
    for r in data:
        q = r["responses"].get("q45")
        if q:
            q45_by_code.setdefault(q["code"], {"label": q["label"], "n": 0})
            q45_by_code[q["code"]]["n"] += 1
    result = []
    for code in sorted(q45_by_code):
        l, c = q45_by_code[code]["label"], q45_by_code[code]["n"]
        row(l, c)
        result.append(fmt_row(l, c))
    results["B1-18"] = {"query": "Q45 TSP decision stakeholders", "n_base": N, "rows": result}

    # -----------------------------------------------------------------------
    # B1-19: S6 functions × Q43 alignment gap cross-tab
    # -----------------------------------------------------------------------
    header("B1-19", "S6 functions × Q43 AI alignment gap cross-tab")

    Q43_SCORE = {1: 1.0, 2: 0.75, 3: 0.50, 4: 0.25, 5: 0.0}
    Q43_MOD_OR_GREATER = {3, 4, 5}  # Moderate, Large, Very large

    func_q43 = defaultdict(list)
    for r in data:
        funcs = r["profile"].get("functions") or []
        q43 = r["responses"].get("q43")
        if q43 and q43.get("code") is not None:
            score = Q43_SCORE.get(q43["code"])
            is_mod_plus = q43["code"] in Q43_MOD_OR_GREATER
            for f in funcs:
                func_q43[f].append((score, is_mod_plus))

    rows_data = []
    for func, pairs in func_q43.items():
        n = len(pairs)
        scores = [s for s, _ in pairs if s is not None]
        avg = round(statistics.mean(scores), 3) if scores else None
        mod_plus = sum(1 for _, m in pairs if m)
        mod_plus_pct = round(mod_plus / n * 100, 1) if n else 0
        rows_data.append({"function": func, "n": n, "avg_q43_score": avg,
                          "pct_moderate_or_greater_gap": mod_plus_pct})

    rows_data.sort(key=lambda x: -(x["avg_q43_score"] or 0))

    lines.append(f"\n  Q43 score: No gap=1.0, Small=0.75, Moderate=0.50, Large=0.25, Very large=0.0")
    lines.append(f"  {'Function':<48} {'n':>5}  {'AvgScore':>9}  {'Mod+Gap%':>9}")
    divider()
    for d in rows_data:
        lines.append(f"  {d['function']:<48} {d['n']:>5}  {d['avg_q43_score']:>9.3f}  {d['pct_moderate_or_greater_gap']:>8.1f}%")

    results["B1-19"] = {
        "query": "S6 functions × Q43 alignment gap",
        "scoring": "No gap=1.0, Small=0.75, Moderate=0.50, Large=0.25, Very large=0.0",
        "rows": rows_data,
    }

    # -----------------------------------------------------------------------
    # B1-20: S6 functions × Q28 primary brand preference cross-tab
    # -----------------------------------------------------------------------
    header("B1-20", "S6 functions × Q28 primary brand preference (functions n≥20)")

    func_tsp = defaultdict(list)
    for r in data:
        funcs = r["profile"].get("functions") or []
        pref = r["responses"].get("preferred_tsp")
        if pref and pref.get("label"):
            for f in funcs:
                func_tsp[f].append(pref["label"])

    result_funcs = []
    funcs_sorted = sorted(func_tsp.keys(), key=lambda f: -len(func_tsp[f]))

    for func in funcs_sorted:
        brands = func_tsp[func]
        n_func = len(brands)
        if n_func < 20:
            continue
        top3 = Counter(brands).most_common(3)
        lines.append(f"\n  {func} (n={n_func})")
        t3_rows = []
        for i, (brand, cnt) in enumerate(top3, 1):
            bp = round(cnt / n_func * 100, 1)
            lines.append(f"    {i}. {brand:<44} {cnt:>4}  {bp:>5.1f}% of function")
            t3_rows.append({"rank": i, "brand": brand, "n": cnt, "pct_of_function": bp})
        result_funcs.append({"function": func, "n": n_func, "top_3_brands": t3_rows})

    results["B1-20"] = {
        "query": "S6 functions × Q28 primary TSP preference",
        "note": "Functions with n≥20 only; % is share of respondents with that function tag",
        "functions": result_funcs,
    }

    return results, "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    with open(RESPONDENTS_PATH) as f:
        data = json.load(f)
    assert len(data) == N, f"Expected {N} records, got {len(data)}"

    results, terminal_output = run_queries(data)

    # Write JSON output
    with open(OUTPUT_PATH, "w") as f:
        json.dump(results, f, indent=2)

    # Print to terminal
    print(terminal_output)
    print(f"\n{'='*60}")
    print(f"Output written to: {OUTPUT_PATH}")
    print(f"Queries completed: {len(results)}")
    print(f"All {N} records confirmed intact.")


if __name__ == "__main__":
    main()
