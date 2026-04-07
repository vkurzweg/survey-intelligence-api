"""
ask.py — Intent dispatcher for the survey intelligence ask-layer.

Public API
──────────
    ask(intent_id, params, db)  →  response envelope (dict)

Usage
─────
    from pymongo import MongoClient
    from app.ask_layer.ask import ask

    db = MongoClient(MONGODB_URI)[MONGODB_DB]
    result = ask("provider_perception", {"segment_industry_codes": [11]}, db)

Errors
──────
    UnknownIntentError       intent_id not in registry
    MissingRequiredParamError  a required param is absent or null
"""

from __future__ import annotations

import json
from pathlib import Path

from . import query_templates as qt
from .formatters import build_envelope

# ── Load intent registry ───────────────────────────────────────────────────────

_REGISTRY_PATH = Path(__file__).parent / "intents.json"
INTENTS: dict = json.loads(_REGISTRY_PATH.read_text(encoding="utf-8"))

# ── Template dispatch table ────────────────────────────────────────────────────

_TEMPLATE_FNS: dict = {
    "attribute_unwind":       qt.attribute_unwind,
    "performance_trajectory": qt.performance_trajectory,
    "brand_segment_metric":   qt.brand_segment_metric,
    "verbatim_fetch":         qt.verbatim_fetch,
    "respondent_list":        qt.respondent_list,
}


# ── Errors ─────────────────────────────────────────────────────────────────────

class UnknownIntentError(ValueError):
    pass


class MissingRequiredParamError(ValueError):
    pass


# ── Public function ────────────────────────────────────────────────────────────

def ask(intent_id: str, params: dict | None, db) -> dict:
    """
    Execute a named intent against the survey MongoDB database.

    Args:
        intent_id : One of the 8 registered intents (see intents.json).
        params    : Optional overrides merged over intent defaults. Pass None or {}
                    to use all defaults.
        db        : A pymongo Database object.

    Returns:
        Standard response envelope:
        { "intent", "params", "meta": { generated_at, n_respondents_in_base,
          base_note, template, query_source, scale_note }, "data": [...] }

    Raises:
        UnknownIntentError         if intent_id is not registered.
        MissingRequiredParamError  if a required param is null or missing.
    """
    # ── Validate intent ────────────────────────────────────────────────────────
    if intent_id not in INTENTS:
        raise UnknownIntentError(
            f"Unknown intent: '{intent_id}'. "
            f"Valid intents: {sorted(INTENTS)}"
        )

    intent_def = INTENTS[intent_id]

    # ── Merge params: defaults → caller overrides → static template params ─────
    #    Static template_params always win; they encode the intent's fixed behaviour
    #    (e.g. mode="gap_vs_field") and must not be overridden by the caller.
    merged: dict = {
        **intent_def["default_params"],
        **(params or {}),
        **intent_def.get("template_params", {}),
    }

    # ── Validate required params ───────────────────────────────────────────────
    for rp in intent_def.get("required_params", []):
        if not merged.get(rp):
            raise MissingRequiredParamError(
                f"Intent '{intent_id}' requires param: '{rp}'"
            )

    # ── Build pipeline ─────────────────────────────────────────────────────────
    template_fn = _TEMPLATE_FNS[intent_def["template"]]
    pipeline    = template_fn(merged)

    # ── Count respondent base (before unwind / brand filter) ───────────────────
    seg_filter = qt.build_segment_filter(merged)
    n_base     = db.respondents.count_documents(seg_filter if seg_filter else {})

    # ── Execute ────────────────────────────────────────────────────────────────
    collection = intent_def["collection"]
    raw        = list(db[collection].aggregate(pipeline))

    # ── Format and return ──────────────────────────────────────────────────────
    return build_envelope(
        intent_id    = intent_id,
        merged_params= merged,
        raw_data     = raw,
        n_base       = n_base,
        intent_def   = intent_def,
    )
