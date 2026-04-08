# Meeting Pipeline

## Use When

- working on OBS file watching
- adding audio extraction
- adding transcription
- changing chunking or relevance scoring

## Current Reality

- file watcher debounce and queue flow are implemented
- audio extraction, transcription, chunking, and scoring are mostly scaffold-level
- the intended path is OBS segment -> audio extraction -> transcript chunks -> relevance per persona

## Hard Constraints

- do not process a segment until file size is stable
- keep pipeline steps incremental; the system is designed around 2-minute segments
- transcript chunks should be suitable both for storage and persona-specific scoring
- preserve session transcript as the shared source of truth

## Main Files

- `src/recorder/pipeline/file_watcher.py`
- `src/recorder/pipeline/audio_extractor.py`
- `src/recorder/pipeline/transcription.py`
- `src/recorder/pipeline/chunking.py`
- `src/recorder/pipeline/relevance_scorer.py`
- `src/recorder/db/models.py`

## Common Mistakes

- reading incomplete OBS files
- coupling pipeline code directly to HTTP routes
- losing timestamps or segment indexes during chunk creation
- treating all persona relevance the same

## Minimum Validation

- create or simulate a stable mp4 arrival path
- verify queueing behavior
- verify produced chunk metadata includes timing and session linkage
