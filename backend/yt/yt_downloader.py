import re
import uuid
from pathlib import Path

import yt_dlp


def _normalize_quality(mode, quality):
    text = str(quality).strip().lower()
    if mode == "audio":
        level = {"low": 128, "middle": 192, "high": 256, "max": 320}
        if text in level:
            return level[text]
        return int(text)

    # video
    level = {"low": 480, "middle": 720, "high": 1080, "max": 2160}
    if text in level:
        return level[text]
    return int(text)


def _sanitize(title: str) -> str:
    """공백→대시, 특수문자 제거, 최대 40자"""
    title = title.strip()
    title = re.sub(r"\s+", "-", title)           # 공백 → -
    title = re.sub(r"[^\w\-]", "", title)         # 특수문자 제거 (한글/영문/숫자/-_ 유지)
    title = re.sub(r"-{2,}", "-", title)          # 연속 대시 정리
    return title[:40].strip("-")


def _resolve_url(url: str) -> tuple[str, str]:
    """
    URL에서 실제 단일 영상 URL과 제목을 반환.
    플레이리스트면 첫 번째 항목만 사용.
    """
    ydl_opts = {"quiet": True, "skip_download": True, "noplaylist": False}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)

    # 플레이리스트 처리: entries가 있고 2개 이상이면 첫 번째만
    if "entries" in info:
        entries = [e for e in info["entries"] if e]  # None 필터
        if not entries:
            raise ValueError("플레이리스트가 비어 있습니다.")
        info = entries[0]  # 항상 첫 번째만

    video_url = info.get("webpage_url") or info.get("url") or url
    title = info.get("title", "untitled")
    return video_url, title


def download(url, mode="video", quality="high", output_dir="."):
    mode = mode.strip().lower()
    if mode not in {"audio", "video"}:
        raise ValueError("mode must be one of: audio, video")
    q = _normalize_quality(mode, quality)

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # 단일 영상 URL + 제목 확보 (플레이리스트 → 첫 항목)
    video_url, title = _resolve_url(url)
    stem = f"{_sanitize(title)}-{uuid.uuid4().hex[:8]}"

    before_files = {p.name for p in output_path.glob("*") if p.is_file()}

    if mode == "audio":
        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": str(output_path / f"{stem}.%(ext)s"),
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": str(q)
            }]
        }
    else:  # video
        ydl_opts = {
            "format": f"bestvideo[height<={q}]+bestaudio/best",
            "merge_output_format": "mp4",
            "outtmpl": str(output_path / f"{stem}.%(ext)s")
        }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([video_url])

    after_files = [p for p in output_path.glob("*") if p.is_file() and p.name not in before_files]
    if not after_files:
        ext = "mp3" if mode == "audio" else "mp4"
        after_files = sorted(output_path.glob(f"*.{ext}"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not after_files:
        raise RuntimeError("Download finished but output file was not found")

    result = max(after_files, key=lambda p: p.stat().st_mtime)
    print("downloaded:", result.name)
    return result


def main():
    url = input("유튜브 URL: ")

    mode = input("모드 선택 (video / audio) [video]: ").strip().lower()
    if mode == "":
        mode = "video"

    if mode == "audio":
        quality = input("음질 kbps (320/256/192/128) [192]: ").strip() or "192"
    else:
        quality = input("최대 화질 (2160/1440/1080/720) [1080]: ").strip() or "1080"

    print("\n다운로드 시작...\n")
    download(url, mode, quality)
    print("\n다운로드 완료!")


if __name__ == "__main__":
    main()
