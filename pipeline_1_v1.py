import os
import json
import re
import logging
from typing import List, Dict
from pathlib import Path

from dotenv import load_dotenv
from vertexai.generative_models import GenerativeModel
from langchain_google_vertexai import VertexAIEmbeddings
from google.cloud import aiplatform
import vertexai

# ======================================================================
# CONFIG & LOGGING
# ======================================================================
load_dotenv()
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = r"/home/pranav_ggs/pipeline/rag-pipeline/google_crendentials_from_CN.json"

PROJECT_ID = "spine-qa"
LOCATION = "asia-south1"
EMBEDDING_MODEL = "text-embedding-004"

MIN_PROCESS_DURATION = 20  # seconds (20‒40 suggested)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

# init
aiplatform.init(project=PROJECT_ID, location=LOCATION)
vertexai.init(project=PROJECT_ID, location=LOCATION)
embedding_model = VertexAIEmbeddings(model_name=EMBEDDING_MODEL)

BoundaryCache = {}

# ======================================================================
# HELPERS
# ======================================================================

def ts_to_seconds(ts: str):
    """00:00:10 -> float seconds"""
    try:
        h, m, s = ts.strip().split(":")
        return int(h)*3600 + int(m)*60 + float(s)
    except:
        return 0.0


def parse_transcript_lines_with_timestamps(text: str) -> List[Dict]:
    parsed = []
    for line in text.strip().split("\n"):
        parts = line.strip().split(" | ")
        if len(parts) == 3:
            parsed.append({
                "start": parts[0].strip(),
                "end": parts[1].strip(),
                "text": parts[2].strip()
            })
    return parsed


# ======================================================================
# GEMINI boundary extraction (with caching)
# ======================================================================
def get_timestamps_from_transcript(transcript_text: str) -> List[Dict]:
    """Extract procedure boundaries using Gemini (cached)."""

    if transcript_text in BoundaryCache:
        logging.info("Using cached Gemini boundaries")
        return BoundaryCache[transcript_text]

    logging.info("Calling Gemini to detect process boundaries…")

    prompt = f"""
You are an expert technician.
Given the transcript with timestamps,
identify TRUE procedure boundaries.

Boundaries appear when a NEW technical action starts:
remove, install, replace, adjust, check, inspect, test, torque,
safety, preparation, etc.

RETURN ONLY strict JSON array:
[
  {{"start":"00:00:10","title":"Remove Viscous Fan"}}
]

Transcript:
\"\"\"{transcript_text}\"\"\"    
"""

    try:
        model = GenerativeModel(model_name="gemini-2.5-flash")
        response = model.generate_content(prompt)
        text = getattr(response, "text", "")
        match = re.search(r'\[.*\]', text, re.DOTALL)

        result = json.loads(match.group(0)) if match else []
        BoundaryCache[transcript_text] = result

        logging.info(f"Gemini returned {len(result)} boundaries")
        return result

    except Exception as e:
        logging.error(f"[Gemini Error] {e}")
        BoundaryCache[transcript_text] = []
        return []


# ======================================================================
# PROCESS CHUNKING + auto-merge
# ======================================================================
def group_lines_by_section(parsed_lines, section_starts):

    if not section_starts:
        logging.warning("No Gemini sections → full video single chunk")
        return [{
            "section_title": "Process",
            "start": parsed_lines[0]["start"],
            "end": parsed_lines[-1]["end"],
            "process_text": " ".join(p["text"] for p in parsed_lines)
        }]

    section_starts = sorted(section_starts, key=lambda x: x["start"])
    blocks = []
    block_idx = 0

    current = {
        "section_title": section_starts[0]["title"],
        "start": section_starts[0]["start"],
        "contents": []
    }

    for line in parsed_lines:
        if block_idx+1 < len(section_starts) and line["start"] >= section_starts[block_idx+1]["start"]:
            current["end"] = current["contents"][-1]["end"]
            current["process_text"] = " ".join(p["text"] for p in current["contents"])
            blocks.append(current)

            block_idx += 1
            current = {
                "section_title": section_starts[block_idx]["title"],
                "start": section_starts[block_idx]["start"],
                "contents": []
            }

        current["contents"].append(line)

    if current["contents"]:
        current["end"] = current["contents"][-1]["end"]
        current["process_text"] = " ".join(p["text"] for p in current["contents"])
        blocks.append(current)

    logging.info(f"Raw Gemini sections = {len(blocks)}")

    # ---- AUTO MERGE TINY SEGMENTS ----
    merged = []
    for b in blocks:
        duration = ts_to_seconds(b["end"]) - ts_to_seconds(b["start"])

        if duration < MIN_PROCESS_DURATION and merged:
            logging.info(f"Merging tiny segment '{b['section_title']}' ({duration}s) into previous")
            merged[-1]["process_text"] += " " + b["process_text"]
            merged[-1]["end"] = b["end"]
        else:
            merged.append(b)

    logging.info(f"Final merged chunks = {len(merged)}")
    return merged


# ======================================================================
# PIPELINE
# ======================================================================
def process_transcript_file(file_path: Path) -> List[Dict]:
    logging.info(f"Processing: {file_path.name}")

    raw_text = file_path.read_text(encoding="utf-8").strip()
    parsed = parse_transcript_lines_with_timestamps(raw_text)

    if not parsed:
        logging.warning("Transcript empty or unparsable")
        return []

    boundaries = get_timestamps_from_transcript(raw_text)
    blocks = group_lines_by_section(parsed, boundaries)

    texts = [b["process_text"] for b in blocks]

    try:
        embeddings = embedding_model.embed_documents(texts)
    except Exception as e:
        logging.error(f"Embedding failed '{file_path.name}': {e}")
        return []

    results = []
    for i, b in enumerate(blocks):
        results.append({
            "filename": file_path.stem,
            "start": b["start"],
            "end": b["end"],
            # SAME schema as before
            "chunk_text": b["process_text"],
            "section_title": b["section_title"],
            "embedding": embeddings[i]
        })

    logging.info(f"Created {len(results)} process-chunks from {file_path.name}")
    return results



def process_all_transcripts(folder_path: str) -> List[Dict]:
    all_results = []
    folder = Path(folder_path)
    files = list(folder.glob("*.txt"))

    if not files:
        logging.error(f"No .txt files found in folder: {folder_path}")
        return []

    for f in files:
        all_results.extend(process_transcript_file(f))

    return all_results


def save_to_json(data: List[Dict], path: str):
    Path(path).write_text(
        json.dumps(data, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )
    logging.info(f"Saved all results → {path}")


# ======================================================================
# MAIN
# ======================================================================
if __name__ == "__main__":
    results = process_all_transcripts(
        r"/home/pranav_ggs/pipeline/rag-pipeline/videos_to_upload/Ingestion2_transcripts"
    )

    save_to_json(
        results,
        r"/home/pranav_ggs/pipeline/rag-pipeline/videos_to_upload/wabco_chunk_embeddings.json"
    )
    logging.info("Processing complete.")