// =============================================================================
// create_indexes.js — B-tree indexes for all four survey collections
//
// Run with:
//   mongosh "$MONGODB_URI/$MONGODB_DB" --file scripts/create_indexes.js
//
// Notes:
//   - All indexes are createIndex(), not createIndexes(), for clarity.
//   - Vector indexes (for embeddings in verbatims.analysis.embedding) are
//     deferred — create those via Atlas UI or Atlas CLI after embeddings are
//     populated by the downstream normalisation pass.
//   - background: true is ignored in MongoDB 4.2+ (all index builds are now
//     background), kept here for older driver compatibility.
// =============================================================================

// ── Helper ────────────────────────────────────────────────────────────────────
function ensureIndex(collection, spec, options) {
  const result = db[collection].createIndex(spec, options);
  print("  " + collection + "  " + JSON.stringify(spec) + "  →  " + result);
}

print("════════════════════════════════════════════════════════════");
print("  Creating indexes — database: " + db.getName());
print("════════════════════════════════════════════════════════════");

// ── codebook ──────────────────────────────────────────────────────────────────
// Primary lookup: variable_code (already _id, but explicit for driver queries)
ensureIndex("codebook", { variable_code: 1 }, { unique: true, name: "cb_variable_code" });
// Filter by question type
ensureIndex("codebook", { question_type: 1 }, { name: "cb_question_type" });

// ── respondents ───────────────────────────────────────────────────────────────
// _id is the uuid — already indexed.

// Profile segmentation (most common filter axes)
ensureIndex("respondents", { "profile.hq_location.code":          1 }, { name: "resp_hq" });
ensureIndex("respondents", { "profile.emp_count.code":            1 }, { name: "resp_emp_count" });
ensureIndex("respondents", { "profile.revenue.code":              1 }, { name: "resp_revenue" });
ensureIndex("respondents", { "profile.industry.code":             1 }, { name: "resp_industry" });
ensureIndex("respondents", { "profile.seniority.code":            1 }, { name: "resp_seniority" });
ensureIndex("respondents", { "profile.decision_involvement.code": 1 }, { name: "resp_decision" });

// Brand exposure lookup (used in brand_scores pipeline unwind + match)
ensureIndex("respondents",
  { "brand_awareness.shown_brands": 1 },
  { name: "resp_shown_brands" }
);
ensureIndex("respondents",
  { "brand_awareness.current_brands": 1 },
  { name: "resp_current_brands" }
);

// AI maturity (common cross-tab dimension)
ensureIndex("respondents",
  { "responses.ai_maturity.code": 1 },
  { name: "resp_ai_maturity" }
);

// Import batch (for re-import / diff queries)
ensureIndex("respondents",
  { "_provenance.import_batch_id": 1 },
  { name: "resp_batch_id" }
);

// ── verbatims ─────────────────────────────────────────────────────────────────
// Lookup by respondent
ensureIndex("verbatims", { respondent_uuid: 1 }, { name: "verb_respondent" });

// Filter by question (Q17 vs S8)
ensureIndex("verbatims", { question_code: 1 }, { name: "verb_question_code" });

// Compound: question + slot (S8 slot-level queries)
ensureIndex("verbatims",
  { question_code: 1, slot: 1 },
  { name: "verb_question_slot" }
);

// Snapshot segment filters (join-free — respondent_snapshot is denormalised)
ensureIndex("verbatims",
  { "respondent_snapshot.industry":   1 },
  { name: "verb_snap_industry" }
);
ensureIndex("verbatims",
  { "respondent_snapshot.seniority":  1 },
  { name: "verb_snap_seniority" }
);
ensureIndex("verbatims",
  { "respondent_snapshot.emp_count":  1 },
  { name: "verb_snap_emp_count" }
);

// Analysis flags (post-normalisation queries)
ensureIndex("verbatims",
  { "analysis.resolved_brand":    1 },
  { name: "verb_resolved_brand" }
);
ensureIndex("verbatims",
  { "analysis.flagged":           1 },
  { name: "verb_flagged" }
);

// Import batch
ensureIndex("verbatims",
  { "_provenance.import_batch_id": 1 },
  { name: "verb_batch_id" }
);

// ── import_batches ────────────────────────────────────────────────────────────
// _id is the batch_id.  One supplementary index for status queries.
ensureIndex("import_batches", { status: 1 }, { name: "ib_status" });
ensureIndex("import_batches", { started_at: -1 }, { name: "ib_started_at_desc" });

print("════════════════════════════════════════════════════════════");
print("  Done. Deferred: vector index on verbatims.analysis.embedding");
print("  (create via Atlas UI or Atlas CLI after embeddings are populated)");
print("════════════════════════════════════════════════════════════");
