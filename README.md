# Mutzin Youtube Downloader

# [TRY IT!](https://yt.mutzin.com)(click me)

# Youtube To Album!
This project is a centralized Youtube downloader featuring a separated frontend (React + Vite)<br>
and backend (FastAPI + yt-dlp/ffmpeg). It allows users to download standard audio/video<br>
and also includes an AI-powered feature to automatically fetch album artwork, lyrics, and metadata using the Gemini API.

<img width="1639" height="1041" alt="스크린샷 2026-03-11 21 04 16" src="https://github.com/user-attachments/assets/5dda67ac-8b3e-4a34-ae6f-a68301522205" />

## 🚀 Features

### Frontend (React + Vite)
- **Audio Download:** Quickly extract MP3 high-quality audio from any YouTube Video.
- **Video Download:** Select quality tiers to download raw YouTube videos (MP4).
- **AI Music Generation:** Automatically fetches cover images, injects metadata, and leverages Gemini API to identify songs and embed `.lrc` sync lyrics directly into your downloaded MP3 files.
- **Interactive UI:** Provides distinct visual flows, feedback loading states, and options to seamlessly preview contents.

### Backend (FastAPI + yt-dlp)
- **Scalable Endpoint:** Powered by FastAPI providing async-downloads relying on `yt-dlp`.
- **Lyric & Cover Embeds:** Embeds covers, album info natively into MP3 files using `mutagen`.
- **AI Fallbacks:** Rotates through multiple API keys ensuring limits aren't exceeded when heavily translating / summarizing contexts via Google Gemini.

---

## ⚙️ Setup Instructions

### 1. Environment Variables Configuration
Before starting the application, you must configure the environment variables.

Copy the `.env.sample` into `.env` at the root of the project:
```bash
cp .env.sample .env
```

Fill in your domain/IP and Gemini API keys inside the `.env`:

```dotenv
# Backend & Frontend Ports
BACKEND_PORT=10210
FRONTEND_PORT=10211

# URLs (Replace YOUR_DOMAIN_OR_IP with your server ip/domain)
APP_URL="http://YOUR_DOMAIN_OR_IP:10210"
PUBLIC_FRONT_URL="http://YOUR_DOMAIN_OR_IP:10211"

# Gemini API Keys (Frontend)
GEMINI_API_KEY="YOUR_FRONTEND_GEMINI_API_KEY"

# Gemini API Keys (Backend AI Caller - up to 3 keys)
GEMINI_API_KEY_1="YOUR_BACKEND_GEMINI_API_KEY_1"
GEMINI_API_KEY_2="YOUR_BACKEND_GEMINI_API_KEY_2"
GEMINI_API_KEY_3="YOUR_BACKEND_GEMINI_API_KEY_3"
```

### 2. Starting the Application

The application is fully dockerized. To start both the frontend and backend services:

```bash
docker-compose up -d --build
```

### 3. Stopping the Application
To shut down the application:
```bash
docker-compose down
```

---

## 📡 API Reference & cURL Usage

Assuming your backend is running locally on port `10210`, you can interact with the backend using the following cURL examples. Make sure to replace `YOUR_YOUTUBE_URL` with a valid YouTube link.

### 1. Audio Download (MP3)
Downloads just the audio format of the YouTube URL.
```bash
curl -X POST "http://localhost:10210/yt/audio" \
     -H "Content-Type: application/json" \
     -d '{
           "url": "YOUR_YOUTUBE_URL",
           "quality": "high"
         }'
```

### 2. Video Download (MP4)
Downloads the MP4 video using specified quality tiers (e.g. `low`, `middle`, `high`, `max`).
```bash
curl -X POST "http://localhost:10210/yt/video" \
     -H "Content-Type: application/json" \
     -d '{
           "url": "YOUR_YOUTUBE_URL",
           "quality": "high"
         }'
```

### 3. Music Download (MP3 with Metadata / Lyrics)
Uses AI via Gemini to gather metadata and embeds it along with downloading `.lrc` lyrics directly into the MP3 ID3 tags.
```bash
curl -X POST "http://localhost:10210/yt/music" \
     -H "Content-Type: application/json" \
     -d '{
           "url": "YOUR_YOUTUBE_URL",
           "quality": "high",
           "lyric": true,
           "metadata": true
         }'
```

### 4. Fetch the Rendered File
The POST request will yield a URL containing the file hash or name. Utilize that location via a standard GET:
```bash
# Example Response from POST
# {
#   "status": true,
#   "url": "http://localhost:10210/download/yt_music/example.mp3"
# }

curl -O -J "http://localhost:10210/download/yt_music/example.mp3"
```
