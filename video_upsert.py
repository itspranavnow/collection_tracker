import os
import json
from google.cloud import aiplatform, storage
from google.cloud.aiplatform_v1.types import IndexDatapoint

# ==========================
# 1. Google Cloud Setup
# ==========================
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = r"/home/pranav_ggs/pipeline/rag-pipeline/google_crendentials_from_CN.json"

PROJECT_ID = "spine-qa"
REGION = "asia-south1"
aiplatform.init(project=PROJECT_ID, location=REGION)


# ==========================
# 2. Load Existing Matching Engine Index
# ==========================
# REPLACE WITH YOUR ACTUAL INDEX ID AND ENDPOINT ID
# You can find these in the Vertex AI console under Vector Search -> INDEXES and INDEX ENDPOINTS.
# Make sure your index was created with STREAM_UPDATE method.

INDEX_ID = "6441255774860607488"
INDEX_ENDPOINT_ID = "8998983703858249728"
# print(aiplatform.MatchingEngineIndex.list())
# print(aiplatform.MatchingEngineIndexEndpoint.list())

my_index = aiplatform.MatchingEngineIndex(INDEX_ID)
my_index_endpoint = aiplatform.MatchingEngineIndexEndpoint(INDEX_ENDPOINT_ID)

print(f" Loaded existing index: {my_index.resource_name}")
print(f" Loaded existing index endpoint: {my_index_endpoint.resource_name}")

# ==========================
# 3. Process and Upsert Datapoints
# ==========================
# local_jsonl_path = r"/home/spineai/pipeline/rag-pipeline/trials/combined_video_rag.jsonl"
# local_jsonl_path = r"/home/spineai/pipeline/rag-pipeline/trials/CNG_Cranking_circuit_English.jsonl"
# local_jsonl_path = r"/home/spineai/pipeline/rag-pipeline/trials/JPSL_bolted_design_lift_axle_fitment_process_video_English_1.jsonl"

local_jsonl_path = r"/home/pranav_ggs/pipeline/rag-pipeline/videos_to_upload/wabco_jsonl.jsonl"

# def process_dict_new(metadata: Dict) -> List[IndexDatapoint.Restriction]:
#     restricts = metadata.get("restricts", [])
#     return [
#         IndexDatapoint.Restriction(namespace=r["namespace"], allow_list=r["allow"])
#         for r in restricts
#         if "namespace" in r and "allow" in r
#     ]

# def metadata_to_index_datapoint(item: Dict) -> Optional[IndexDatapoint]:
#     if not item.get("embedding"):
#         print(f"[WARNING] Skipping datapoint {item.get('id')} - no embedding")
#         return None
#     return IndexDatapoint(
#         datapoint_id=item["id"],
#         feature_vector=item["embedding"],
#         restricts=process_dict_new(item),
#     )


datapoints_to_upsert = []
with open(local_jsonl_path, "r", encoding="utf-8") as f:
    for lineno, line in enumerate(f, start=1):
        # Skip empty/whitespace-only lines
        if not line or not line.strip():
            continue

        # Normalize common non-JSON prefixes (e.g. files with '// ' comment prefixes)
        s = line.strip()
        if s.startswith("//"):
            s = s[2:].lstrip()
        if s.startswith("#"):
            s = s[1:].lstrip()

        # Try to parse the (possibly normalized) string as JSON; if it's malformed, log and skip
        try:
            item = json.loads(s)
        except json.JSONDecodeError as e:
            print(f"[WARNING] Skipping malformed JSON at {local_jsonl_path}:{lineno}: {e}")
            preview = s[:200]
            print(f"  preview: {preview}{'...' if len(s)>200 else ''}")
            continue

        # Basic validation
        if not item.get("embedding"):
            print(f"[WARNING] Skipping datapoint at line {lineno} - missing 'embedding'")
            continue

        datapoints_to_upsert.append(
            IndexDatapoint(
                datapoint_id=str(item.get("id", f"line-{lineno}")),
                feature_vector=item["embedding"],
                restricts=[
                    IndexDatapoint.Restriction(
                        namespace=r["namespace"], allow_list=r["allow"]
                    )
                    for r in item.get("restricts", [])
                    if "namespace" in r and "allow" in r
                ],
            )
        )
        # datapoints_to_upsert.append({
        #     "datapoint_id": str(item["id"]),  # Ensure a unique ID
        #     "feature_vector": item["embedding"] # The vector data
        # })

print(f" Found {len(datapoints_to_upsert)} datapoints to upsert.")

# Upsert the datapoints in batches
batch_size = 1000
for i in range(0, len(datapoints_to_upsert), batch_size):
    batch = datapoints_to_upsert[i : i + batch_size]
    try:
        my_index.upsert_datapoints(datapoints=batch)
        print(f" Successfully upserted batch starting at index {i}")
    except Exception as e:
        print(f" Failed to upsert batch starting at index {i}: {e}")

print(" Upsert process complete.")


