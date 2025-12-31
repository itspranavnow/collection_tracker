import os
import json
import uuid
import math
import re
import logging
from pathlib import Path
from typing import List, Dict, Any

import whisper
import psycopg2
from google.cloud import storage, aiplatform
from vertexai.generative_models import GenerativeModel
from langchain_google_vertexai import VertexAIEmbeddings
import vertexai

# ---------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------

PROJECT_ID = os.getenv("PROJECT_ID", "spine-qa")
LOCATION = os.getenv("LOCATION", "asia-south1")

EMBEDDING_MODEL = "gemini-embedding-001"
EXPECTED_EMBED_DIM = 3072   # gemini-embedding-001 dimension
MIN_PROCESS_DURATION = 20

GCS_TMP_DIR = "/tmp/videos"
OUTPUT_JSONL = "/tmp/video_rag_embeddings.jsonl"

MATCHING_ENGINE_INDEX_ID = os.getenv("ME_INDEX_ID")
MATCHING_ENGINE_ENDPOINT_ID = os.getenv("ME_ENDPOINT_ID")

vertexai.init(project=PROJECT_ID, location=LOCATION)
aiplatform.init(project=PROJECT_ID, location=LOCATION)

embedding_model = VertexAIEmbeddings(model_name=EMBEDDING_MODEL)
gemini_model = GenerativeModel("gemini-2.5-flash")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

os.makedirs(GCS_TMP_DIR, exist_ok=True)
BoundaryCache = {}

# ---------------------------------------------------------------------
# TIME HELPERS
# ---------------------------------------------------------------------

def seconds_to_ts(sec: float) -> str:
    h = int(sec // 3600)
    m = int((sec % 3600) // 60)
    s = sec % 60
    return f"{h:02d}:{m:02d}:{s:05.2f}"

def ts_to_seconds(ts: str) -> float:
    try:
        h, m, s = ts.split(":")
        return int(h) * 3600 + int(m) * 60 + float(s)
    except:
        return 0.0

# ---------------------------------------------------------------------
# POSTGRES (CMS VIEW)
# ---------------------------------------------------------------------

def get_pg_conn():
    return psycopg2.connect(
        host=os.getenv("PG_HOST"),
        database=os.getenv("PG_DB"),
        user=os.getenv("PG_USER"),
        password=os.getenv("PG_PASSWORD"),
        port=5432
    )

def fetch_metadata_from_view(filename: str) -> Dict[str, Any]:
    logging.info(f"Fetching CMS metadata for filename={filename}")

    query = "SELECT * FROM public.fn_get_metadata_details_raw(%s)"

    with get_pg_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (filename,))
            row = cur.fetchone()
            cols = [d[0] for d in cur.description]

    if not row:
        raise ValueError(f"No metadata found for {filename}")

    return dict(zip(cols, row))

# ---------------------------------------------------------------------
# GCS
# ---------------------------------------------------------------------

def download_video(gcs_url: str) -> str:
    logging.info(f"Downloading video: {gcs_url}")
    client = storage.Client()
    bucket, blob = gcs_url.replace("gs://", "").split("/", 1)
    local_path = os.path.join(GCS_TMP_DIR, Path(blob).name)
    client.bucket(bucket).blob(blob).download_to_filename(local_path)
    return local_path

# ---------------------------------------------------------------------
# TRANSCRIPTION
# ---------------------------------------------------------------------

def transcribe_video(video_path: str) -> List[Dict]:
    logging.info(f"Transcribing video: {video_path}")
    model = whisper.load_model("base")
    result = model.transcribe(video_path, fp16=False)

    segments = [{
        "start": seconds_to_ts(s["start"]),
        "end": seconds_to_ts(s["end"]),
        "text": s["text"].strip()
    } for s in result["segments"] if s["text"].strip()]

    logging.info(f"Transcript segments: {len(segments)}")
    return segments

# ---------------------------------------------------------------------
# GEMINI PROCEDURAL BOUNDARIES
# ---------------------------------------------------------------------

def get_gemini_boundaries(segments: List[Dict]) -> List[Dict]:
    transcript = "\n".join(
        f"{s['start']} | {s['end']} | {s['text']}" for s in segments
    )

    if transcript in BoundaryCache:
        return BoundaryCache[transcript]

    logging.info("Calling Gemini for procedural boundaries")

    prompt = f"""
Identify true procedural boundaries.
Return ONLY strict JSON:

[
  {{"start":"00:01:13","title":"Continuity test"}}
]

Transcript:
\"\"\"{transcript}\"\"\"
"""

    try:
        resp = gemini_model.generate_content(prompt)
        match = re.search(r"\[.*\]", resp.text, re.DOTALL)
        boundaries = json.loads(match.group(0)) if match else []
        BoundaryCache[transcript] = boundaries
        logging.info(f"Gemini boundaries detected: {len(boundaries)}")
        return boundaries
    except Exception as e:
        logging.error(f"Gemini boundary failure: {e}")
        return []

# ---------------------------------------------------------------------
# CHUNKING + AUTO MERGE
# ---------------------------------------------------------------------

def group_segments(segments, boundaries):
    if not boundaries:
        return [{
            "section_title": "Process",
            "start": segments[0]["start"],
            "end": segments[-1]["end"],
            "chunk_text": " ".join(s["text"] for s in segments)
        }]

    boundaries = sorted(boundaries, key=lambda x: x["start"])
    chunks, idx = [], 0

    current = {
        "section_title": boundaries[0]["title"],
        "start": boundaries[0]["start"],
        "lines": []
    }

    for seg in segments:
        if idx + 1 < len(boundaries) and seg["start"] >= boundaries[idx + 1]["start"]:
            current["end"] = current["lines"][-1]["end"]
            current["chunk_text"] = " ".join(l["text"] for l in current["lines"])
            chunks.append(current)
            idx += 1
            current = {
                "section_title": boundaries[idx]["title"],
                "start": boundaries[idx]["start"],
                "lines": []
            }
        current["lines"].append(seg)

    current["end"] = current["lines"][-1]["end"]
    current["chunk_text"] = " ".join(l["text"] for l in current["lines"])
    chunks.append(current)

    merged = []
    for c in chunks:
        dur = ts_to_seconds(c["end"]) - ts_to_seconds(c["start"])
        if dur < MIN_PROCESS_DURATION and merged:
            merged[-1]["chunk_text"] += " " + c["chunk_text"]
            merged[-1]["end"] = c["end"]
        else:
            merged.append(c)

    logging.info(f"Final chunks: {len(merged)}")
    return merged

# ---------------------------------------------------------------------
# EMBEDDINGS
# ---------------------------------------------------------------------

def embed_chunks(chunks):
    texts = [c["chunk_text"] for c in chunks]
    vectors = embedding_model.embed_documents(texts)

    for i, c in enumerate(chunks):
        c["embedding"] = vectors[i]

    return chunks

# ---------------------------------------------------------------------
# RESTRICT BUILDER (FINAL LOGIC)
# ---------------------------------------------------------------------

def build_restricts(meta, chunk, filename, gcs_url):

    restricts = [
        {"namespace": "filename", "allow": [filename]},
        {"namespace": "start", "allow": [chunk["start"]]},
        {"namespace": "end", "allow": [chunk["end"]]},
        {"namespace": "chunk_text", "allow": [chunk["chunk_text"]]},
        {"namespace": "section_title", "allow": [chunk["section_title"]]},
        {"namespace": "gcs_url", "allow": [gcs_url]},
        {"namespace": "data_source", "allow": ["video"]},
    ]

    # optional always-safe fields
    mapping = {
        "division": meta.get("div_name"),
        "emission": meta.get("emission_type"),
        "segment": meta.get("segment_name"),
        "language": meta.get("language_name"),
    }

    for k, v in mapping.items():
        if v:
            restricts.append({"namespace": k, "allow": [v]})

    applicability = meta.get("applicability_type")
    restricts.append({"namespace": "applicability_type", "allow": [applicability]})

    if applicability != "Global":
        if meta.get("application_type"):
            restricts.append({"namespace": "series", "allow": meta["application_type"]})
        if meta.get("model_name"):
            restricts.append({"namespace": "model_name", "allow": meta["model_name"]})
        if meta.get("fuel_type"):
            restricts.append({"namespace": "fuel_type", "allow": [meta["fuel_type"]]})
        if meta.get("aggregate_name"):
            restricts.append({"namespace": "aggregate", "allow": [meta["aggregate_name"]]})

    return restricts

# ---------------------------------------------------------------------
# INGESTION
# ---------------------------------------------------------------------

def ingest_video(filename: str, jsonl_file):
    meta = fetch_metadata_from_view(filename)
    video_path = download_video(meta["gcs_url"])

    segments = transcribe_video(video_path)
    boundaries = get_gemini_boundaries(segments)
    chunks = embed_chunks(group_segments(segments, boundaries))

    for c in chunks:
        record = {
            "id": str(uuid.uuid4()),
            "embedding": c["embedding"],
            "restricts": build_restricts(meta, c, filename, meta["gcs_url"])
        }
        jsonl_file.write(json.dumps(record) + "\n")

    logging.info(f"Ingested {len(chunks)} chunks for {filename}")

# ---------------------------------------------------------------------
# VALIDATION
# ---------------------------------------------------------------------

def validate_jsonl(path):
    with open(path) as f:
        for i, line in enumerate(f, 1):
            rec = json.loads(line)
            if len(rec["embedding"]) != EXPECTED_EMBED_DIM:
                raise RuntimeError(f"Line {i}: embedding dim mismatch")
    logging.info("JSONL validation passed")

# ---------------------------------------------------------------------
# ENTRYPOINT
# ---------------------------------------------------------------------

def run(filenames: List[str]):
    with open(OUTPUT_JSONL, "w") as f:
        for name in filenames:
            try:
                ingest_video(name, f)
            except Exception as e:
                logging.error(f"Failed {name}: {e}")

    validate_jsonl(OUTPUT_JSONL)

if __name__ == "__main__":
    FILES = os.getenv("VIDEO_FILENAMES", "").split(",")
    run([f for f in FILES if f])
