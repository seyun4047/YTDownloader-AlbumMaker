import json
from google import genai
from google.genai import types


# 2️⃣ Gemini 설정 (v1 SDK)
MODEL_ID = "gemini-3.1-flash-lite-preview"
import os

key1 = os.getenv("GEMINI_API_KEY_1", "")
key2 = os.getenv("GEMINI_API_KEY_2", "")
key3 = os.getenv("GEMINI_API_KEY_3", "")

API_KEYS = [k for k in (key1, key2, key3) if k]


def ai(prompt):
    last_exc = None
    for idx, api_key in enumerate(API_KEYS, start=1):
        try:
            client = genai.Client(api_key=api_key)
            response = client.models.generate_content(
                model=MODEL_ID,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.0,
                ),
            )
            return json.loads(response.text)
        except Exception as exc:
            last_exc = exc
            print(f"❌ AI 호출 오류 (key {idx}): {exc}")
            continue

    print(f"❌ AI 호출 오류: 모든 키 실패 ({last_exc})")
    return []
