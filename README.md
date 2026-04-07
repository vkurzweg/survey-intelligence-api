# survey-intelligence-api

A standalone FastAPI service that exposes the survey intelligence ask-layer as a REST API. It connects to a MongoDB database of survey respondents, verbatims, and codebook data, and returns structured JSON responses for a set of named analytical intents.

---

## Repo structure

```
survey-intelligence-api/
├── app/
│   ├── main.py               # FastAPI app, routes, MongoDB lifespan
│   └── ask_layer/
│       ├── ask.py            # Intent dispatcher — public ask() function
│       ├── formatters.py     # Response envelope builder
│       ├── query_templates.py # MongoDB aggregation pipeline builders
│       └── intents.json      # Intent registry (8 intents)
├── data/
│   ├── codebook.json         # Question/response code definitions
│   ├── import_batches.json   # Import provenance metadata
│   ├── verbatims.json        # Open-ended survey responses
│   └── respondents.json      # Full respondent profiles (57MB, git-ignored)
├── scripts/
│   ├── mongoimport_all.sh    # Load JSON files into MongoDB
│   ├── create_indexes.js     # Create MongoDB indexes after import
│   └── verify_import.js      # Verify collection counts and spot-check docs
├── Dockerfile
├── render.yaml
└── requirements.txt
```

---

## Local setup

**Requirements:** Python 3.11+, a running MongoDB instance (local or Atlas).

```bash
git clone <repo-url>
cd survey-intelligence-api

python -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
```

---

## Environment variables

Create a `.env` file at the project root (never committed):

```bash
MONGODB_URI=mongodb://localhost:27017
MONGODB_DB=survey_intelligence
```

For MongoDB Atlas:

```bash
MONGODB_URI=mongodb+srv://<user>:<password>@<cluster>.mongodb.net/
MONGODB_DB=survey_intelligence
```

| Variable | Required | Description |
|---|---|---|
| `MONGODB_URI` | Yes | Full MongoDB connection string |
| `MONGODB_DB` | Yes | Database name to connect to |

---

## How to run locally

```bash
source .venv/bin/activate
export MONGODB_URI="mongodb://localhost:27017"
export MONGODB_DB="survey_intelligence"

uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`.
Interactive docs (Swagger UI): `http://localhost:8000/docs`

---

## How to import data into MongoDB

Data files live in `data/`. Run the import:

```bash
export MONGODB_URI="mongodb://localhost:27017"
export MONGODB_DB="survey_intelligence"

bash scripts/mongoimport_all.sh
```

After import, create indexes:

```bash
mongosh "$MONGODB_URI" --file scripts/create_indexes.js
```

Verify the import:

```bash
mongosh "$MONGODB_URI" --file scripts/verify_import.js
```

> `respondents.json` is 57MB and git-ignored. Keep a copy locally or in external storage (S3, GCS) and copy it into `data/` before importing.

---

## How to deploy to Render

1. Push this repo to GitHub.
2. In the Render dashboard: **New → Web Service → connect your repo**.
3. Render will detect `render.yaml` automatically and use the `Dockerfile`.
4. Go to **Environment** and set the two secret variables:
   - `MONGODB_URI` — your Atlas connection string
   - `MONGODB_DB` — your database name
5. Deploy.

Render injects `PORT` automatically; the Dockerfile reads it via `$PORT`.

---

## Example API usage

### Check health

```bash
curl http://localhost:8000/health
```
```json
{"status": "ok", "db": "ok"}
```

### List available intents

```bash
curl http://localhost:8000/intents
```

Returns all 8 intents with descriptions, required params, and defaults.

### POST /ask — run an intent

```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"intent": "provider_perception", "params": {"focus_brand": "Cognizant"}}'
```

```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"intent": "unmet_needs", "params": {"keyword": "integration", "limit": 10}}'
```

```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"intent": "segment_profile", "params": {"focus_brand": "Cognizant", "segment_by": "industry"}}'
```

### GET /ask — convenience endpoint for quick testing

```bash
curl "http://localhost:8000/ask?intent=provider_momentum"
```

```bash
curl "http://localhost:8000/ask?intent=target_list&params=%7B%22focus_brand%22%3A%22Cognizant%22%7D"
```

### Response envelope

All `/ask` responses follow the same shape:

```json
{
  "intent": "provider_perception",
  "params": { "focus_brand": "Cognizant", ... },
  "meta": {
    "generated_at": "2026-03-31T12:00:00+00:00",
    "n_respondents_in_base": 412,
    "template": "attribute_unwind",
    "base_note": "...",
    "scale_note": "..."
  },
  "data": [ ... ]
}
```

### Available intents

| Intent | Description |
|---|---|
| `provider_perception` | Attribute ratings for one brand vs the field average |
| `provider_comparison` | Head-to-head attribute ratings between two brands |
| `provider_momentum` | TSP rating delta (now vs 2-year future) per brand |
| `segment_profile` | Purchase intent broken down by one profile dimension |
| `segment_difference` | Focus brand intent vs market average by segment |
| `unmet_needs` | Q17 open-ended verbatims with keyword/segment filters |
| `target_list` | Anonymised respondent profiles with high purchase intent |
| `white_space` | Not-answered attribute rates — unclaimed perception space |
