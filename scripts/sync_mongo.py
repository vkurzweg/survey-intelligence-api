#!/usr/bin/env python3
"""
Sync the updated respondents.json into MongoDB insightops_v1.respondents.
Drops and re-inserts all documents (safe because JSON is the source of truth).
"""

import json
from pymongo import MongoClient
from bson import ObjectId

RESPONDENTS_PATH = "data/respondents.json"
MONGO_URI = "mongodb://localhost:27017/"
DB_NAME = "insightops_v1"

def main():
    with open(RESPONDENTS_PATH) as f:
        data = json.load(f)

    print(f"Loaded {len(data)} records from {RESPONDENTS_PATH}")

    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    db = client[DB_NAME]
    coll = db.respondents

    before_count = coll.count_documents({})
    print(f"MongoDB before: {before_count} documents")

    # Replace all documents using bulk replace
    from pymongo import ReplaceOne
    ops = []
    for doc in data:
        # Use string _id as-is
        ops.append(ReplaceOne({"_id": doc["_id"]}, doc, upsert=True))

    result = coll.bulk_write(ops, ordered=False)
    print(f"Bulk write result: matched={result.matched_count}, modified={result.modified_count}, upserted={result.upserted_count}")

    after_count = coll.count_documents({})
    print(f"MongoDB after: {after_count} documents")
    assert after_count == 600, f"Expected 600, got {after_count}"

    # Spot-check: verify a few fields
    sample = coll.find_one({"profile.unaided_brands": {"$exists": True}})
    print(f"\nSpot check — unaided_brands exists: {sample is not None}")
    sample2 = coll.find_one({"profile.brand_familiarity": {"$exists": True}})
    print(f"Spot check — brand_familiarity exists: {sample2 is not None}")
    sample3 = coll.find_one({"responses.respondent_segment": {"$exists": True}})
    print(f"Spot check — respondent_segment exists: {sample3 is not None}")
    sample4 = coll.find_one({"responses.ai_budget_planned": {"$exists": True}})
    print(f"Spot check — ai_budget_planned gone: {sample4 is None}")
    sample5 = coll.find_one({"responses.q52": {"$exists": True}})
    print(f"Spot check — q52 gone: {sample5 is None}")

    print("\nSync complete.")

if __name__ == "__main__":
    main()
