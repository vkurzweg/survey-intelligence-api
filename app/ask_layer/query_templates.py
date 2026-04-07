"""
query_templates.py — Pre-built MongoDB aggregation pipelines for the ask-layer.

Each public function accepts a merged params dict and returns a plain list
(MongoDB aggregation pipeline). No database connection here — pure data structures.

Templates
─────────
  attribute_unwind        Double-unwind brand_scores + attribute_ratings.
                          mode="gap_vs_field" | "ratings" | "uncertainty"
  performance_trajectory  Now vs 2yr-future TSP rating delta per brand.
  brand_segment_metric    Purchase intent by profile segment dimension.
  verbatim_fetch          Q17 unmet-needs verbatims with segment + keyword filters.
  respondent_list         Anonymised respondent profiles above an intent threshold.
"""

from __future__ import annotations

# ── Shared helper ──────────────────────────────────────────────────────────────

def build_segment_filter(params: dict) -> dict:
    """
    Build a $match-compatible filter dict from standard segment params.
    Always apply this filter BEFORE the first $unwind for efficiency.
    """
    f: dict = {}
    if params.get("segment_industry_codes"):
        f["profile.industry.code"] = {"$in": params["segment_industry_codes"]}
    if params.get("segment_emp_codes"):
        f["profile.emp_count.code"] = {"$in": params["segment_emp_codes"]}
    if params.get("segment_seniority_codes"):
        f["profile.seniority.code"] = {"$in": params["segment_seniority_codes"]}
    if params.get("maturity_min") is not None:
        f.setdefault("responses.ai_maturity.code", {})["$gte"] = params["maturity_min"]
    if params.get("maturity_max") is not None:
        f.setdefault("responses.ai_maturity.code", {})["$lte"] = params["maturity_max"]
    return f


# ── Template 1: attribute_unwind ───────────────────────────────────────────────

def attribute_unwind(params: dict) -> list:
    """
    Double-unwind brand_scores → attribute_ratings on the respondents collection.

    mode="gap_vs_field"
        Focus brand avg vs all-brand average per attribute.
        Returns: attribute, focus_avg, field_avg, gap_vs_field, focus_n.
        Sorted: gap_vs_field descending (strengths first).

    mode="ratings"
        If competitor_brand is set: pivot to two-brand side-by-side with gap column.
        If only focus_brand: per-attribute avg + pct_positive + pct_negative.
        Sorted: attribute_idx ascending.

    mode="uncertainty"
        Not-answered count and pct_not_answered per brand × attribute.
        focus_brand filters to one brand; null = all brands.
        Sorted: pct_not_answered descending.
    """
    mode        = params.get("mode", "ratings")
    focus       = params.get("focus_brand")
    competitor  = params.get("competitor_brand")
    seg_filter  = build_segment_filter(params)

    pipeline: list = []

    if seg_filter:
        pipeline.append({"$match": seg_filter})

    # Brand filter for the unwind stage
    brand_match: dict = {"brand_scores.shown": True}
    if mode == "ratings" and competitor:
        brand_match["brand_scores.brand"] = {"$in": [focus, competitor]}
    elif mode == "ratings" and focus:
        brand_match["brand_scores.brand"] = focus
    elif mode == "uncertainty" and focus:
        brand_match["brand_scores.brand"] = focus
    # gap_vs_field and uncertainty (no focus) need all brands — no extra filter

    pipeline += [
        {"$unwind": "$brand_scores"},
        {"$match": brand_match},
        {"$unwind": "$brand_scores.attribute_ratings"},
    ]

    if mode == "gap_vs_field":
        # ── Stage: filter answered ────────────────────────────────────────────
        pipeline.append({
            "$match": {"brand_scores.attribute_ratings.response_status": "answered"}
        })
        # ── Stage: group by brand × attribute ────────────────────────────────
        pipeline.append({"$group": {
            "_id": {
                "brand":         "$brand_scores.brand",
                "attribute":     "$brand_scores.attribute_ratings.attribute",
                "attribute_idx": "$brand_scores.attribute_ratings.attribute_idx",
            },
            "n":         {"$sum": 1},
            "avg_value": {"$avg": "$brand_scores.attribute_ratings.value"},
        }})
        # ── Stage: pivot to focus vs field per attribute ──────────────────────
        pipeline.append({"$group": {
            "_id": {
                "attribute":     "$_id.attribute",
                "attribute_idx": "$_id.attribute_idx",
            },
            "focus_avg": {
                "$max": {"$cond": [
                    {"$eq": ["$_id.brand", focus]},
                    {"$round": ["$avg_value", 3]},
                    None,
                ]}
            },
            "field_avg": {"$avg": "$avg_value"},
            "focus_n": {
                "$max": {"$cond": [
                    {"$eq": ["$_id.brand", focus]},
                    "$n",
                    None,
                ]}
            },
        }})
        pipeline.append({"$addFields": {
            "gap_vs_field": {"$round": [{"$subtract": ["$focus_avg", "$field_avg"]}, 3]},
            "focus_avg":    {"$round": ["$focus_avg", 3]},
            "field_avg":    {"$round": ["$field_avg", 3]},
        }})
        pipeline.append({"$sort": {"gap_vs_field": -1}})

    elif mode == "ratings":
        pipeline.append({
            "$match": {"brand_scores.attribute_ratings.response_status": "answered"}
        })
        pipeline.append({"$group": {
            "_id": {
                "brand":         "$brand_scores.brand",
                "attribute":     "$brand_scores.attribute_ratings.attribute",
                "attribute_idx": "$brand_scores.attribute_ratings.attribute_idx",
            },
            "n":            {"$sum": 1},
            "avg_value":    {"$avg": "$brand_scores.attribute_ratings.value"},
            "pct_positive": {
                "$avg": {"$cond": [
                    {"$gt": ["$brand_scores.attribute_ratings.value", 0]}, 1, 0
                ]}
            },
            "pct_negative": {
                "$avg": {"$cond": [
                    {"$lt": ["$brand_scores.attribute_ratings.value", 0]}, 1, 0
                ]}
            },
        }})
        pipeline.append({"$addFields": {
            "avg_value":    {"$round": ["$avg_value", 3]},
            "pct_positive": {"$round": [{"$multiply": ["$pct_positive", 100]}, 1]},
            "pct_negative": {"$round": [{"$multiply": ["$pct_negative", 100]}, 1]},
        }})

        if competitor:
            # ── Pivot to side-by-side gap view ────────────────────────────────
            pipeline.append({"$group": {
                "_id": {
                    "attribute":     "$_id.attribute",
                    "attribute_idx": "$_id.attribute_idx",
                },
                "focus_avg": {
                    "$max": {"$cond": [
                        {"$eq": ["$_id.brand", focus]}, "$avg_value", None
                    ]}
                },
                "competitor_avg": {
                    "$max": {"$cond": [
                        {"$eq": ["$_id.brand", competitor]}, "$avg_value", None
                    ]}
                },
                "focus_n":      {"$max": {"$cond": [{"$eq": ["$_id.brand", focus]},      "$n", None]}},
                "competitor_n": {"$max": {"$cond": [{"$eq": ["$_id.brand", competitor]}, "$n", None]}},
            }})
            pipeline.append({"$addFields": {
                "gap": {"$round": [{"$subtract": ["$focus_avg", "$competitor_avg"]}, 3]}
            }})
        pipeline.append({"$sort": {"_id.attribute_idx": 1}})

    else:  # mode == "uncertainty"
        # ── No response_status filter — count everything ──────────────────────
        pipeline.append({"$group": {
            "_id": {
                "brand":         "$brand_scores.brand",
                "attribute":     "$brand_scores.attribute_ratings.attribute",
                "attribute_idx": "$brand_scores.attribute_ratings.attribute_idx",
            },
            "total": {"$sum": 1},
            "not_answered": {
                "$sum": {"$cond": [
                    {"$eq": ["$brand_scores.attribute_ratings.response_status", "not_answered"]},
                    1, 0,
                ]}
            },
        }})
        pipeline.append({"$addFields": {
            "pct_not_answered": {
                "$round": [
                    {"$multiply": [{"$divide": ["$not_answered", "$total"]}, 100]},
                    1,
                ]
            }
        }})
        pipeline.append({"$sort": {"pct_not_answered": -1}})

    return pipeline


# ── Template 2: performance_trajectory ────────────────────────────────────────

def performance_trajectory(params: dict) -> list:
    """
    Unwinds shown brand_scores; computes average TSP rating now vs 2-year-future
    and the delta (momentum) per brand. Sorted by momentum descending.
    """
    seg_filter = build_segment_filter(params)
    pipeline: list = []

    if seg_filter:
        pipeline.append({"$match": seg_filter})

    pipeline += [
        {"$unwind": "$brand_scores"},
        {"$match": {
            "brand_scores.shown": True,
            "brand_scores.tsp_rating_now.response_status":         "answered",
            "brand_scores.tsp_rating_2yrs_future.response_status": "answered",
        }},
        {"$group": {
            "_id":               "$brand_scores.brand",
            "n":                 {"$sum": 1},
            "avg_rating_now":    {"$avg": "$brand_scores.tsp_rating_now.code"},
            "avg_rating_future": {"$avg": "$brand_scores.tsp_rating_2yrs_future.code"},
        }},
        {"$addFields": {
            "avg_rating_now":    {"$round": ["$avg_rating_now",    3]},
            "avg_rating_future": {"$round": ["$avg_rating_future", 3]},
            "momentum":          {"$round": [
                {"$subtract": ["$avg_rating_future", "$avg_rating_now"]}, 3
            ]},
        }},
        {"$sort": {"momentum": -1}},
    ]
    return pipeline


# ── Template 3: brand_segment_metric ──────────────────────────────────────────

# Maps segment_by value to (mongo_field_expr, computed_add_fields_expr_or_None)
_SEGMENT_MAP: dict[str, tuple] = {
    "industry":           ("$profile.industry.label",           None),
    "emp_count":          ("$profile.emp_count.label",          None),
    "seniority":          ("$profile.seniority.label",          None),
    "decision_involvement": ("$profile.decision_involvement.label", None),
    "maturity_band": (
        "$_maturity_band",
        {"$switch": {
            "branches": [
                {"case": {"$lte": ["$responses.ai_maturity.code", 3]}, "then": "Low (1–3)"},
                {"case": {"$lte": ["$responses.ai_maturity.code", 6]}, "then": "Mid (4–6)"},
            ],
            "default": "High (7–10)",
        }},
    ),
}


def brand_segment_metric(params: dict) -> list:
    """
    Unwinds shown brand_scores; groups purchase intent by one profile dimension.

    market_compare=False  Filter to focus_brand; return one row per segment value.
    market_compare=True   Include all brands; second-group to focus vs market avg.

    segment_by: "industry" | "emp_count" | "seniority" | "maturity_band"
                | "decision_involvement"
    """
    focus_brand  = params.get("focus_brand", "Cognizant")
    segment_by   = params.get("segment_by", "industry")
    market_cmp   = params.get("market_compare", False)
    threshold    = params.get("high_intent_threshold", 5)
    seg_filter   = build_segment_filter(params)

    seg_field_expr, seg_computed = _SEGMENT_MAP.get(
        segment_by, ("$profile.industry.label", None)
    )

    pipeline: list = []

    if seg_filter:
        pipeline.append({"$match": seg_filter})

    # Compute maturity_band before unwind so it's available on the respondent doc
    if seg_computed is not None:
        pipeline.append({"$addFields": {"_maturity_band": seg_computed}})

    brand_match: dict = {
        "brand_scores.shown": True,
        "brand_scores.purchase_intent.response_status": "answered",
    }
    if not market_cmp:
        brand_match["brand_scores.brand"] = focus_brand

    pipeline += [
        {"$unwind": "$brand_scores"},
        {"$match": brand_match},
    ]

    group_id: dict = {"segment": seg_field_expr}
    if market_cmp:
        group_id["brand"] = "$brand_scores.brand"

    pipeline.append({"$group": {
        "_id": group_id,
        "n":               {"$sum": 1},
        "avg_intent_code": {"$avg": "$brand_scores.purchase_intent.code"},
        "pct_high_intent": {
            "$avg": {"$cond": [
                {"$gte": ["$brand_scores.purchase_intent.code", threshold]}, 1, 0
            ]}
        },
    }})
    pipeline.append({"$addFields": {
        "avg_intent_code": {"$round": ["$avg_intent_code", 3]},
        "pct_high_intent": {"$round": [{"$multiply": ["$pct_high_intent", 100]}, 1]},
    }})

    if market_cmp:
        # Second group: pivot focus brand vs market average side-by-side
        pipeline.append({"$group": {
            "_id": "$_id.segment",
            "focus_avg": {
                "$max": {"$cond": [
                    {"$eq": ["$_id.brand", focus_brand]}, "$avg_intent_code", None
                ]}
            },
            "market_avg": {"$avg": "$avg_intent_code"},
            "focus_n": {
                "$max": {"$cond": [
                    {"$eq": ["$_id.brand", focus_brand]}, "$n", None
                ]}
            },
        }})
        pipeline.append({"$addFields": {
            "focus_avg":  {"$round": ["$focus_avg",  3]},
            "market_avg": {"$round": ["$market_avg", 3]},
            "gap": {"$round": [{"$subtract": ["$focus_avg", "$market_avg"]}, 3]},
        }})
        pipeline.append({"$sort": {"gap": -1}})
    else:
        pipeline.append({"$sort": {"avg_intent_code": -1}})

    return pipeline


# ── Template 4: verbatim_fetch ─────────────────────────────────────────────────

def verbatim_fetch(params: dict) -> list:
    """
    Aggregation on the verbatims collection.
    Returns Q17_UnmetNeeds verbatims matching segment + keyword filters.
    Sorted by char_count descending (richest responses first).
    """
    match: dict = {"question_code": "Q17_UnmetNeeds"}

    if params.get("segment_industry_codes"):
        match["respondent_snapshot.industry"] = {"$in": params["segment_industry_codes"]}
    if params.get("segment_seniority_codes"):
        match["respondent_snapshot.seniority"] = {"$in": params["segment_seniority_codes"]}
    if params.get("maturity_min") is not None:
        match["respondent_snapshot.ai_maturity_code"] = {"$gte": params["maturity_min"]}
    if params.get("keyword"):
        match["text"] = {"$regex": params["keyword"], "$options": "i"}

    limit = int(params.get("limit") or 50)

    return [
        {"$match": match},
        {"$project": {
            "_id":            0,
            "respondent_uuid": 1,
            "text":           1,
            "word_count":     1,
            "char_count":     1,
            "respondent_snapshot.industry_label":  1,
            "respondent_snapshot.seniority_label":  1,
            "respondent_snapshot.emp_count_label":  1,
            "respondent_snapshot.ai_maturity_code": 1,
        }},
        {"$sort":  {"char_count": -1}},
        {"$limit": limit},
    ]


# ── Template 5: respondent_list ────────────────────────────────────────────────

def respondent_list(params: dict) -> list:
    """
    Match respondents showing high purchase intent for focus_brand.
    Optionally restricts to current users of competitor_brand (displacement targeting).
    Returns anonymised profile fields only — no PII in the dataset.
    """
    focus_brand  = params.get("focus_brand", "Cognizant")
    competitor   = params.get("competitor_brand")
    threshold    = int(params.get("high_intent_threshold") or 5)
    limit        = int(params.get("limit") or 50)
    seg_filter   = build_segment_filter(params)

    pre_match: dict = {}
    if seg_filter:
        pre_match.update(seg_filter)
    if competitor:
        pre_match["brand_awareness.current_brands"] = competitor

    pipeline: list = []
    if pre_match:
        pipeline.append({"$match": pre_match})

    pipeline += [
        {"$unwind": "$brand_scores"},
        {"$match": {
            "brand_scores.brand":  focus_brand,
            "brand_scores.shown":  True,
            "brand_scores.purchase_intent.response_status": "answered",
            "brand_scores.purchase_intent.code": {"$gte": threshold},
        }},
        {"$addFields": {
            "_is_current_user": {"$in": [focus_brand, "$brand_awareness.current_brands"]}
        }},
        {"$project": {
            "_id":                  1,
            "industry":             "$profile.industry.label",
            "emp_count":            "$profile.emp_count.label",
            "revenue":              "$profile.revenue.label",
            "seniority":            "$profile.seniority.label",
            "decision_involvement": "$profile.decision_involvement.label",
            "functions":            "$profile.functions",
            "ai_maturity_code":     "$responses.ai_maturity.code",
            "purchase_intent_code": "$brand_scores.purchase_intent.code",
            "is_current_user":      "$_is_current_user",
        }},
        {"$sort":  {"purchase_intent_code": -1}},
        {"$limit": limit},
    ]
    return pipeline
