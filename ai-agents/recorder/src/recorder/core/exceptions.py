"""Domain exception hierarchy for the Recorder Agent."""


class RecorderError(Exception):
    """Base exception for all recorder errors."""


# ── Project Brain ─────────────────────────────────────────────────────────────

class ProjectNotFoundError(RecorderError):
    pass


class IndexingError(RecorderError):
    pass


class CodeIndexerError(IndexingError):
    pass


class DocumentIndexerError(IndexingError):
    pass


class ConnectorError(RecorderError):
    pass


# ── Session / Pipeline ────────────────────────────────────────────────────────

class SessionNotFoundError(RecorderError):
    pass


class SessionStateError(RecorderError):
    """Raised when an operation is invalid for the current session state."""


class PipelineError(RecorderError):
    pass


class TranscriptionError(PipelineError):
    pass


class AudioExtractionError(PipelineError):
    pass


# ── Agent ─────────────────────────────────────────────────────────────────────

class AgentError(RecorderError):
    pass


class PersonaNotFoundError(AgentError):
    pass


class OrchestrationError(AgentError):
    pass


# ── Voice ─────────────────────────────────────────────────────────────────────

class VoiceError(RecorderError):
    pass


class TTSError(VoiceError):
    pass


class STTError(VoiceError):
    pass
