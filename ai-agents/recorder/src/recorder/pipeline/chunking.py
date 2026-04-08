"""Time-window chunking of transcript segments.

Produces 60-second chunks with 15-second overlap from transcript segments.
"""

from recorder.schemas.transcript import SegmentTranscription, TranscriptChunkSchema

CHUNK_WINDOW_SECS = 60.0
CHUNK_OVERLAP_SECS = 15.0


def chunk_transcription(transcription: SegmentTranscription, chunk_n_start: int = 0) -> list[TranscriptChunkSchema]:
    """Split transcript segments into overlapping time-window chunks."""
    if not transcription.transcription:
        return []

    segments = transcription.transcription
    start_time = segments[0].start
    end_time = segments[-1].end
    chunks: list[TranscriptChunkSchema] = []
    chunk_n = chunk_n_start
    window_start = start_time

    while window_start < end_time:
        window_end = window_start + CHUNK_WINDOW_SECS
        window_segs = [s for s in segments if s.start < window_end and s.end > window_start]
        if window_segs:
            speakers = list({s.speaker for s in window_segs if s.speaker})
            text = " ".join(s.text for s in window_segs)
            chunks.append(
                TranscriptChunkSchema(
                    chunk_id=f"{transcription.session_id}::chunk_{chunk_n}",
                    session_id=transcription.session_id,
                    segment_index=transcription.segment_index,
                    start_time=window_segs[0].start,
                    end_time=window_segs[-1].end,
                    speakers=speakers,
                    text=text,
                )
            )
            chunk_n += 1
        window_start += CHUNK_WINDOW_SECS - CHUNK_OVERLAP_SECS

    return chunks
