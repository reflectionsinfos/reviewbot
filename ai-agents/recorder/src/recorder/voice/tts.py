"""TTS (Text-to-Speech) — spoken responses to earphone only.

Providers: openai | elevenlabs | kokoro (local)
Output: explicitly routed to configured headset device (sounddevice device index).
NEVER routed to system speakers or OBS capture device.

Voice responses are condensed to 2-3 sentences.
Full response is shown in chat UI simultaneously.
"""

# Implementation: Phase 3
# Skeleton only.

import structlog

from recorder.core.config import settings
from recorder.core.exceptions import TTSError

logger = structlog.get_logger()


async def speak(text: str, condensed: bool = True) -> None:
    """Convert text to speech and play to the configured headset device.

    If condensed=True, the text is shortened to 2-3 sentences for voice.
    Phase 3 implementation.
    """
    raise NotImplementedError("TTS — Phase 3")


def condense_for_voice(full_response: str, max_sentences: int = 3) -> str:
    """Shorten a full agent response to max_sentences for earphone delivery.
    Phase 3 implementation.
    """
    raise NotImplementedError("Voice condensing — Phase 3")
