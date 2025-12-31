---
VIDEO_TTS — Submission README
---

Purpose
-------
This folder contains the tooling and artifacts used to generate and manage Text-to-Speech (TTS) audio aligned to video timelines. The README below is a submission-style document intended to be uploaded to a Git repository alongside the code and assets.

Contents
--------
- `raw/` (recommended): per-chunk generated audio files (e.g. `segment_0.mp3`).
- `final/` (recommended): final merged audio files for each video (e.g. `video_final.mp3`).
- `manifests/` (recommended): JSON/CSV mapping files that link transcript segments to audio files and timestamps.
- `scripts/` (optional): helper scripts for normalization, concatenation, and upload.
- `dubs_rear.py` (example): a sample end-to-end script that generates, aligns, and muxes TTS audio to video.

Quick summary
-------------
- Input: timestamped transcript (JSON) containing segments with `start`, `end`, and `text` (SSML or plain text).
- Processing: generate per-segment audio via TTS, speed-adjust or pad to meet segment duration, concatenate segments, optionally pad to video length.
- Output: combined aligned audio for each video and a final video with the new audio track.

Prerequisites
-------------
- System tools:
	- `ffmpeg` and `ffprobe` available on PATH.
- Python environment (recommended):
	- Python 3.10+ (repo used Python 3.12 during development).
	- Virtual environment recommended to isolate dependencies.

Python dependencies (example)
-----------------------------
Install the minimal packages used by helper scripts and sample tools:

```bash
python -m venv .venv
source .venv/bin/activate
pip install pydub python-dotenv google-cloud-texttospeech
```

Configuration & credentials
---------------------------
- If using Google Cloud Text-to-Speech, set the `GOOGLE_APPLICATION_CREDENTIALS` environment variable to a service account JSON with TTS permissions. Example:

```bash
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account.json"
```

Example usage (high-level)
--------------------------
1. Prepare a timestamped transcript JSON (array of segments). Each segment must at least contain `start`, `end`, and `text`.
2. Generate per-segment TTS audio and save into `VIDEO_TTS/raw/`.
3. Normalize and, if required, speed-adjust or pad each chunk to match its target duration.
4. Concatenate chunks in chronological order into `VIDEO_TTS/final/{video_id}.wav` or `.mp3`.
5. Optionally upload final audio and/or mux it into the original video via `ffmpeg`.

Common ffmpeg examples
----------------------
Normalize sample rate and channels:

```bash
ffmpeg -i input.mp3 -ar 16000 -ac 1 output_mono_16k.wav
```

Concat a list of WAV files using a file list:

```bash
# create files.txt with lines: file 'VIDEO_TTS/raw/chunk_001.wav'
ffmpeg -f concat -safe 0 -i files.txt -c copy VIDEO_TTS/final/video_final.wav
```

Recommended practices
---------------------
- Keep a manifest per video in `VIDEO_TTS/manifests/` that records: segment index, start, end, chunk filename, flags (speed_adjusted/silence_added), and QA notes.
- Use consistent sample rate and channel layout across chunks (recommended mono 16k or 24kHz) before concatenation.
- Version control only scripts and manifests; avoid committing large binary audio files unless required by repo policy.

Troubleshooting
---------------
- JSON parse errors: ensure NDJSON/JSON files contain valid JSON objects (no leading `//` or stray commas).
- `ModuleNotFoundError`: activate the virtualenv and install dependencies into it.
- Out-of-sync audio: check timestamps and QA manifest to find segments with mismatch or speed adjustment.

Extending this folder
---------------------
- Add helper scripts under `VIDEO_TTS/scripts/` for normalization, merging, and uploading.
- Add a `Makefile` or `run_tts.sh` to standardize the pipeline: generate → normalize → merge → upload.
- Store QA JSON outputs (segment QA and timeline QA) in `VIDEO_TTS/manifests/` for traceability.

Contact / Maintainer
--------------------
If you want me to add helper scripts, CI checks, or manifest writers, reply with which parts you want automated and I will add them.

