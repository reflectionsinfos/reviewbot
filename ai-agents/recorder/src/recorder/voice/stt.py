"""STT for voice queries — captures mic input and transcribes the question.

Uses the same Faster-Whisper model already loaded for segment transcription.
Listen duration: configurable (default 8 seconds).
"""

# Implementation: Phase 3
# Skeleton only.

from recorder.core.config import settings


async def capture_voice_query() -> str:
    """Capture mic input for stt_listen_duration_secs and return transcribed text.
    Phase 3 implementation.
    """
    raise NotImplementedError("Voice query STT — Phase 3")
