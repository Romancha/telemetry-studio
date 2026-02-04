"""Render job API endpoints."""

import contextlib
import logging
import os
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel, Field

from telemetry_studio.constants import (
    DEFAULT_GPS_DOP_MAX,
    DEFAULT_GPS_SPEED_MAX,
    DEFAULT_GPX_MERGE_MODE,
    DEFAULT_UNITS_ALTITUDE,
    DEFAULT_UNITS_DISTANCE,
    DEFAULT_UNITS_SPEED,
    DEFAULT_UNITS_TEMPERATURE,
)
from telemetry_studio.models.job import RenderJobConfig
from telemetry_studio.models.schemas import FileRole
from telemetry_studio.services.file_manager import file_manager
from telemetry_studio.services.job_manager import job_manager
from telemetry_studio.services.render_service import render_service

router = APIRouter()
logger = logging.getLogger(__name__)


# Request/Response models
class RenderJobRequest(BaseModel):
    """Request to start a render job."""

    session_id: str
    layout: str = "default-1920x1080"
    layout_xml_path: str | None = None
    output_file: str | None = None  # Auto-generated if not provided
    units_speed: str = DEFAULT_UNITS_SPEED
    units_altitude: str = DEFAULT_UNITS_ALTITUDE
    units_distance: str = DEFAULT_UNITS_DISTANCE
    units_temperature: str = DEFAULT_UNITS_TEMPERATURE
    map_style: str | None = None
    gpx_merge_mode: str = DEFAULT_GPX_MERGE_MODE
    video_time_alignment: str | None = None
    ffmpeg_profile: str | None = None  # FFmpeg encoding profile (e.g., "mac", "nvgpu")
    gps_dop_max: float = DEFAULT_GPS_DOP_MAX
    gps_speed_max: float = DEFAULT_GPS_SPEED_MAX


class RenderJobResponse(BaseModel):
    """Response from starting a render job."""

    job_id: str
    status: str
    output_file: str


class JobProgressResponse(BaseModel):
    """Job progress information."""

    percent: float = Field(ge=0, le=100)
    current_frame: int | None = None
    total_frames: int | None = None
    fps: float | None = None
    eta_seconds: float | None = None


class JobStatusResponse(BaseModel):
    """Response with job status."""

    job_id: str
    status: str
    progress: JobProgressResponse
    output_file: str
    created_at: str
    started_at: str | None = None
    completed_at: str | None = None
    error: str | None = None


class JobLogsResponse(BaseModel):
    """Response with job logs."""

    job_id: str
    log_lines: list[str]
    total_lines: int


class CurrentJobResponse(BaseModel):
    """Response with current job info."""

    job_id: str | None = None
    status: str | None = None
    progress: JobProgressResponse | None = None


@router.post("/render/start", response_model=RenderJobResponse)
async def start_render(request: RenderJobRequest, background_tasks: BackgroundTasks) -> RenderJobResponse:
    """Start a new render job."""

    # Validate session
    if not file_manager.session_exists(request.session_id):
        raise HTTPException(status_code=404, detail="Session not found")

    # Check if already rendering
    if await job_manager.has_active_job():
        current = await job_manager.get_current_job()
        raise HTTPException(
            status_code=409, detail=f"Another render job is already running: {current.id if current else 'unknown'}"
        )

    # Get primary file info
    primary = file_manager.get_primary_file(request.session_id)
    if not primary:
        raise HTTPException(status_code=404, detail="No primary file in session")

    # Auto-generate output filename if not specified
    output_file = request.output_file
    if not output_file:
        primary_dir = os.path.dirname(primary.file_path)
        primary_name = os.path.splitext(os.path.basename(primary.file_path))[0]
        output_file = os.path.join(primary_dir, f"{primary_name}_overlay.mp4")

    # Create job config
    config = RenderJobConfig(
        session_id=request.session_id,
        layout=request.layout,
        layout_xml_path=request.layout_xml_path,
        output_file=output_file,
        units_speed=request.units_speed,
        units_altitude=request.units_altitude,
        units_distance=request.units_distance,
        units_temperature=request.units_temperature,
        map_style=request.map_style,
        gpx_merge_mode=request.gpx_merge_mode,
        video_time_alignment=request.video_time_alignment,
        ffmpeg_profile=request.ffmpeg_profile,
        gps_dop_max=request.gps_dop_max,
        gps_speed_max=request.gps_speed_max,
    )

    # Create job
    job = await job_manager.create_job(config)

    # Start rendering in background
    background_tasks.add_task(render_service.start_render, job.id, config)

    logger.info(f"Queued render job {job.id} for session {request.session_id}")

    return RenderJobResponse(
        job_id=job.id,
        status=job.status.value,
        output_file=output_file,
    )


@router.get("/render/status/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str) -> JobStatusResponse:
    """Get status of a render job."""

    job = await job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return JobStatusResponse(
        job_id=job.id,
        status=job.status.value,
        progress=JobProgressResponse(
            percent=job.progress.percent,
            current_frame=job.progress.current_frame,
            total_frames=job.progress.total_frames,
            fps=job.progress.fps,
            eta_seconds=job.progress.eta_seconds,
        ),
        output_file=job.config.output_file,
        created_at=job.created_at.isoformat(),
        started_at=job.started_at.isoformat() if job.started_at else None,
        completed_at=job.completed_at.isoformat() if job.completed_at else None,
        error=job.error,
    )


@router.get("/render/logs/{job_id}", response_model=JobLogsResponse)
async def get_job_logs(job_id: str, tail: int = 100) -> JobLogsResponse:
    """Get log output for a job."""

    job = await job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Return last N lines
    log_lines = job.log_lines[-tail:] if len(job.log_lines) > tail else job.log_lines

    return JobLogsResponse(
        job_id=job.id,
        log_lines=log_lines,
        total_lines=len(job.log_lines),
    )


@router.post("/render/cancel/{job_id}")
async def cancel_job(job_id: str) -> dict:
    """Cancel a running render job."""

    job = await job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if not job.is_running():
        raise HTTPException(status_code=400, detail="Job is not running")

    success = await render_service.cancel_render(job_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to cancel job")

    return {"job_id": job_id, "status": "cancelled"}


@router.get("/render/current", response_model=CurrentJobResponse)
async def get_current_job() -> CurrentJobResponse:
    """Get the currently running job, if any."""

    job = await job_manager.get_current_job()
    if not job:
        return CurrentJobResponse()

    return CurrentJobResponse(
        job_id=job.id,
        status=job.status.value,
        progress=JobProgressResponse(
            percent=job.progress.percent,
            current_frame=job.progress.current_frame,
            total_frames=job.progress.total_frames,
            fps=job.progress.fps,
            eta_seconds=job.progress.eta_seconds,
        ),
    )


# --- Batch Render ---


class BatchFileInput(BaseModel):
    """Input for batch render - file path with optional GPX/FIT."""

    video_path: str
    gpx_path: str | None = None
    output_path: str | None = None  # Auto-generated if not provided


class BatchRenderRequest(BaseModel):
    """Request to start batch render jobs."""

    files: list[BatchFileInput] = Field(min_length=1)
    layout: str = "default-1920x1080"
    layout_xml_path: str | None = None
    units_speed: str = DEFAULT_UNITS_SPEED
    units_altitude: str = DEFAULT_UNITS_ALTITUDE
    units_distance: str = DEFAULT_UNITS_DISTANCE
    units_temperature: str = DEFAULT_UNITS_TEMPERATURE
    map_style: str | None = None
    gpx_merge_mode: str = DEFAULT_GPX_MERGE_MODE
    video_time_alignment: str | None = None
    ffmpeg_profile: str | None = None
    gps_dop_max: float = DEFAULT_GPS_DOP_MAX
    gps_speed_max: float = DEFAULT_GPS_SPEED_MAX


class BatchRenderResponse(BaseModel):
    """Response from batch render request."""

    batch_id: str
    job_ids: list[str]
    total_jobs: int
    skipped_files: list[str] = Field(default_factory=list)


class BatchJobDetail(BaseModel):
    """Details of a single job in batch."""

    job_id: str
    status: str
    video_name: str
    progress_percent: float = 0
    current_frame: int | None = None
    total_frames: int | None = None
    fps: float | None = None
    eta_seconds: float | None = None
    error: str | None = None


class BatchStatusResponse(BaseModel):
    """Response with batch status summary."""

    batch_id: str
    total: int
    pending: int
    running: int
    completed: int
    failed: int
    cancelled: int
    current_job: BatchJobDetail | None = None


@router.post("/render/batch", response_model=BatchRenderResponse)
async def start_batch_render(request: BatchRenderRequest, background_tasks: BackgroundTasks) -> BatchRenderResponse:
    """Start a batch of render jobs."""

    if not request.files:
        raise HTTPException(status_code=400, detail="No files provided")

    # Clean up orphaned pending jobs before starting new batch
    valid_sessions = file_manager.get_all_session_ids()
    orphaned = await job_manager.cleanup_orphaned_pending_jobs(valid_sessions)
    if orphaned > 0:
        logger.info(f"Cleaned up {orphaned} orphaned pending jobs before batch start")

    # Check if already rendering
    if await job_manager.has_active_job():
        current = await job_manager.get_current_job()
        raise HTTPException(
            status_code=409, detail=f"Another render job is already running: {current.id if current else 'unknown'}"
        )

    batch_id = str(uuid4())
    job_ids = []
    skipped_files = []

    for file_input in request.files:
        video_path = Path(file_input.video_path)

        # Validate video file exists
        if not video_path.exists():
            logger.warning(f"Batch: skipping non-existent file: {video_path}")
            skipped_files.append(str(video_path))
            continue

        # Determine file type
        suffix = video_path.suffix.lower()
        if suffix in [".mp4", ".mov", ".avi"]:
            file_type = "video"
        elif suffix == ".gpx":
            file_type = "gpx"
        elif suffix == ".fit":
            file_type = "fit"
        else:
            logger.warning(f"Batch: skipping unsupported file type: {video_path}")
            skipped_files.append(str(video_path))
            continue

        # Create local session for this file (skip cleanup to preserve previous batch sessions)
        session_id = file_manager.create_local_session(skip_cleanup=True)

        try:
            # Add primary file
            file_manager.add_file(
                session_id=session_id,
                filename=video_path.name,
                file_path=str(video_path),
                file_type=file_type,
                role=FileRole.PRIMARY,
            )

            # Add secondary GPX/FIT if provided
            if file_input.gpx_path:
                gpx_path = Path(file_input.gpx_path)
                if gpx_path.exists():
                    gpx_suffix = gpx_path.suffix.lower()
                    gpx_type = "gpx" if gpx_suffix == ".gpx" else "fit"
                    file_manager.add_file(
                        session_id=session_id,
                        filename=gpx_path.name,
                        file_path=str(gpx_path),
                        file_type=gpx_type,
                        role=FileRole.SECONDARY,
                    )
                else:
                    logger.warning(f"Batch: GPX/FIT file not found: {gpx_path}")

            # Auto-generate output filename if not specified
            output_file = file_input.output_path
            if not output_file:
                output_file = str(video_path.parent / f"{video_path.stem}_overlay.mp4")

            # Create job config
            config = RenderJobConfig(
                session_id=session_id,
                layout=request.layout,
                layout_xml_path=request.layout_xml_path,
                output_file=output_file,
                units_speed=request.units_speed,
                units_altitude=request.units_altitude,
                units_distance=request.units_distance,
                units_temperature=request.units_temperature,
                map_style=request.map_style,
                gpx_merge_mode=request.gpx_merge_mode,
                video_time_alignment=request.video_time_alignment,
                ffmpeg_profile=request.ffmpeg_profile,
                gps_dop_max=request.gps_dop_max,
                gps_speed_max=request.gps_speed_max,
            )

            # Create job with batch_id
            job = await job_manager.create_job_with_batch(config, batch_id=batch_id)
            job_ids.append(job.id)

        except Exception as e:
            logger.error(f"Batch: failed to create job for {video_path}: {e}")
            skipped_files.append(str(video_path))
            # Cleanup orphaned session
            with contextlib.suppress(Exception):
                file_manager.cleanup_session(session_id)
            continue

    if not job_ids:
        raise HTTPException(status_code=400, detail="No valid files to render")

    # Start first job
    first_job = await job_manager.get_job(job_ids[0])
    if first_job:
        background_tasks.add_task(render_service.start_render, first_job.id, first_job.config)

    logger.info(f"Created batch {batch_id} with {len(job_ids)} jobs")

    return BatchRenderResponse(
        batch_id=batch_id,
        job_ids=job_ids,
        total_jobs=len(job_ids),
        skipped_files=skipped_files,
    )


@router.get("/render/batch/{batch_id}/status", response_model=BatchStatusResponse)
async def get_batch_status(batch_id: str) -> BatchStatusResponse:
    """Get status summary of all jobs in a batch."""
    counts = await job_manager.count_batch_jobs(batch_id)

    if counts["total"] == 0:
        raise HTTPException(status_code=404, detail="Batch not found")

    # Get current running job details
    current_job_detail = None
    running_job = await job_manager.get_running_batch_job(batch_id)
    if running_job:
        # Extract video name from session
        video_name = "Unknown"
        primary = file_manager.get_primary_file(running_job.config.session_id)
        if primary:
            video_name = primary.filename

        current_job_detail = BatchJobDetail(
            job_id=running_job.id,
            status=running_job.status.value,
            video_name=video_name,
            progress_percent=running_job.progress.percent,
            current_frame=running_job.progress.current_frame,
            total_frames=running_job.progress.total_frames,
            fps=running_job.progress.fps,
            eta_seconds=running_job.progress.eta_seconds,
            error=running_job.error,
        )

    return BatchStatusResponse(
        batch_id=batch_id,
        total=counts["total"],
        pending=counts["pending"],
        running=counts["running"],
        completed=counts["completed"],
        failed=counts["failed"],
        cancelled=counts["cancelled"],
        current_job=current_job_detail,
    )


@router.post("/render/batch/{batch_id}/cancel")
async def cancel_batch(batch_id: str) -> dict:
    """Cancel all pending and running jobs in a batch."""
    counts = await job_manager.count_batch_jobs(batch_id)

    if counts["total"] == 0:
        raise HTTPException(status_code=404, detail="Batch not found")

    cancelled_count = 0

    # Cancel all pending jobs
    pending_cancelled = await job_manager.cancel_batch_pending_jobs(batch_id)
    cancelled_count += pending_cancelled

    # Cancel running job if it belongs to this batch
    running_job = await job_manager.get_running_batch_job(batch_id)
    if running_job:
        success = await render_service.cancel_render(running_job.id)
        if success:
            cancelled_count += 1

    logger.info(f"Cancelled {cancelled_count} jobs in batch {batch_id}")

    return {
        "batch_id": batch_id,
        "cancelled_count": cancelled_count,
    }
