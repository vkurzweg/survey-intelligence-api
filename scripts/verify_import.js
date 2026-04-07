// =============================================================================
// verify_import.js — Post-import verification for survey_intelligence
//
// Run with:
//   mongosh "$MONGODB_URI/$MONGODB_DB" --file scripts/verify_import.js
//
// Exit behaviour:
//   Prints PASS / FAIL for each check.
//   Prints a final summary line: "ALL CHECKS PASSED" or "N CHECK(S) FAILED".
//   mongosh does not propagate a non-zero exit code from JS, so check the
//   final summary line in CI scripts:
//     mongosh ... | grep -q "ALL CHECKS PASSED"
// =============================================================================

let failures = 0;

function check(name, actual, expected) {
  if (actual === expected) {
    print("  ✓  " + name + "  →  " + actual);
  } else {
    print("  ✗  " + name + "  →  got " + actual + ", expected " + expected);
    failures++;
  }
}

function checkAtLeast(name, actual, minVal) {
  if (actual >= minVal) {
    print("  ✓  " + name + "  →  " + actual + " (≥ " + minVal + ")");
  } else {
    print("  ✗  " + name + "  →  got " + actual + ", expected ≥ " + minVal);
    failures++;
  }
}

function checkZero(name, actual) {
  check(name, actual, 0);
}

print("════════════════════════════════════════════════════════════");
print("  Cognizant Survey Intelligence — Import Verification");
print("  Database: " + db.getName());
print("════════════════════════════════════════════════════════════");

// ── 1. Collection counts ──────────────────────────────────────────────────────
print("");
print("── Collection counts ────────────────────────────────────────");

const nRespondents   = db.respondents.countDocuments();
const nVerbatims     = db.verbatims.countDocuments();
const nCodebook      = db.codebook.countDocuments();
const nBatches       = db.import_batches.countDocuments();

check("respondents count",   nRespondents, 600);
check("import_batches count", nBatches,    1);
checkAtLeast("verbatims count",  nVerbatims,  1791);   // Q17=561 + S8=1230
checkAtLeast("codebook count",   nCodebook,   25);     // V9 floor

// ── 2. V10 smoke tests (match ETL validation targets) ─────────────────────────
print("");
print("── V10 smoke tests (crosstab cross-checks) ──────────────────");

// S1_HQ code 1 = U.S. only headquarters
const s1hqCount = db.respondents.countDocuments({
  "profile.hq_location.code": 1
});
check("S1_HQ=1 (US HQ) count", s1hqCount, 259);

// Cognizant shown (brand_idx 1, pipedBrands gate = shown)
const cognizantShown = db.respondents.countDocuments({
  "brand_awareness.shown_brands": "Cognizant"
});
check("Cognizant shown count", cognizantShown, 333);

// Q24 Cognizant attribute 1 answered
const q24CognAttr1 = db.respondents.countDocuments({
  brand_scores: {
    $elemMatch: {
      brand:     "Cognizant",
      attribute_ratings: {
        $elemMatch: {
          attribute_idx:   1,
          response_status: "answered"
        }
      }
    }
  }
});
check("Q24 Cognizant attr_1 answered", q24CognAttr1, 141);

// ── 3. Verbatim question split ─────────────────────────────────────────────────
print("");
print("── Verbatim question split ──────────────────────────────────");

const q17Count = db.verbatims.countDocuments({ question_code: "Q17_UnmetNeeds" });
const s8Count  = db.verbatims.countDocuments({ question_code: "S8_Unaided" });
check("Q17 verbatims count", q17Count, 561);
check("S8 verbatims count",  s8Count,  1230);

// ── 4. Duplicate respondent UUID check ────────────────────────────────────────
print("");
print("── Duplicate respondent UUIDs ───────────────────────────────");

const dupPipeline = [
  { $group: { _id: "$_id", n: { $sum: 1 } } },
  { $match: { n: { $gt: 1 } } },
  { $count: "duplicates" }
];
const dupResult = db.respondents.aggregate(dupPipeline).toArray();
const dupCount  = dupResult.length > 0 ? dupResult[0].duplicates : 0;
checkZero("Duplicate respondent UUIDs", dupCount);

// ── 5. Brand_scores structure ─────────────────────────────────────────────────
print("");
print("── Brand_scores structure ───────────────────────────────────");

// Every respondent should have exactly 16 brand_scores entries
const wrongBrandCount = db.respondents.countDocuments({
  $expr: { $ne: [{ $size: "$brand_scores" }, 16] }
});
checkZero("Respondents with brand_scores ≠ 16 entries", wrongBrandCount);

// Every brand_scores entry should have exactly 12 attribute_ratings
const wrongAttrCount = db.respondents.aggregate([
  { $unwind: "$brand_scores" },
  {
    $match: {
      $expr: { $ne: [{ $size: "$brand_scores.attribute_ratings" }, 12] }
    }
  },
  { $count: "bad" }
]).toArray();
checkZero(
  "Brand_scores entries with attribute_ratings ≠ 12",
  wrongAttrCount.length > 0 ? wrongAttrCount[0].bad : 0
);

// Shown brands (those with shown: true) should have no not_shown attribute ratings
const shownWithNotShownAttr = db.respondents.aggregate([
  { $unwind: "$brand_scores" },
  { $match: { "brand_scores.shown": true } },
  {
    $match: {
      "brand_scores.attribute_ratings": {
        $elemMatch: { response_status: "not_shown" }
      }
    }
  },
  { $count: "bad" }
]).toArray();
checkZero(
  "Shown brands with not_shown attribute rating",
  shownWithNotShownAttr.length > 0 ? shownWithNotShownAttr[0].bad : 0
);

// Not-shown brands should have no answered attribute ratings
const notShownWithAnswered = db.respondents.aggregate([
  { $unwind: "$brand_scores" },
  { $match: { "brand_scores.shown": false } },
  {
    $match: {
      "brand_scores.attribute_ratings": {
        $elemMatch: { response_status: "answered" }
      }
    }
  },
  { $count: "bad" }
]).toArray();
checkZero(
  "Not-shown brands with answered attribute rating",
  notShownWithAnswered.length > 0 ? notShownWithAnswered[0].bad : 0
);

// ── 6. Import batch record ─────────────────────────────────────────────────────
print("");
print("── Import batch record ──────────────────────────────────────");

const batch = db.import_batches.findOne();
if (!batch) {
  print("  ✗  import_batches: no document found");
  failures++;
} else {
  check("batch status",               batch.status,                  "completed");
  check("batch respondents_inserted", batch.counts.respondents_inserted, 600);
  check("batch verbatims_inserted",   batch.counts.verbatims_inserted,   1791);
  check("batch errors",               batch.counts.errors,               0);
}

// ── Summary ───────────────────────────────────────────────────────────────────
print("");
print("════════════════════════════════════════════════════════════");
if (failures === 0) {
  print("  RESULT: ALL CHECKS PASSED");
} else {
  print("  RESULT: " + failures + " CHECK(S) FAILED — review output above");
}
print("════════════════════════════════════════════════════════════");
