from mutagen.id3 import APIC, ID3


def add_thumbnail_to_mp3(mp3_path, thumbnail_path):
    with open(thumbnail_path, "rb") as f:
        image_data = f.read()

    if thumbnail_path.lower().endswith(".png"):
        mime = "image/png"
    elif thumbnail_path.lower().endswith(".webp"):
        mime = "image/webp"
    else:
        mime = "image/jpeg"

    try:
        audio = ID3(mp3_path)
    except Exception:
        audio = ID3()

    audio.delall("APIC")
    audio.add(
        APIC(
            encoding=3,
            mime=mime,
            type=3,  # front cover
            desc="Cover",
            data=image_data,
        )
    )
    audio.save(mp3_path)
    print("Thumbnail embedded!")


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 3:
        print("Usage: python thumnailadder.py [mp3_path] [thumbnail_path]")
    else:
        add_thumbnail_to_mp3(sys.argv[1], sys.argv[2])
