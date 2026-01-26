"""Preview API endpoint."""

import asyncio
from concurrent.futures import ThreadPoolExecutor

from fastapi import APIRouter, HTTPException

from telemetry_studio.models.schemas import PreviewRequest, PreviewResponse
from telemetry_studio.services.file_manager import file_manager
from telemetry_studio.services.renderer import image_to_base64, render_preview

router = APIRouter()

# Thread pool for running sync code that uses asyncio
_executor = ThreadPoolExecutor(max_workers=2)


@router.post("/preview", response_model=PreviewResponse)
async def generate_preview(request: PreviewRequest) -> PreviewResponse:
    """Generate a preview image for the uploaded file with specified settings."""
    # Validate session exists
    if not file_manager.session_exists(request.session_id):
        raise HTTPException(status_code=404, detail="Session not found")

    # Get the file path
    file_path = file_manager.get_file_path(request.session_id)
    if file_path is None:
        raise HTTPException(status_code=404, detail="File not found in session")

    try:
        # Render the preview in a separate thread to avoid asyncio conflicts
        loop = asyncio.get_running_loop()
        png_bytes, width, height = await loop.run_in_executor(
            _executor,
            lambda: render_preview(
                file_path=file_path,
                layout=request.layout,
                frame_time_ms=request.frame_time_ms,
                units_speed=request.units_speed,
                units_altitude=request.units_altitude,
                units_distance=request.units_distance,
                units_temperature=request.units_temperature,
                map_style=request.map_style,
            ),
        )

        # Convert to base64
        image_base64 = image_to_base64(png_bytes)

        return PreviewResponse(
            image_base64=image_base64,
            width=width,
            height=height,
            frame_time_ms=request.frame_time_ms,
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate preview: {str(e)}",
        ) from e
