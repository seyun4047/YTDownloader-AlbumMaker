from mutagen.id3 import ID3, USLT


def add_lyrics_to_mp3(mp3_path, lyrics_path, lang="kor"):
    with open(lyrics_path, "r", encoding="utf-8") as f:
        lyrics_text = f.read().strip()

    try:
        audio = ID3(mp3_path)
    except Exception:
        audio = ID3()

    # 기존 가사 제거
    audio.delall("USLT")

    audio.add(
        USLT(
            encoding=3,  # utf-8
            # lang=lang,  # ISO-639-2, e.g. kor/eng/jpn
            desc="Lyrics",
            text=lyrics_text,
        )
    )

    audio.save(mp3_path)
    print("Lyrics added!")


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("Usage: python audiolyricadder.py [mp3_path] [lyrics_path] [lang(optional, default=kor)]")
    else:
        mp3_path = sys.argv[1]
        lyrics_path = sys.argv[2]
        lang = sys.argv[3] if len(sys.argv) >= 4 else "kor"
        add_lyrics_to_mp3(mp3_path, lyrics_path, lang=lang)
