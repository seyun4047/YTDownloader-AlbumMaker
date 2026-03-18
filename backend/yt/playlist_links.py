#!/usr/bin/env python3
"""
Fetch all video links from a YouTube playlist.

Usage:
  python playlist_links.py "https://youtube.com/playlist?list=..."

Notes:
  - Requires yt-dlp: pip install yt-dlp
  - Prints one video URL per line to stdout.
"""

from __future__ import annotations

import sys
from typing import List


def _require_yt_dlp():
    try:
        import yt_dlp  # type: ignore
    except Exception as exc:  # pragma: no cover
        raise SystemExit(
            "yt-dlp is required. Install with: pip install yt-dlp"
        ) from exc
    return yt_dlp


def get_playlist_links(playlist_url: str) -> List[str]:
    yt_dlp = _require_yt_dlp()
    ydl_opts = {
        "quiet": True,
        "extract_flat": True,
        "skip_download": True,
        "dump_single_json": True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(playlist_url, download=False)
    entries = info.get("entries") or []
    links = []
    for entry in entries:
        if not entry:
            continue
        url = entry.get("url")
        if not url:
            continue
        if url.startswith("http"):
            links.append(url)
        else:
            links.append(f"https://www.youtube.com/watch?v={url}")
    return links


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python playlist_links.py <playlist_url>", file=sys.stderr)
        return 2
    playlist_url = sys.argv[1].strip()
    if not playlist_url:
        print("Playlist URL is empty.", file=sys.stderr)
        return 2
    links = get_playlist_links(playlist_url)
    for link in links:
        print(link)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
