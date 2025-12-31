import os
import whisper
from datetime import timedelta

def format_time(s):
    return str(timedelta(seconds=int(s))).zfill(8)

def transcribe_video(video_path):
    model = whisper.load_model("base")  # You can use "small", "medium", or "large" if GPU supports
    result = model.transcribe(video_path)
    lines = []
    for seg in result["segments"]:
        start = format_time(seg['start'])
        end = format_time(seg['end'])
        txt = seg["text"].strip().replace('\n', ' ')
        lines.append(f"{start} | {end} | {txt}")
    return "\n".join(lines)

def transcribe_all_videos(video_dir, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    supported_exts = (".mp4", ".mov", ".mkv", ".avi")

    for root, _, files in os.walk(video_dir):
        for file in files:
            if file.lower().endswith(supported_exts):
                video_path = os.path.join(root, file)
                print(f"Transcribing: {video_path}")
                try:
                    transcript = transcribe_video(video_path)
                    base_name = os.path.splitext(file)[0]
                    out_file = os.path.join(output_dir, f"{base_name}.txt")
                    with open(out_file, "w", encoding="utf-8") as f:
                        f.write(transcript)
                    print(f"✅ Saved transcript: {out_file}")
                except Exception as e:
                    print(f"❌ Error transcribing {file}: {e}")

if __name__ == "__main__":
    # Prefer the original Windows path if present (allows running on the original dev machine),
    # otherwise fall back to the local `videos_to_upload` folder in this repo.
    win_path = r"C:\Users\CN685\ai-microservice\videos_to_upload"
    local_path = os.path.join(os.getcwd(), "videos_to_upload")
    output_dir = os.path.join(os.getcwd(), "videos_to_upload", "Ingestion2_transcripts")

    input_dir = win_path if os.path.exists(win_path) else local_path
    print(f"Using input_dir={input_dir}")
    print(f"Using output_dir={output_dir}")

    transcribe_all_videos(input_dir, output_dir)