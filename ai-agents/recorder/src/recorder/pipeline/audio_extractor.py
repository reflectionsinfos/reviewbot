"""FFmpeg audio extraction from OBS mp4 segments.

Extracts 16kHz mono PCM WAV from each mp4 segment.
"""

import asyncio
import os
from pathlib import Path

import structlog

from recorder.core.exceptions import AudioExtractionError

logger = structlog.get_logger()

FFMPEG_CMD = (
    "ffmpeg -y -i {input} -vn -acodec pcm_s16le -ar 16000 -ac 1 {output} -loglevel error"
)


async def extract_audio(mp4_path: str) -> str:
    """Extract audio from mp4 to wav. Returns path to the wav file."""
    input_path = Path(mp4_path)
    output_path = input_path.with_suffix(".wav")

    cmd = FFMPEG_CMD.format(input=str(input_path), output=str(output_path))
    logger.info("audio_extraction_start", input=mp4_path)

    proc = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.PIPE,
    )
    _, stderr = await proc.communicate()

    if proc.returncode != 0:
        err = stderr.decode(errors="replace")
        logger.error("audio_extraction_failed", input=mp4_path, error=err)
        raise AudioExtractionError(f"FFmpeg failed for {mp4_path}: {err}")

    logger.info("audio_extraction_complete", output=str(output_path))
    return str(output_path)
