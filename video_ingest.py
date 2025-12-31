import os
import json
from google.cloud import aiplatform, storage

# ==========================
# 1. Google Cloud Setup
# ==========================
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = r"C:\Users\CN685\OneDrive\Desktop\ai-microservice\src\retrieval\spine-qa-62166d7c2d5a.json"

PROJECT_ID = "spine-qa"
REGION = "asia-south1"
aiplatform.init(project=PROJECT_ID, location=REGION)

# ==========================
# 2. Combine JSON Files
# ==========================
file1 = "xml_data.json"
file2 = "videos_data.json"
output_file = "combined-data-video-xml.json"

with open(file1, "r", encoding="utf-8") as f1:
    data1 = json.load(f1)

with open(file2, "r", encoding="utf-8") as f2:
    data2 = json.load(f2)

if isinstance(data1, list) and isinstance(data2, list):
    combined = data1 + data2
elif isinstance(data1, dict) and isinstance(data2, dict):
    combined = {**data1, **data2}
else:
    combined = [data1, data2]

with open(output_file, "w", encoding="utf-8") as out:
    json.dump(combined, out, indent=4, ensure_ascii=False)

print(f" Combined JSON saved to {output_file}")

# ==========================
# 3. Upload to GCS
# ==========================
storage_client = storage.Client()
TEXT_EMBEDDING_BUCKET = "video-data-spine"
gcs_path = "combined-data-video-xml.json"
local_path = r"C:\Users\CN685\ai-microservice\chunking_output\new_combined_3_sep_unique.jsonl"

try:
    bucket = storage_client.get_bucket(TEXT_EMBEDDING_BUCKET)
    print(f"Bucket '{TEXT_EMBEDDING_BUCKET}' already exists.")
except Exception:
    bucket = storage.Bucket(storage_client, name=TEXT_EMBEDDING_BUCKET)
    bucket.location = REGION
    bucket = storage_client.create_bucket(bucket)
    print(f"Bucket '{TEXT_EMBEDDING_BUCKET}' created.")

blob = bucket.blob(gcs_path)

if blob.exists():
    print(f" File already exists at gs://{TEXT_EMBEDDING_BUCKET}/{gcs_path}")
else:
    try:
        blob.upload_from_filename(local_path)
        print(f" Uploaded JSON to: gs://{TEXT_EMBEDDING_BUCKET}/{gcs_path}")
    except Exception as e:
        print(f" Failed to upload JSON to GCS: {e}")

# ==========================
# 4. Create Matching Engine Index
# ==========================
DISPLAY_NAME = "combined_data"
DIMENSIONS = 768
gs_uri = f"gs://{TEXT_EMBEDDING_BUCKET}"

print(" Creating Matching Engine index (this may take ~30s)...")
my_index = aiplatform.MatchingEngineIndex.create_tree_ah_index(
    display_name=DISPLAY_NAME,
    dimensions=DIMENSIONS,
    approximate_neighbors_count=150,
    distance_measure_type="DOT_PRODUCT_DISTANCE",
    index_update_method="STREAM_UPDATE",
    contents_delta_uri=gs_uri,
    shard_size="SHARD_SIZE_SMALL",
)

# ==========================
# 5. Create Endpoint
# ==========================
DEPLOYMENT_MACHINE_TYPE = "n2d-standard-32"
print(" Creating index endpoint...")
my_index_endpoint = aiplatform.MatchingEngineIndexEndpoint.create(
    display_name=f"{DISPLAY_NAME}-endpoint",
    public_endpoint_enabled=True,
    location=REGION,
)

# ==========================
# 6. Deploy Index
# ==========================
deployed_index_id = "sample_idx_2"

print(" Deploying index (this may take up to 20 minutes)...")
my_index_endpoint = my_index_endpoint.deploy_index(
    index=my_index,
    deployed_index_id=deployed_index_id,
    machine_type=DEPLOYMENT_MACHINE_TYPE,
)

print(" Deployment complete.")
print("Deployed indexes:", my_index_endpoint.deployed_indexes)
