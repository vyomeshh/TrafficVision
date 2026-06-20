import uuid
from fastapi import APIRouter, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from app.services.detection_service import process_detection

router = APIRouter()

@router.post("")
async def detect(image: UploadFile = File(...)):
    """
    Main detection pipeline.
    Upload an image to detect vehicles, check violations, and read license plates.
    """
    detection_id = f"TR-{uuid.uuid4().hex[:6].upper()}"
    
    try:
        contents = await image.read()
        if not contents:
            raise HTTPException(status_code=400, detail="Empty file uploaded.")
            
        result = await process_detection(detection_id, contents, image.filename or "upload.jpg")
        return JSONResponse(content=result)

    except HTTPException:
        raise
    except Exception as exc:
        import traceback
        traceback_str = traceback.format_exc()
        # Fallback error response
        from app.services.log_service import log_service
        log_service.add_log(detection_id, f"ERROR: {exc}")
        
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "detection_id": detection_id,
                "error": str(exc),
                "traceback": traceback_str,
                "processing_logs": log_service.get_logs(detection_id),
            },
        )
