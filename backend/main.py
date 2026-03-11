import asyncio
import os
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

from yt.audiolyricadder import add_lyrics_to_mp3
from yt.extlrc import transcribe_to_lrc
from yt.thumbnailadder import add_thumbnail_to_mp3
from yt.thumbnaildownloader import download_thumbnail
from yt.yt_downloader import download as yt_download
from yt.allbumMaker import build_album_from_youtube

# ── 환경 변수 ──────────────────────────────────────────────
PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL", "http://seyun4047.iptime.org:10210").rstrip("/")
DOWNLOAD_DIR = Path(os.getenv("DOWNLOAD_DIR", "./downloads"))
FRONTEND_URL = os.getenv("PUBLIC_FRONT_URL", "http://seyun4047.iptime.org:10211")

YT_SUBDIR = "yt"
YT_MUSIC_SUBDIR = "yt_music"

DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

# ── 동시 작업 제한 (세마포어) ────────────────────────────────
_semaphore = asyncio.Semaphore(5)


async def run_job_with_limit(fn, *args, **kwargs):
    async with _semaphore:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: fn(*args, **kwargs))


# ── FastAPI ──────────────────────────────────────────────
app = FastAPI(title="mutzin-ytdown")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL, "http://localhost:10211"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)


# ── 스키마 ────────────────────────────────────────────────
class YtRequest(BaseModel):
    url: str
    quality: str = "high"  # low | middle | high | max | 숫자

    def normalized_quality(self) -> str:
        return self.quality.strip().lower()


class YtMusicRequest(YtRequest):
    lyric: bool = False
    metadata: bool = False


class DownloadResponse(BaseModel):
    status: bool
    url: str


# ── 헬퍼 ─────────────────────────────────────────────────
def build_download_url(request: Request, relative_path: str) -> str:
    base = PUBLIC_BASE_URL or str(request.base_url).rstrip("/")
    return f"{base}/download/{relative_path}"


# ── 내부 공통 함수 ────────────────────────────────────────
async def _run_yt_download(request: Request, body: YtRequest, mode: str) -> DownloadResponse:
    quality = body.normalized_quality()
    output_dir = DOWNLOAD_DIR / YT_SUBDIR
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        output_path = await run_job_with_limit(
            yt_download,
            body.url.strip(),
            mode,
            quality,
            output_dir,
        )
    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to download media: {exc}") from exc

    relative_path = f"{YT_SUBDIR}/{output_path.name}"
    return DownloadResponse(status=True, url=build_download_url(request, relative_path))


# ── 엔드포인트 ────────────────────────────────────────────
@app.get("/")
async def root():
    return {"message": "mutzin-ytdown API is running"}


@app.post("/yt/audio", response_model=DownloadResponse)
async def yt_audio(request: Request, body: YtRequest):
    """유튜브 URL → MP3 다운로드 링크 반환"""
    return await _run_yt_download(request, body, "audio")


@app.post("/yt/video", response_model=DownloadResponse)
async def yt_video(request: Request, body: YtRequest):
    """유튜브 URL → MP4 다운로드 링크 반환"""
    return await _run_yt_download(request, body, "video")


@app.post("/yt/music", response_model=DownloadResponse)
async def yt_music(request: Request, body: YtMusicRequest):
    """유튜브 URL → MP3 + (가사 / 메타데이터 임베드) 다운로드 링크 반환"""
    quality = body.normalized_quality()
    output_dir = DOWNLOAD_DIR / YT_MUSIC_SUBDIR
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        if body.metadata:
            mp3_path = await run_job_with_limit(build_album_from_youtube, body.url.strip(), output_dir)
        else:
            mp3_path = await run_job_with_limit(yt_download, body.url.strip(), "audio", quality, output_dir)

        if body.lyric:
            lrc_path = mp3_path.parent / f"{mp3_path.stem}.lrc"
            await run_job_with_limit(transcribe_to_lrc, str(mp3_path), str(lrc_path))
            await run_job_with_limit(add_lyrics_to_mp3, str(mp3_path), str(lrc_path))

    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to build yt_music file: {exc}") from exc

    relative_path = mp3_path.relative_to(DOWNLOAD_DIR).as_posix()
    return DownloadResponse(status=True, url=build_download_url(request, relative_path))


@app.get("/download/{filepath:path}", name="download_file")
async def download_file(filepath: str):
    """생성된 파일을 실제로 다운로드"""
    file_path = (DOWNLOAD_DIR / filepath).resolve()
    download_root = DOWNLOAD_DIR.resolve()
    if download_root not in file_path.parents and file_path != download_root:
        raise HTTPException(status_code=400, detail="Invalid download path")
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(path=file_path, filename=file_path.name, media_type="application/octet-stream")
