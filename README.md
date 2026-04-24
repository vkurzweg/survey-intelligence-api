# Survey Intelligence API (InsightOps)

A small FastAPI service for working with enterprise AI survey data.

The goal is simple: make the data usable.

This sits between the raw survey and the work that depends on it—analysis, charts, decks—so the same question returns the same answer, every time, and can be traced back to the underlying data.

---

## Overview

This allows you to:

- Run the same analysis consistently (instead of rebuilding it in Excel)
- Tie outputs directly back to survey questions and data
- Reuse common patterns (brand comparisons, segmentation)
- Produce outputs that drop cleanly into decks and briefs

Insights should be consistent, explainable and traceable back to the data.

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

## Data model (high level)

Each respondent includes:

- **Profile**  
  Industry, company size, seniority

- **Brand awareness**  
  Familiarity and usage across providers

- **Brand scores (per brand)**  
  - performance ratings (Q1–Q3)  
  - category perception (Q20)  
  - attribute ratings (Q24)  
  - rankings over time (Q25–Q26)  
  - purchase intent (Q27)

- **Verbatims**  
  Open-ended responses with source tracking

---

## Additional data outputs

In addition to the core dataset, this repo includes a set of derived files used for analysis:

- `brand_words.csv`  
  Terms most associated with each brand

- `corpus_words.csv`  
  Overall language patterns across all responses

- `brand_salience.csv`  
  Relative visibility and association strength by brand

- `response_tiers.csv`  
  Groupings used to segment respondents for analysis

These are working files — used to support analysis, not treated as source data.

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

---

## Context

This project was built as part of a broader effort to turn survey data into a reusable “analysis layer” for marketing, strategy, and thought leadership work.

It’s designed to support:
- internal analysis
- executive narratives
- campaign and content development
