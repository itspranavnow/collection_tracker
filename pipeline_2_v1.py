# import json
# import os
# import uuid
# from datetime import datetime

# ALL_VIDEO_ROOT = r"/home/pranav_ggs/pipeline/rag-pipeline/ALL_VIDEOS"
# EMBEDDINGS_FILE = r"/home/pranav_ggs/pipeline/rag-pipeline/ALL_VIDEOS/chunks_embeddingsv2.json"
# OUTPUT_FILE = r"/home/pranav_ggs/pipeline/rag-pipeline/ALL_VIDEOS/final_embeddings.jsonl"

# LOG_FILE = r"/home/pranav_ggs/pipeline/rag-pipeline/ALL_VIDEOS/embed_warnings.log"

# GCS_PREFIX = "gs://pilot-videos/uploads/videos/"
# DATA_SOURCE = "video"


# # log helper
# def log(message):
#     with open(LOG_FILE, "a", encoding="utf8") as lf:
#         lf.write(f"{datetime.now()}  {message}\n")
#     print(message)  # also print to console


# def generate_uuid():
#     return str(uuid.uuid4())


# def process_dict(metadata: dict):
#     return [{"namespace": k, "allow": [str(v)]} for k, v in metadata.items()]


# def scan_all_videos(base_dir):
#     vidmap = {}

#     for root, dirs, files in os.walk(base_dir):
#         for file in files:
#             if file.lower().endswith(".mp4"):
#                 noext = os.path.splitext(file)[0]
#                 vidmap[noext] = os.path.join(root, file)

#     return vidmap


# # ----------- Build lookup
# videopaths = scan_all_videos(ALL_VIDEO_ROOT)
# log(f"Found {len(videopaths)} videos in filesystem")


# # ----------- Read embeddings
# with open(EMBEDDINGS_FILE, "r", encoding="utf8") as f:
#     embeddings = json.load(f)


# # ----------- Write final jsonl

# skipped_count = 0
# missing_video_count = 0

# with open(OUTPUT_FILE, "w", encoding="utf8") as outf:

#     for entry in embeddings:

#         fname = entry.get("filename")
#         filepath = videopaths.get(fname)

#         if not filepath:
#             log(f"[MISSING VIDEO] No mp4 found for '{fname}'")
#             missing_video_count += 1
#             continue

#         parts = filepath.split(os.sep)

#         # need at least 8 path elements
#         if len(parts) < 8:
#             log(f"[SKIPPED] '{fname}' — incorrect path depth: {filepath}")
#             skipped_count += 1
#             continue

#         try:
#             aggregate = parts[-2]
#             fuel = parts[-3]
#             model = parts[-4]
#             series = parts[-5]
#             segment = parts[-6]
#             emission = parts[-7]
#         except:
#             log(f"[ERROR extracting metadata] for file={filepath}")
#             skipped_count += 1
#             continue

#         gcs_url = f"{GCS_PREFIX}{fname}.mp4"

#         metadata = {
#             "filename": fname + ".mp4",
#             "start": entry.get("start"),
#             "end": entry.get("end"),
#             "section_title": entry.get("section_title"),

#             # extracted from folders
#             "emission": emission,
#             "segment": segment,
#             "series": series,
#             "model_name": model,
#             "fuel_type": fuel,
#             "aggregate": aggregate,

#             "gcs_url": gcs_url,
#             "data_source": DATA_SOURCE,
#         }

#         record = {
#             "id": generate_uuid(),
#             "embedding": entry.get("embedding"),
#             "chunk_text": entry.get("chunk_text"),
#             "restricts": process_dict(metadata)
#         }

#         outf.write(json.dumps(record) + "\n")


# log("\n=== FINISHED ===")
# log(f"Output file: {OUTPUT_FILE}")
# log(f"Skipped (wrong folder depth): {skipped_count}")
# log(f"Missing video files: {missing_video_count}")
# log(f"Total embeddings processed: {len(embeddings) - skipped_count - missing_video_count}")



import json
import os
import uuid
from datetime import datetime

ALL_VIDEO_ROOT = r"/home/pranav_ggs/pipeline/rag-pipeline/videos_to_upload"
EMBEDDINGS_FILE = r"/home/pranav_ggs/pipeline/rag-pipeline/videos_to_upload/wabco_chunk_embeddings.json"
OUTPUT_FILE = r"/home/pranav_ggs/pipeline/rag-pipeline/videos_to_upload/wabco_jsonl.jsonl"

LOG_FILE = r"/home/pranav_ggs/pipeline/rag-pipeline/ALL_VIDEOS/embed_warnings.log"

GCS_PREFIX = "gs://pilot-videos/uploads/videos/"
DATA_SOURCE = "video"

# log helper
def log(message):
    with open(LOG_FILE, "a", encoding="utf8") as lf:
        lf.write(f"{datetime.now()}  {message}\n")
    print(message)

def generate_uuid():
    return str(uuid.uuid4())

def process_dict(metadata: dict):
    """
    Converts a metadata dictionary to restricts format:
    {"filename": "xxx"} -> [{"namespace": "filename", "allow": ["xxx"]}]
    """
    return [{"namespace": k, "allow": [str(v)]} for k, v in metadata.items()]

def scan_all_videos(base_dir):
    vidmap = {}
    for root, dirs, files in os.walk(base_dir):
        for file in files:
            if file.lower().endswith(".mp4"):
                noext = os.path.splitext(file)[0]
                vidmap[noext] = os.path.join(root, file)
    return vidmap

# ----------- Build lookup
videopaths = scan_all_videos(ALL_VIDEO_ROOT)
log(f"Found {len(videopaths)} videos in filesystem")

# ----------- Read embeddings
with open(EMBEDDINGS_FILE, "r", encoding="utf8") as f:
    embeddings = json.load(f)

# ----------- Write final jsonl

skipped_count = 0
missing_video_count = 0

with open(OUTPUT_FILE, "w", encoding="utf8") as outf:

    for entry in embeddings:

        fname = entry.get("filename")
        filepath = videopaths.get(fname)

        if not filepath:
            log(f"[MISSING VIDEO] No mp4 found for '{fname}'")
            missing_video_count += 1
            continue

        parts = filepath.split(os.sep)

        if len(parts) < 8:
            log(f"[SKIPPED] '{fname}' — incorrect path depth: {filepath}")
            skipped_count += 1
            continue

        try:
            aggregate = parts[-2]
            fuel = parts[-3]
            model = parts[-4]     # <- model_name (should now be "6048")
            series = parts[-5]
            segment = parts[-6]
            emission = parts[-7]
        except:
            log(f"[ERROR extracting metadata] for file={filepath}")
            skipped_count += 1
            continue

        gcs_url = f"{GCS_PREFIX}{fname}.mp4"

        # STRICT OLD-PROD SCHEMA
        metadata = {
            "filename": fname + ".mp4",
            "start": entry.get("start"),
            "end": entry.get("end"),
            "chunk_text": entry.get("chunk_text"),   # <-- stays inside restricts exactly like before
            "section_title": entry.get("section_title"),
            "model_name": model,                     # <-- correct extraction from folder
            "gcs_url": gcs_url,
            "data_source": DATA_SOURCE
        }

        record = {
            "id": generate_uuid(),
            "embedding": entry.get("embedding"),
            # "chunk_text": entry.get("chunk_text"),   # <--- important: top-level chunk_text
            "restricts": process_dict(metadata)
        }

        outf.write(json.dumps(record) + "\n")

log("\n=== FINISHED ===")
log(f"Output file: {OUTPUT_FILE}")
log(f"Skipped (wrong folder depth): {skipped_count}")
log(f"Missing video files: {missing_video_count}")
log(f"Total embeddings processed: {len(embeddings) - skipped_count - missing_video_count}")
