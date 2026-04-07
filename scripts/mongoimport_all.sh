#!/usr/bin/env bash
# =============================================================================
# mongoimport_all.sh — Load all four survey collections into MongoDB
#
# Required environment variables:
#   MONGODB_URI  MongoDB connection string
#   MONGODB_DB   Target database name (e.g. survey_intelligence)
#
# Usage:
#   export MONGODB_URI="mongodb+srv://..."
#   export MONGODB_DB="survey_intelligence"
#   bash scripts/mongoimport_all.sh
#
# Import order matters: codebook first (respondent ETL reads it downstream).
# =============================================================================

set -euo pipefail

# ── Resolve project root relative to this script ─────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
PROCESSED_DIR="${PROJECT_ROOT}/data"

# ── Validate environment variables ───────────────────────────────────────────
if [[ -z "${MONGODB_URI:-}" ]]; then
  echo "ERROR: MONGODB_URI is not set." >&2
  echo "       export MONGODB_URI=\"mongodb+srv://user:pass@cluster/\"" >&2
  exit 1
fi

if [[ -z "${MONGODB_DB:-}" ]]; then
  echo "ERROR: MONGODB_DB is not set." >&2
  echo "       export MONGODB_DB=\"survey_intelligence\"" >&2
  exit 1
fi

# ── Validate source files ─────────────────────────────────────────────────────
REQUIRED_FILES=(
  "${PROCESSED_DIR}/codebook.json"
  "${PROCESSED_DIR}/respondents.json"
  "${PROCESSED_DIR}/verbatims.json"
  "${PROCESSED_DIR}/import_batches.json"
)

for f in "${REQUIRED_FILES[@]}"; do
  if [[ ! -f "${f}" ]]; then
    echo "ERROR: Required file not found: ${f}" >&2
    echo "       Run the ETL first: python3 scripts/import_survey_data.py" >&2
    exit 1
  fi
done

# ── Validate mongoimport is available ────────────────────────────────────────
if ! command -v mongoimport &>/dev/null; then
  echo "ERROR: mongoimport not found. Install MongoDB Database Tools:" >&2
  echo "       https://www.mongodb.com/try/download/database-tools" >&2
  exit 1
fi

# ── Helper ────────────────────────────────────────────────────────────────────
import_collection() {
  local collection="$1"
  local file="$2"
  echo ""
  echo "  Importing ${collection} from $(basename "${file}") …"
  mongoimport \
    --uri        "${MONGODB_URI}" \
    --db         "${MONGODB_DB}" \
    --collection "${collection}" \
    --jsonArray  \
    --file       "${file}"
}

# ── Banner ────────────────────────────────────────────────────────────────────
echo "────────────────────────────────────────────────────────────"
echo "  Cognizant Survey Intelligence — MongoDB Import"
echo "────────────────────────────────────────────────────────────"
echo "  URI      : ${MONGODB_URI:0:40}…"
echo "  Database : ${MONGODB_DB}"
echo "  Source   : ${PROCESSED_DIR}"

# ── Import (codebook must be first) ──────────────────────────────────────────
import_collection "codebook"       "${PROCESSED_DIR}/codebook.json"
import_collection "respondents"    "${PROCESSED_DIR}/respondents.json"
import_collection "verbatims"      "${PROCESSED_DIR}/verbatims.json"
import_collection "import_batches" "${PROCESSED_DIR}/import_batches.json"

echo ""
echo "────────────────────────────────────────────────────────────"
echo "  Import complete."
echo "  Next: mongosh \"\${MONGODB_URI}\" --file scripts/create_indexes.js"
echo "────────────────────────────────────────────────────────────"
