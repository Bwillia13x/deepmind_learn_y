"""WebSocket endpoints package."""

from app.api.v1.websockets.voice_stream import router as voice_router

__all__ = ["voice_router"]
