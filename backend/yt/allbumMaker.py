import json
import re
import uuid
from pathlib import Path

import yt_dlp
from mutagen.id3 import ID3, TALB, TCOM, TCON, TIT2, TPE1, TRCK, TDRC

from yt.ai_caller import ai
from yt.thumbnailadder import add_thumbnail_to_mp3
from yt.thumbnaildownloader import download_thumbnail


def _pick_first_entry(info: dict) -> dict:
    if "entries" in info:
        entries = [e for e in info["entries"] if e]
        if not entries:
            raise ValueError("플레이리스트가 비어 있습니다.")
        return entries[0]
    return info


def _sanitize_filename(title: str) -> str:
    title = title.strip()
    title = re.sub(r"\s+", "", title)  # remove spaces
    title = re.sub(r"[^\w\-가-힣]", "", title)  # keep word chars, dash, korean
    title = re.sub(r"-{2,}", "-", title)
    return title[:80] or "untitled"


def _basic_split(title: str, uploader: str | None) -> dict:
    artist = uploader or "Unknown"
    song = title or "Unknown"
    if " - " in title:
        left, right = title.split(" - ", 1)
        artist = left.strip() or artist
        song = right.strip() or song
    return {
        "title": song,
        "artist": artist,
        "album": "",
        "composer": "",
        "genre": "",
        "year": "",
        "track_number": "",
    }


def _ai_parse_metadata(title: str, uploader: str | None, upload_date: str | None) -> dict:
    prompt = {
        "task": "Parse the YouTube video title into music metadata.",
        "title": title,
        "uploader": uploader,
        "upload_date": upload_date,
        "return_json_only": True,
        "schema": {
            "title": "string",
            "artist": "string",
            "album": "string",
            "composer": "string",
            "genre": "string",
            "year": "string",
            "track_number": "string",
        },
        "rules": [
            "Return ONLY JSON.",
            "If unknown, return empty string.",
        ],
    }
    try:
        result = ai(json.dumps(prompt, ensure_ascii=False))
        if isinstance(result, dict):
            return {
                "title": str(result.get("title", "")).strip(),
                "artist": str(result.get("artist", "")).strip(),
                "album": str(result.get("album", "")).strip(),
                "composer": str(result.get("composer", "")).strip(),
                "genre": str(result.get("genre", "")).strip(),
                "year": str(result.get("year", "")).strip(),
                "track_number": str(result.get("track_number", "")).strip(),
            }
    except Exception:
        pass
    return {}


def _normalize_year(upload_date: str | None, year: str | None) -> str:
    if year and year.isdigit() and len(year) == 4:
        return year
    if upload_date and upload_date.isdigit() and len(upload_date) >= 4:
        return upload_date[:4]
    return ""


def _write_id3(mp3_path: Path, meta: dict) -> None:
    try:
        tags = ID3(mp3_path.as_posix())
    except Exception:
        tags = ID3()

    def _set(frame):
        tags.delall(frame.__class__.__name__)
        tags.add(frame)

    if meta.get("title"):
        _set(TIT2(encoding=3, text=meta["title"]))
    if meta.get("artist"):
        _set(TPE1(encoding=3, text=meta["artist"]))
    if meta.get("album"):
        _set(TALB(encoding=3, text=meta["album"]))
    if meta.get("composer"):
        _set(TCOM(encoding=3, text=meta["composer"]))
    if meta.get("genre"):
        _set(TCON(encoding=3, text=meta["genre"]))
    if meta.get("year"):
        _set(TDRC(encoding=3, text=meta["year"]))
    if meta.get("track_number"):
        _set(TRCK(encoding=3, text=meta["track_number"]))

    tags.save(mp3_path.as_posix())


def build_album_from_youtube(url: str, output_root: Path) -> Path:
    ydl_opts = {"quiet": True, "skip_download": True, "noplaylist": False}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
    info = _pick_first_entry(info)

    video_url = info.get("webpage_url") or info.get("url") or url
    title = info.get("title", "untitled")
    uploader = info.get("uploader")
    upload_date = info.get("upload_date")

    meta = _ai_parse_metadata(title, uploader, upload_date)
    if not meta:
        meta = _basic_split(title, uploader)

    if not meta.get("title"):
        meta["title"] = title
    if not meta.get("artist"):
        meta["artist"] = uploader or ""
    meta["year"] = _normalize_year(upload_date, meta.get("year"))

    safe_title = _sanitize_filename(meta["title"])
    album_dir = output_root / uuid.uuid4().hex
    album_dir.mkdir(parents=True, exist_ok=True)
    target_path = album_dir / f"{safe_title}.mp3"

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": target_path.as_posix().replace(".mp3", ".%(ext)s"),
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "256",
        }],
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([video_url])

    # yt_dlp may still choose another ext before postprocess
    if not target_path.exists():
        candidates = sorted(album_dir.glob("*.mp3"), key=lambda p: p.stat().st_mtime, reverse=True)
        if not candidates:
            raise RuntimeError("MP3 output file was not found")
        target_path = candidates[0]

    _write_id3(target_path, meta)

    thumb_path = album_dir / "cover.jpg"
    download_thumbnail(video_url, thumb_path.as_posix())
    add_thumbnail_to_mp3(target_path.as_posix(), thumb_path.as_posix())

    return target_path

