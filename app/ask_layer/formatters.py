"""
formatters.py — Response envelope construction for the ask-layer.
"""

from __future__ import annotations

from datetime import datetime, timezone


def build_envelope(
    intent_id:     str,
    merged_params: dict,
    raw_data:      list,
    n_base:        int,
    intent_def:    dict,
) -> dict:
    """
    Wrap raw MongoDB output in the standard response envelope.

    Compound _id dicts from $group stages are flattened into top-level keys.
    Internal helper fields (prefix '_') are stripped from each row.
    """
    data = [_clean_doc(row) for row in raw_data]

    envelope = {
        "intent": intent_id,
        "params": merged_params,
        "meta": {
            "generated_at":          datetime.now(timezone.utc).isoformat(),
            "n_respondents_in_base": n_base,
            "base_note":             intent_def.get("base_note", ""),
            "template":              intent_def["template"],
            "query_source":          intent_def.get("query_source", ""),
            "scale_note":            intent_def.get("scale_note", ""),
        },
        "data": data,
    }

    if not data:
        envelope["meta"]["warning"] = "no_results"

    return envelope


def _clean_doc(doc: dict) -> dict:
    """
    Recursively clean a MongoDB result document:
      - Flatten compound _id dicts into top-level keys.
      - Drop simple _id values (ObjectId or string — not useful in output).
      - Strip internal helper fields prefixed with '_'.
    """
    out: dict = {}
    for k, v in doc.items():
        if k == "_id":
            if isinstance(v, dict):
                # Flatten compound group _id into the row
                out.update(_clean_doc(v))
            # else: plain _id (ObjectId / string) — skip
        elif k.startswith("_"):
            # Internal pipeline helpers like _maturity_band, _is_current_user
            pass
        elif isinstance(v, dict):
            out[k] = _clean_doc(v)
        else:
            out[k] = v
    return out
