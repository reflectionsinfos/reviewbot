"""Pydantic schemas for transcript chunks."""

from pydantic import BaseModel


class TranscriptSegment(BaseModel):
    start: float
    end: float
    text: str
    speaker: str | None = None


class TranscriptChunkSchema(BaseModel):
    chunk_id: str
    session_id: str
    segment_index: int
    start_time: float
    end_time: float
    speakers: list[str]
    text: str
    relevance_scores: dict[str, float] = {}  # {persona_id: score}


class SegmentTranscription(BaseModel):
    session_id: str
    segment_index: int
    segment_start_offset_secs: float
    transcription: list[TranscriptSegment]
