import urllib.request
from pathlib import Path

import yt_dlp


def download_thumbnail(url, output_path=None):
    ydl_opts = {
        "quiet": True,
        "skip_download": True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)

    thumbnail_url = info.get("thumbnail")
    if not thumbnail_url:
        raise ValueError("No thumbnail found for this URL.")

    if output_path is None:
        output_path = f"{info.get('title', 'thumbnail')}.jpg"

    output = Path(output_path)
    urllib.request.urlretrieve(thumbnail_url, output.as_posix())
    return output.as_posix()


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python thumbnaildownloader.py [url] [output_path(optional)]")
    else:
        url = sys.argv[1]
        output_path = sys.argv[2] if len(sys.argv) >= 3 else None
        saved_path = download_thumbnail(url, output_path=output_path)
        print(f"Thumbnail saved: {saved_path}")
