import whisper
import os
import ssl

ssl._create_default_https_context = ssl._create_unverified_context


# def sec2lrc(sec):
#     m = int(sec // 60)
#     s = int(sec % 60)
#     cs = int((sec - int(sec)) * 100)  # centisecond
#     return f"{m:02}:{s:02}.{cs:02}"
def transcribe_to_lrc(audio_path, lrc_path=None, model_size="small", lang="ko"):
    # Load Whisper model
    model = whisper.load_model(model_size)

    # transcribe
    result = model.transcribe(audio_path, language=lang)
    segments = result["segments"]

    if lrc_path is None:
        lrc_path = os.path.splitext(audio_path)[0] + ".lrc"

    with open(lrc_path, "w", encoding="utf-8") as f:
        for seg in segments:
            text = seg["text"].strip()
            f.write(f"{text}\n")

            # timestamp = sec2lrc(start)
            # f.write(f"[{timestamp}] {text}\n")

    print(f"Saved LRC! Path: {lrc_path}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python extlrc.py [audio_path] [lrc_path(optional)] [lang(optional, default=ko)]")
    else:
        audio_path = sys.argv[1]
        lrc_path = sys.argv[2] if len(sys.argv) >= 3 else None
        lang = sys.argv[3] if len(sys.argv) >= 4 else "ko"
        transcribe_to_lrc(audio_path, lrc_path=lrc_path, lang=lang)
