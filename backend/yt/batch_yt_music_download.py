#!/usr/bin/env python3
"""
Batch-call a JSON API for each YouTube URL and download returned links.

Usage:
  python batch_yt_music_download.py urls.txt

Input file:
  - One YouTube URL per line.
  - Blank lines and lines starting with "#" are ignored.

Notes:
  - API endpoint and payload match the user's curl example by default.
  - Downloads are saved into ./downloads (created if missing).
"""

from __future__ import annotations

import json
import os
import re
import sys
import urllib.parse
import urllib.request
from typing import Any, Iterable, Optional


API_URL = "http://seyun4047.iptime.org:10210/yt/music"
DEFAULT_PAYLOAD = {
    "quality": "high",
    "lyric": False,
    "metadata": True,
}
OUT_DIR = "downloads"


def iter_urls(path: str) -> Iterable[str]:
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            yield line


def _find_url_in_json(obj: Any) -> Optional[str]:
    if isinstance(obj, str):
        if obj.startswith("http://") or obj.startswith("https://"):
            return obj
        return None
    if isinstance(obj, dict):
        for key in ("url", "link", "download_url", "downloadUrl", "file"):
            if key in obj and isinstance(obj[key], str):
                val = obj[key]
                if val.startswith("http://") or val.startswith("https://"):
                    return val
        for value in obj.values():
            found = _find_url_in_json(value)
            if found:
                return found
    if isinstance(obj, list):
        for item in obj:
            found = _find_url_in_json(item)
            if found:
                return found
    return None


def _find_url_in_text(text: str) -> Optional[str]:
    match = re.search(r"https?://\\S+", text)
    if not match:
        return None
    return match.group(0).rstrip(").,]")


def call_api(youtube_url: str) -> str:
    payload = dict(DEFAULT_PAYLOAD)
    payload["url"] = youtube_url
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        API_URL,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        body = resp.read().decode("utf-8", errors="replace")
        content_type = resp.headers.get("Content-Type", "")
    if "application/json" in content_type:
        try:
            obj = json.loads(body)
        except json.JSONDecodeError:
            obj = None
        if obj is not None:
            found = _find_url_in_json(obj)
            if found:
                return found
    found = _find_url_in_text(body)
    if found:
        return found
    raise RuntimeError("No downloadable link found in API response.")


def download_file(url: str, out_dir: str) -> str:
    os.makedirs(out_dir, exist_ok=True)
    parsed = urllib.parse.urlsplit(url)
    safe_path = urllib.parse.quote(parsed.path)
    safe_query = urllib.parse.quote_plus(parsed.query, safe="=&")
    safe_url = urllib.parse.urlunsplit(
        (parsed.scheme, parsed.netloc, safe_path, safe_query, parsed.fragment)
    )
    filename = os.path.basename(parsed.path) or "download.bin"
    out_path = os.path.join(out_dir, filename)
    req = urllib.request.Request(safe_url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=300) as resp, open(out_path, "wb") as f:
        while True:
            chunk = resp.read(1024 * 1024)
            if not chunk:
                break
            f.write(chunk)
    return out_path


def main() -> int:
    def safe_print(text: str, *, err: bool = False) -> None:
        stream = sys.stderr if err else sys.stdout
        try:
            stream.buffer.write((text + "\n").encode("utf-8", errors="backslashreplace"))
            stream.buffer.flush()
        except Exception:
            # Fallback to normal print if buffer isn't available.
            print(text, file=stream)
    if len(sys.argv) != 2:
        safe_print("Usage: python batch_yt_music_download.py <urls.txt>", err=True)
        return 2
    url_file = sys.argv[1]
    if not os.path.isfile(url_file):
        safe_print(f"File not found: {url_file}", err=True)
        return 2

    for youtube_url in iter_urls(url_file):
        try:
            download_url = call_api(youtube_url)
            out_path = download_file(download_url, OUT_DIR)
            safe_print(f"OK {youtube_url} -> {out_path}")
        except Exception as exc:
            safe_print(f"FAIL {youtube_url} -> {exc}", err=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
