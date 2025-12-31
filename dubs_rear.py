import json
import subprocess
import os
from google.cloud import texttospeech
from pydub import AudioSegment
from dotenv import load_dotenv

# -----------------------------
# CONFIGURATION
# -----------------------------
load_dotenv()
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/home/pranav_ggs/pipeline/rag-pipeline/google_crendentials_from_CN.json"

INPUT_JSON = "/home/pranav_ggs/pipeline/rag-pipeline/tamil_transcripts/ja_rear.json"  # SSML transcript file
VIDEO_FILE = "/home/pranav_ggs/pipeline/rag-pipeline/english_videos/Rear Axle Contruction View 1.mp4"        # Original video
FINAL_AUDIO = "final_aligned_audio.mp3"  # Output audio
OUTPUT_VIDEO = "final_output.mp4"        # Output video
LANGUAGE_CODE = "ja-JP"                  # Change for language (e.g., te-IN, ta-IN, hi-IN)

# -----------------------------
# HELPER FUNCTIONS
# -----------------------------
def timestamp_to_seconds(ts):
    h, m, s = map(float, ts.split(":"))
    return h * 3600 + m * 60 + s

def generate_tts(ssml_text, filename):
    client = texttospeech.TextToSpeechClient()
    synthesis_input = texttospeech.SynthesisInput(ssml=ssml_text)
    voice = texttospeech.VoiceSelectionParams(language_code=LANGUAGE_CODE, ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL)
    audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3)
    response = client.synthesize_speech(input=synthesis_input, voice=voice, audio_config=audio_config)
    with open(filename, "wb") as out:
        out.write(response.audio_content)

def adjust_speed(input_file, output_file, speed_factor):
    # Limit speed factor for naturalness
    speed_factor = max(0.95, min(speed_factor, 1.15))
    subprocess.run(["ffmpeg", "-y", "-i", input_file, "-filter:a", f"atempo={speed_factor}", output_file])

# -----------------------------
# STEP 1: LOAD TRANSCRIPT
# -----------------------------
with open(INPUT_JSON, "r", encoding="utf-8") as f:
    segments = json.load(f)

segment_files = []
qa_segments = []

print("Generating TTS segments with strict timestamp adherence...")

# -----------------------------
# STEP 2: GENERATE SEGMENTS
# -----------------------------
for i, seg in enumerate(segments):
    start_sec = timestamp_to_seconds(seg["start"])
    end_sec = timestamp_to_seconds(seg["end"])
    target_duration = end_sec - start_sec

    ssml_text = seg["text"]
    filename = f"segment_{i}.mp3"
    generate_tts(ssml_text, filename)

    audio = AudioSegment.from_file(filename)
    actual_duration = audio.duration_seconds

    silence_added = False
    speed_adjusted = False

    # Speed adjustment if audio exceeds target
    if actual_duration > target_duration:
        speed_factor = target_duration / actual_duration
        adjusted_file = f"segment_adjusted_{i}.mp3"
        adjust_speed(filename, adjusted_file, speed_factor)
        audio = AudioSegment.from_file(adjusted_file)
        actual_duration = audio.duration_seconds
        filename = adjusted_file
        speed_adjusted = True

    # Silence padding if audio shorter
    if actual_duration < target_duration:
        silence = AudioSegment.silent(duration=(target_duration - actual_duration) * 1000)
        audio += silence
        audio.export(filename, format="mp3")
        silence_added = True

    segment_files.append(filename)
    qa_segments.append({
        "segment": i,
        "target_duration": target_duration,
        "actual_duration": actual_duration,
        "silence_added": silence_added,
        "speed_adjusted": speed_adjusted
    })

# -----------------------------
# STEP 3: ALIGN SEGMENTS ON TIMELINE
# -----------------------------
print("Aligning segments on timeline with silence for gaps...")
final_audio = AudioSegment.silent(duration=0)
current_time = 0.0
qa_timeline = []

for i, seg in enumerate(segments):
    start_sec = timestamp_to_seconds(seg["start"])
    end_sec = timestamp_to_seconds(seg["end"])
    target_duration = end_sec - start_sec

    audio = AudioSegment.from_file(segment_files[i])
    actual_duration = audio.duration_seconds

    # Insert silence for gap
    if start_sec > current_time:
        gap = start_sec - current_time
        final_audio += AudioSegment.silent(duration=gap * 1000)
        current_time += gap

    final_audio += audio
    current_time += actual_duration

    mismatch = abs(current_time - end_sec)
    qa_timeline.append({
        "segment": i,
        "start": start_sec,
        "end": end_sec,
        "target_duration": target_duration,
        "actual_duration": actual_duration,
        "gap_inserted": start_sec - (current_time - actual_duration),
        "mismatch_after_merge": mismatch
    })

# -----------------------------
# STEP 4: PAD TO MATCH VIDEO LENGTH
# -----------------------------
video_info = subprocess.run(
    ["ffprobe", "-v", "error", "-show_entries", "format=duration",
     "-of", "default=noprint_wrappers=1:nokey=1", VIDEO_FILE],
    capture_output=True, text=True
)
video_duration = float(video_info.stdout.strip())

if current_time < video_duration:
    final_audio += AudioSegment.silent(duration=(video_duration - current_time) * 1000)

final_audio.export(FINAL_AUDIO, format="mp3")

# -----------------------------
# STEP 5: MERGE AUDIO + VIDEO
# -----------------------------
print("Combining aligned audio with video...")
subprocess.run([
    "ffmpeg", "-y",
    "-i", VIDEO_FILE,
    "-i", FINAL_AUDIO,
    "-c:v", "copy",
    "-map", "0:v:0",
    "-map", "1:a:0",
    "-shortest",
    "-c:a", "aac",
    OUTPUT_VIDEO
])

print(f"✅ Final video saved as {OUTPUT_VIDEO}")

# -----------------------------
# STEP 6: PRINT QA REPORTS
# -----------------------------
print("\n=== SEGMENT QA REPORT ===")
for entry in qa_segments:
    print(f"Segment {entry['segment']}: Target={entry['target_duration']}s | Actual={entry['actual_duration']}s | Silence Added={entry['silence_added']} | Speed Adjusted={entry['speed_adjusted']}")

print("\n=== TIMELINE QA REPORT ===")
for entry in qa_timeline:
    print(f"Segment {entry['segment']}: Start={entry['start']}s | End={entry['end']}s | Target Duration={entry['target_duration']}s | Actual Duration={entry['actual_duration']}s | Gap Inserted={entry['gap_inserted']}s | Mismatch After Merge={entry['mismatch_after_merge']}s")