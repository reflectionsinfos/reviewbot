"""Audio device routing — ensures TTS goes to headset only, never to system speakers.

Uses sounddevice with explicit device index (settings.tts_output_device_index).
This prevents TTS audio from bleeding into the meeting microphone or OBS capture.

To list available devices:
  python -c "import sounddevice as sd; print(sd.query_devices())"
"""

# Implementation: Phase 3
# Skeleton only.

import structlog

from recorder.core.config import settings

logger = structlog.get_logger()


def get_tts_device_index() -> int:
    """Return the configured sounddevice index for TTS output."""
    return settings.tts_output_device_index


def validate_device_index(index: int) -> bool:
    """Check that the device index is valid and not the system default speaker.
    Phase 3 implementation.
    """
    raise NotImplementedError("Audio device validation — Phase 3")
