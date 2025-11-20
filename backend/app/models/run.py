"""
Run model for video generation tracking.
"""
from sqlalchemy import Column, String, Integer, DateTime, Enum as SQLEnum, Boolean, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from app.database import Base


class RunMode(str, enum.Enum):
    """Video generation modes"""
    GENERAL = "general"
    STORY = "story"
    AD = "ad"


class RunState(str, enum.Enum):
    """Run states matching FSM"""
    IDLE = "IDLE"
    PLOT_GENERATION = "PLOT_GENERATION"
    PLOT_REVIEW = "PLOT_REVIEW"
    ASSET_GENERATION = "ASSET_GENERATION"
    LAYOUT_REVIEW = "LAYOUT_REVIEW"
    RENDERING = "RENDERING"
    QA = "QA"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class Run(Base):
    __tablename__ = "runs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id = Column(String, unique=True, index=True, nullable=False)  # "20241119_1230_프롬프트"
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)

    # Run configuration
    mode = Column(SQLEnum(RunMode), nullable=False)
    prompt = Column(Text, nullable=False)
    num_cuts = Column(Integer, default=3)
    num_characters = Column(Integer, default=1)

    # State tracking
    state = Column(SQLEnum(RunState), default=RunState.IDLE, nullable=False)
    progress = Column(Integer, default=0)  # 0-100

    # Output
    video_url = Column(String, nullable=True)  # S3 URL (나중에 추가)
    thumbnail_url = Column(String, nullable=True)

    # Metadata
    is_public = Column(Boolean, default=False)  # 커뮤니티 공개 여부
    view_count = Column(Integer, default=0)
    credits_used = Column(Integer, default=1)  # 사용한 크레딧

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    # Relationship
    # user = relationship("User", back_populates="runs")

    def __repr__(self):
        return f"<Run(id={self.id}, run_id={self.run_id}, user_id={self.user_id}, state={self.state})>"
