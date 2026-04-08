"""Faster-Whisper transcription service.

Transcribes each wav segment and returns timestamped segments.
GPU preferred; CPU fallback.
"""

from __future__ import annotations

from functools import lru_cache
from typing import TYPE_CHECKING

import structlog

from recorder.core.config import settings
from recorder.core.exceptions import TranscriptionError
from recorder.schemas.transcript import SegmentTranscription, TranscriptSegment

if TYPE_CHECKING:
    pass

logger = structlog.get_logger()


@lru_cache(maxsize=1)
def _get_model() -> "faster_whisper.WhisperModel":  # type: ignore[name-defined]
    try:
        from faster_whisper import WhisperModel  # type: ignore[import]
    except ImportError as e:
        raise TranscriptionError("faster-whisper is not installed") from e

    logger.info("loading_whisper_model", model=settings.whisper_model)
    return WhisperModel(settings.whisper_model, device="auto", compute_type="auto")


async def transcribe_segment(
    wav_path: str,
    session_id: str,
    segment_index: int,
    segment_duration_secs: int = 120,
) -> SegmentTranscription:
    """Transcribe a wav file and return timestamped transcript segments."""
    import asyncio

    loop = asyncio.get_event_loop()

    def _transcribe() -> SegmentTranscription:
        model = _get_model()
        segments_iter, info = model.transcribe(wav_path, beam_size=5)
        offset = segment_index * segment_duration_secs
        segments = [
            TranscriptSegment(
                start=round(seg.start + offset, 2),
                end=round(seg.end + offset, 2),
                text=seg.text.strip(),
                speaker=None,  # diarization Phase 2
            )
            for seg in segments_iter
            if seg.text.strip()
        ]
        return SegmentTranscription(
            session_id=session_id,
            segment_index=segment_index,
            segment_start_offset_secs=float(offset),
            transcription=segments,
        )

    logger.info("transcription_start", wav=wav_path, segment=segment_index)
    result = await loop.run_in_executor(None, _transcribe)
    logger.info("transcription_complete", segment=segment_index, n_segments=len(result.transcription))
    return result
