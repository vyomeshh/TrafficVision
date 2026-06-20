import asyncio
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from app.services.log_service import log_service

router = APIRouter()

@router.get("/{detection_id}")
async def stream_logs(detection_id: str, request: Request):
    """Server-Sent Events (SSE) endpoint to stream processing logs in real-time."""
    if not log_service.has_detection(detection_id):
        raise HTTPException(status_code=404, detail="Detection ID not found.")

    async def event_generator():
        last_idx = 0
        while True:
            if await request.is_disconnected():
                break

            logs = log_service.get_logs(detection_id)
            if last_idx < len(logs):
                for log_line in logs[last_idx:]:
                    yield f"data: {log_line}\n\n"
                last_idx = len(logs)

            # Check if processing has explicitly completed or failed
            if last_idx > 0:
                last_line = logs[-1]
                if "Pipeline complete" in last_line or "ERROR" in last_line:
                    yield "data: [DONE]\n\n"
                    break

            # Wait for a signal that new logs were added
            evt = log_service.get_event(detection_id)
            if evt:
                try:
                    await asyncio.wait_for(evt.wait(), timeout=1.0)
                    evt.clear()
                except asyncio.TimeoutError:
                    # Send a heartbeat comment to keep the connection alive
                    yield ": heartbeat\n\n"
            else:
                break

    return StreamingResponse(event_generator(), media_type="text/event-stream")
