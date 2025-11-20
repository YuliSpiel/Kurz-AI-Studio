"""
Runs router for video generation management.
"""
import logging
import shutil
from typing import List
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.database import get_db
from app.models.user import User
from app.models.run import Run as RunModel
from app.utils.auth import get_current_user
from pydantic import BaseModel
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter()


class RunListItem(BaseModel):
    """Run list item for library view."""
    id: str
    run_id: str
    prompt: str
    mode: str
    state: str
    progress: int
    video_url: str | None
    thumbnail_url: str | None
    created_at: datetime

    class Config:
        from_attributes = True


@router.get("/runs", response_model=List[RunListItem])
async def get_my_runs(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    limit: int = 50,
    offset: int = 0
):
    """
    Get current user's video generation runs.
    Returns most recent runs first.

    Args:
        current_user: Authenticated user (from JWT)
        db: Database session
        limit: Maximum number of runs to return (default: 50)
        offset: Pagination offset (default: 0)

    Returns:
        List of user's runs
    """
    logger.info(f"[USER:{current_user.username}] Fetching runs (limit={limit}, offset={offset})")

    # Query runs for current user, ordered by creation date (newest first)
    result = await db.execute(
        select(RunModel)
        .where(RunModel.user_id == current_user.id)
        .order_by(desc(RunModel.created_at))
        .limit(limit)
        .offset(offset)
    )

    runs = result.scalars().all()

    logger.info(f"[USER:{current_user.username}] Found {len(runs)} runs")

    # Convert to response model
    return [
        RunListItem(
            id=str(run.id),
            run_id=run.run_id,
            prompt=run.prompt,
            mode=run.mode.value,
            state=run.state.value,
            progress=run.progress,
            video_url=run.video_url,
            thumbnail_url=run.thumbnail_url,
            created_at=run.created_at
        )
        for run in runs
    ]


@router.delete("/runs/{run_id}")
async def delete_run(
    run_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a run and its associated files.
    Only the owner can delete their runs.

    Args:
        run_id: The run_id to delete
        current_user: Authenticated user (from JWT)
        db: Database session

    Returns:
        Success message

    Raises:
        404: Run not found
        403: Not authorized to delete this run
    """
    logger.info(f"[USER:{current_user.username}] Deleting run: {run_id}")

    # Find the run
    result = await db.execute(
        select(RunModel).where(RunModel.run_id == run_id)
    )
    run = result.scalars().first()

    if not run:
        logger.warning(f"[USER:{current_user.username}] Run not found: {run_id}")
        raise HTTPException(status_code=404, detail="Run not found")

    # Check ownership
    if run.user_id != current_user.id:
        logger.warning(f"[USER:{current_user.username}] Unauthorized delete attempt for run: {run_id}")
        raise HTTPException(status_code=403, detail="Not authorized to delete this run")

    # Delete output folder if exists
    output_dir = Path(f"app/data/outputs/{run_id}")
    if output_dir.exists():
        try:
            shutil.rmtree(output_dir)
            logger.info(f"[{run_id}] Deleted output directory: {output_dir}")
        except Exception as e:
            logger.error(f"[{run_id}] Failed to delete output directory: {e}")
            # Continue with DB deletion even if file deletion fails

    # Delete from database
    await db.delete(run)
    await db.commit()

    logger.info(f"[USER:{current_user.username}] Successfully deleted run: {run_id}")

    return {"message": "Run deleted successfully", "run_id": run_id}
