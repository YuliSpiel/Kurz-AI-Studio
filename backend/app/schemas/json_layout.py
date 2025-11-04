"""
JSON layout schema for final shorts composition.
Defines the structure for timeline, scenes, characters, and assets.
"""
from pydantic import BaseModel, Field
from typing import List, Literal, Optional


class Character(BaseModel):
    """Character definition."""
    char_id: str = Field(description="예: char_1, char_2")
    name: str = Field(description="캐릭터 이름")
    persona: str = Field(description="성격/설정")
    voice_profile: str = Field(description="음성 프로필 ID or 설명")
    seed: int = Field(description="고정 seed for consistency")


class ImageSlot(BaseModel):
    """Image slot positioning in scene."""
    slot_id: Literal["left", "center", "right"]
    type: Literal["character", "background", "prop"]
    ref_id: Optional[str] = Field(None, description="char_id or asset ID")
    image_url: str = Field(description="생성된 이미지 경로")
    z_index: int = Field(default=0, description="레이어 순서")


class Subtitle(BaseModel):
    """Subtitle definition."""
    position: Literal["top", "center", "bottom"]
    text: str
    style: str = Field(default="default", description="스타일 프리셋")
    start_ms: int = Field(description="자막 시작 시간(ms)")
    duration_ms: int = Field(description="자막 지속 시간(ms)")


class SFX(BaseModel):
    """Sound effect definition."""
    sfx_id: str
    tags: List[str] = Field(description="무드 태그 (예: ['soft_chime', 'emotional'])")
    audio_url: str = Field(description="SFX 파일 경로")
    start_ms: int
    volume: float = Field(default=0.5, ge=0.0, le=1.0)


class DialogueLine(BaseModel):
    """Dialogue line with timing."""
    line_id: str
    char_id: str
    text: str
    emotion: str = Field(default="neutral", description="감정 (예: neutral, happy, sad)")
    audio_url: str = Field(description="TTS 음성 파일 경로")
    start_ms: int
    duration_ms: int


class BGM(BaseModel):
    """Background music definition."""
    bgm_id: str
    genre: str
    mood: str
    audio_url: str = Field(description="BGM 파일 경로")
    start_ms: int
    duration_ms: int
    volume: float = Field(default=0.3, ge=0.0, le=1.0)


class Scene(BaseModel):
    """Scene definition with all components."""
    scene_id: str
    sequence: int = Field(description="씬 순서")
    duration_ms: int

    # Visual
    images: List[ImageSlot] = Field(description="이미지 슬롯 배치")
    subtitles: List[Subtitle] = Field(default_factory=list)

    # Audio
    dialogue: List[DialogueLine] = Field(default_factory=list)
    bgm: Optional[BGM] = None
    sfx: List[SFX] = Field(default_factory=list)

    # Scene settings
    bg_seed: int = Field(description="배경 seed")
    transition: str = Field(default="fade", description="전환 효과")


class Timeline(BaseModel):
    """Overall timeline metadata."""
    total_duration_ms: int
    aspect_ratio: str = Field(default="9:16")
    fps: int = Field(default=30)
    resolution: str = Field(default="1080x1920")


class ShortsJSON(BaseModel):
    """Complete JSON schema for shorts composition."""

    project_id: str
    title: str
    mode: Literal["story", "ad"]

    timeline: Timeline
    characters: List[Character]
    scenes: List[Scene]

    # Global assets
    global_bgm: Optional[BGM] = Field(None, description="전체 배경음악 (씬별 BGM 우선)")

    metadata: dict = Field(
        default_factory=dict,
        description="추가 메타데이터 (생성 모델, 파라미터 등)"
    )
