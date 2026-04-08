"""ChromaDB namespace (collection) name helpers.

Namespace conventions:
  project_brain_{project_id}     — docs, ADRs, specs, Jira, Confluence
  project_code_{project_id}      — LLM-generated code summaries
  project_meetings_{project_id}  — prior meeting transcripts + understanding docs
  persona_domain_{persona_id}    — generic domain knowledge (not project-specific)
  session_transcript_{session_id}— this meeting's transcript chunks

Profile Card is NEVER in ChromaDB — injected verbatim into system prompts.
"""


def project_brain(project_id: str) -> str:
    return f"project_brain_{project_id}"


def project_code(project_id: str) -> str:
    return f"project_code_{project_id}"


def project_meetings(project_id: str) -> str:
    return f"project_meetings_{project_id}"


def persona_domain(persona_id: str) -> str:
    return f"persona_domain_{persona_id}"


def session_transcript(session_id: str) -> str:
    return f"session_transcript_{session_id}"
