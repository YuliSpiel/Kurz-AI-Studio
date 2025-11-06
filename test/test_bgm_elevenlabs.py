#!/usr/bin/env python3
"""
ElevenLabs BGM 생성 API 진단 스크립트
Sound Effects API를 사용한 음악 생성 기능을 테스트합니다.
"""
import sys
import os
from pathlib import Path
import httpx
from dotenv import load_dotenv

# .env 파일 명시적으로 로드
env_path = Path(__file__).parent / ".env"
load_dotenv(env_path, override=True)


def test_bgm_generation():
    """BGM 생성 진단 테스트"""

    print("=" * 70)
    print("ElevenLabs BGM 생성 API 진단 (Sound Effects)")
    print("=" * 70)

    # API 키 확인 - 환경변수에서 직접 읽기
    api_key = os.getenv("ELEVENLABS_API_KEY", "")

    if not api_key:
        print("\n❌ ELEVENLABS_API_KEY가 설정되지 않았습니다.")
        return False

    print(f"\n✅ API 키 확인: {api_key[:15]}...{api_key[-10:]}")
    print(f"   전체 길이: {len(api_key)} 문자")

    # HTTP 클라이언트 생성
    client = httpx.Client(
        headers={"xi-api-key": api_key},
        timeout=60.0  # BGM 생성은 시간이 더 걸림
    )

    print("\n" + "=" * 70)
    print("테스트 1: 짧은 Ambient 음악 생성 (10초)")
    print("=" * 70)

    try:
        prompt = "calm and peaceful ambient atmospheric background music, instrumental, no vocals, looping"
        duration = 10

        print(f"프롬프트: {prompt}")
        print(f"길이: {duration}초")
        print("생성 중... (최대 60초 소요)")

        response = client.post(
            "https://api.elevenlabs.io/v1/sound-generation",
            json={
                "text": prompt,
                "duration_seconds": duration,
                "prompt_influence": 0.3
            }
        )

        print(f"\n상태 코드: {response.status_code}")

        if response.status_code == 200:
            print(f"✅ Ambient 음악 생성 성공!")
            print(f"   응답 크기: {len(response.content)} 바이트")

            # 테스트 파일 저장
            output_dir = Path("backend/app/data/bgm_test")
            output_dir.mkdir(parents=True, exist_ok=True)
            output_file = output_dir / "test_ambient_10s.mp3"

            with open(output_file, "wb") as f:
                f.write(response.content)

            print(f"   저장 위치: {output_file}")

        else:
            print(f"❌ 음악 생성 실패")
            print(f"   응답 헤더: {dict(response.headers)}")
            print(f"   응답 본문: {response.text[:500]}")
            return False

    except httpx.HTTPStatusError as e:
        print(f"❌ HTTP 오류 발생:")
        print(f"   상태 코드: {e.response.status_code}")
        print(f"   응답 헤더: {dict(e.response.headers)}")
        print(f"   응답 본문: {e.response.text[:500]}")
        return False
    except Exception as e:
        print(f"❌ 오류 발생: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False

    print("\n" + "=" * 70)
    print("테스트 2: 다양한 장르/무드 조합 테스트")
    print("=" * 70)

    test_cases = [
        {
            "name": "Cinematic",
            "prompt": "energetic and lively cinematic orchestral music, instrumental, no vocals, looping",
            "duration": 8,
            "filename": "test_cinematic_8s.mp3"
        },
        {
            "name": "Upbeat",
            "prompt": "happy and cheerful upbeat energetic music, instrumental, no vocals, looping",
            "duration": 5,
            "filename": "test_upbeat_5s.mp3"
        }
    ]

    for test_case in test_cases:
        print(f"\n▶ {test_case['name']} 테스트")
        print(f"   프롬프트: {test_case['prompt']}")
        print(f"   길이: {test_case['duration']}초")
        print("   생성 중...")

        try:
            response = client.post(
                "https://api.elevenlabs.io/v1/sound-generation",
                json={
                    "text": test_case["prompt"],
                    "duration_seconds": test_case["duration"],
                    "prompt_influence": 0.3
                }
            )

            if response.status_code == 200:
                output_file = output_dir / test_case["filename"]
                with open(output_file, "wb") as f:
                    f.write(response.content)

                print(f"   ✅ 성공! ({len(response.content)} 바이트) → {output_file}")
            else:
                print(f"   ⚠️  실패 (상태 코드: {response.status_code})")
                print(f"   응답: {response.text[:200]}")

        except Exception as e:
            print(f"   ⚠️  오류: {e}")

    print("\n" + "=" * 70)
    print("테스트 3: 최대 길이 테스트 (22초)")
    print("=" * 70)

    try:
        prompt = "mysterious and intriguing ambient atmospheric background music, instrumental, no vocals, looping"
        duration = 22  # ElevenLabs 최대 길이

        print(f"프롬프트: {prompt}")
        print(f"길이: {duration}초 (최대 길이)")
        print("생성 중... (최대 60초 소요)")

        response = client.post(
            "https://api.elevenlabs.io/v1/sound-generation",
            json={
                "text": prompt,
                "duration_seconds": duration,
                "prompt_influence": 0.3
            }
        )

        print(f"\n상태 코드: {response.status_code}")

        if response.status_code == 200:
            print(f"✅ 최대 길이 음악 생성 성공!")
            print(f"   응답 크기: {len(response.content)} 바이트")

            output_file = output_dir / "test_max_length_22s.mp3"
            with open(output_file, "wb") as f:
                f.write(response.content)

            print(f"   저장 위치: {output_file}")

        else:
            print(f"❌ 음악 생성 실패")
            print(f"   응답: {response.text[:500]}")
            return False

    except Exception as e:
        print(f"❌ 오류 발생: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False

    print("\n" + "=" * 70)
    print("📊 테스트 요약")
    print("=" * 70)

    # 생성된 파일 목록
    bgm_files = list(output_dir.glob("*.mp3"))
    print(f"\n생성된 파일: {len(bgm_files)}개")
    for file in sorted(bgm_files):
        size_kb = file.stat().st_size / 1024
        print(f"  - {file.name} ({size_kb:.1f} KB)")

    print("\n" + "=" * 70)
    print("🎉 모든 테스트 통과!")
    print("=" * 70)

    print("\n💡 사용 팁:")
    print("  - ElevenLabs Sound Effects API는 최대 22초까지 생성 가능")
    print("  - 더 긴 음악은 여러 조각을 생성 후 이어붙이기 필요")
    print("  - prompt_influence는 0-1 사이 (0.3 추천)")
    print("  - 'looping' 키워드를 추가하면 반복에 적합한 음악 생성")

    return True


if __name__ == "__main__":
    try:
        success = test_bgm_generation()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  사용자에 의해 중단됨")
        sys.exit(130)
    except Exception as e:
        print(f"\n\n❌ 예상치 못한 오류: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
