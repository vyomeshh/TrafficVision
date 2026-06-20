import asyncio
from datetime import datetime

class LogService:
    def __init__(self):
        self._processing_logs: dict[str, list[str]] = {}
        self._processing_events: dict[str, asyncio.Event] = {}

    def init_detection(self, detection_id: str):
        """Initialize the log list and event for a new detection run."""
        self._processing_logs[detection_id] = []
        self._processing_events[detection_id] = asyncio.Event()

    def add_log(self, detection_id: str, message: str):
        """Append a timestamped log line for the given detection run."""
        ts = datetime.utcnow().strftime("%H:%M:%S.%f")[:-3]
        entry = f"[{ts}] {message}"
        self._processing_logs.setdefault(detection_id, []).append(entry)
        
        # Signal any listeners
        evt = self._processing_events.get(detection_id)
        if evt:
            evt.set()

    def add_raw_logs(self, detection_id: str, logs: list[str]):
        """Extend logs without timestamp formatting."""
        self._processing_logs.setdefault(detection_id, []).extend(logs)
        evt = self._processing_events.get(detection_id)
        if evt:
            evt.set()

    def get_logs(self, detection_id: str) -> list[str]:
        return self._processing_logs.get(detection_id, [])

    def get_event(self, detection_id: str) -> asyncio.Event | None:
        return self._processing_events.get(detection_id)

    def has_detection(self, detection_id: str) -> bool:
        return detection_id in self._processing_logs

# Global instance for use across the app
log_service = LogService()
