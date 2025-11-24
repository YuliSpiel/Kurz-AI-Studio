# Pro Mode - Kling AI Video Generation

## Overview

Pro 모드는 Kling AI의 Image-to-Video 기능을 활용하여 실제 영상을 생성하는 프리미엄 기능입니다.

## Architecture

### Flow
```
사용자 입력 → 프롬프트 증강 → plot.json 생성
                              ↓
            에셋 생성 (병렬)
            ├─ Gemini: 장면당 이미지 2장 (start, end)
            ├─ TTS: 장면별 음성
            └─ BGM: 전역 배경음악
                              ↓
            Kling API (장면별)
            - start_image + end_image → 5초 영상
                              ↓
            감독: 합성
            - 영상 + TTS (길면 freeze frame 추가)
            - 자막 오버레이
            - BGM 믹싱
                              ↓
            final_video.mp4
```

### Key Constraints
- **Kling 영상 길이**: 5초 고정
- **TTS 분량**: ~20자/장면 (5초 내 읽을 수 있는 분량)
- **TTS > 5초**: 마지막 프레임에서 freeze frame 추가
- **이미지 생성**: Gemini (기존 유지)

## Data Schema

### plot.json (Pro Mode)
```json
{
  "mode": "pro",
  "title": "고양이의 하루",
  "bgm_prompt": "calm lo-fi ambient, peaceful morning vibes",
  "characters": [
    {
      "char_id": "cat",
      "name": "나비",
      "description": "하얀 털의 귀여운 고양이, 파란 눈"
    }
  ],
  "scenes": [
    {
      "scene_id": "scene_1",
      "start_frame_prompt": "{cat}가 창가에 앉아있다, 아침 햇살이 비친다, 평화로운 분위기",
      "end_frame_prompt": "{cat}가 하품을 하며 기지개를 편다, 창밖을 바라본다",
      "text": "오늘도 평화로운 아침이 밝았어요",
      "speaker": "narrator",
      "duration_ms": 5000,
      "tts_duration_ms": null,
      "video_url": null,
      "start_image_url": null,
      "end_image_url": null,
      "audio_url": null
    },
    {
      "scene_id": "scene_2",
      "start_frame_prompt": "{cat}가 밥그릇 앞에 앉아있다, 기대하는 표정",
      "end_frame_prompt": "{cat}가 맛있게 밥을 먹고 있다, 행복한 표정",
      "text": "배가 고팠나 봐요, 아침밥 시간!",
      "speaker": "narrator",
      "duration_ms": 5000,
      "tts_duration_ms": null,
      "video_url": null,
      "start_image_url": null,
      "end_image_url": null,
      "audio_url": null
    }
  ]
}
```

### Output Directory Structure
```
backend/app/data/outputs/{run_id}/
   characters.json
   plot.json
   layout.json

   # Images (Pro mode: 2 per scene)
   scene_1_start.png
   scene_1_end.png
   scene_2_start.png
   scene_2_end.png
   ...

   # Videos (Kling generated)
   videos/
      scene_1.mp4
      scene_2.mp4
      ...

   # Audio
   audio/
      scene_1_narrator.mp3
      scene_2_narrator.mp3
      global_bgm.mp3

   # Final output
   final_video.mp4
```

## Implementation Details

### 1. Plot Generator (Pro Mode)

LLM 프롬프트에 추가 지시:
- 장면당 ~20자 자막 (5초 내 읽을 수 있는 분량)
- `start_frame_prompt`와 `end_frame_prompt` 생성
- 두 프롬프트는 연속적인 동작을 묘사해야 함

### 2. Designer Task (Pro Mode)

```python
# 일반 모드: 장면당 1장
if mode == "general":
    generate_image(scene.image_prompt)

# Pro 모드: 장면당 2장
if mode == "pro":
    generate_image(scene.start_frame_prompt)  # scene_X_start.png
    generate_image(scene.end_frame_prompt)    # scene_X_end.png
```

### 3. Kling API Client

```python
class KlingClient:
    async def image_to_video(
        self,
        start_image_path: str,
        end_image_path: str,
        duration: int = 5  # seconds
    ) -> str:
        """
        Generate video from start and end frames.
        Returns path to generated video.
        """
        pass
```

### 4. Director Task (Pro Mode)

```python
def render_pro_mode(scenes, bgm_path):
    clips = []

    for scene in scenes:
        # Load Kling-generated video (5 seconds)
        video = VideoFileClip(scene.video_url)

        # Load TTS audio
        tts = AudioFileClip(scene.audio_url)

        # If TTS > 5 seconds, add freeze frame
        if tts.duration > video.duration:
            extra_duration = tts.duration - video.duration
            last_frame = video.get_frame(video.duration - 0.01)
            freeze = ImageClip(last_frame).with_duration(extra_duration)
            video = concatenate_videoclips([video, freeze])

        # Add subtitle
        video = add_subtitle(video, scene.text)

        # Set audio (TTS)
        video = video.with_audio(tts)

        clips.append(video)

    # Concatenate all scenes
    final = concatenate_videoclips(clips)

    # Add BGM
    bgm = AudioFileClip(bgm_path).with_volume_scaled(0.3)
    bgm = bgm.loop(duration=final.duration)
    final = final.with_audio(CompositeAudioClip([final.audio, bgm]))

    return final
```

## API Endpoints

Pro 모드는 기존 API를 그대로 사용하며, `mode: "pro"` 파라미터로 구분합니다.

```
POST /api/runs
{
  "mode": "pro",
  "prompt": "고양이의 하루",
  ...
}
```

## Cost Estimation

| Item | Cost per Scene | 5 Scenes Total |
|------|----------------|----------------|
| Gemini Image (x2) | ~$0.02 | ~$0.10 |
| Kling Video | ~$0.10-0.50 | ~$0.50-2.50 |
| TTS | ~$0.01 | ~$0.05 |
| BGM | ~$0.05 | ~$0.05 |
| **Total** | | **~$0.70-2.70** |

## FSM States

Pro 모드도 동일한 FSM을 사용합니다:
```
INIT → PLOT_GENERATION → ASSET_GENERATION → RENDERING → QA → END
```

단, ASSET_GENERATION 단계에서:
- 이미지 2장/장면 생성
- Kling API 호출 (RENDERING 전 또는 RENDERING 내)

## Error Handling

1. **Kling API 실패**: 해당 장면을 이미지 슬라이드쇼로 폴백
2. **TTS 생성 실패**: 기존과 동일하게 처리
3. **이미지 생성 실패**: 기존과 동일하게 처리

## Configuration

```python
# backend/app/config.py
class Settings:
    # Kling API
    KLING_API_KEY: str = ""
    KLING_API_BASE_URL: str = "https://api.kling.ai/v1"
    KLING_VIDEO_DURATION: int = 5  # seconds

    # Pro mode
    PRO_MODE_MAX_TEXT_LENGTH: int = 25  # chars per scene
```
