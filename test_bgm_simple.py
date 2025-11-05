#!/usr/bin/env python3
"""
간단한 BGM 생성 테스트 - ElevenLabs Sound Effects API 확인
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# .env 파일 로드 (override=True로 환경변수 덮어쓰기)
load_dotenv(override=True)

# 직접 httpx로 테스트
import httpx

api_key = os.getenv("ELEVENLABS_API_KEY")
print(f"API 키: {api_key[:15]}...{api_key[-10:]}")

client = httpx.Client(
    headers={"xi-api-key": api_key},
    timeout=60.0  # BGM 생성은 시간이 더 걸림
)

# BGM 생성 요청 (ElevenLabs Sound Effects API)
prompt = "calm and peaceful ambient atmospheric background music, instrumental, no vocals, looping"
duration_seconds = 10  # 10초 테스트

print(f"\n생성 중: {prompt}")
print(f"길이: {duration_seconds}초")

response = client.post(
    "https://api.elevenlabs.io/v1/sound-generation",
    json={
        "text": prompt,
        "duration_seconds": duration_seconds,
        "prompt_influence": 0.3
    }
)

print(f"\n상태 코드: {response.status_code}")

if response.status_code == 200:
    print(f"✅ 성공! 응답 크기: {len(response.content)} 바이트")

    # 저장
    output_file = Path("backend/app/data/bgm_test/simple_test.mp3")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_bytes(response.content)
    print(f"저장 위치: {output_file}")
else:
    print(f"❌ 실패: {response.text}")
