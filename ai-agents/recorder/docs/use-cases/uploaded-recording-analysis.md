# Use Case: Uploaded Recording Analysis

## Goal

Let a user analyze a meeting after it has already been recorded.

## Applies To

- Phase 1 optional ingestion path
- post-meeting analysis
- replay and late-joiner workflows

## Workflow

1. User selects an existing project in the UI.
2. User clicks `Analyze Recording`.
3. UI creates a new session and asks for meeting title, meeting focus, active personas, and any meeting-specific context.
4. User uploads one or more meeting files through the UI.
5. System stores the files under the created `session_id`.
6. The ingestion pipeline processes those files exactly like OBS segments after they are attached to the session.
7. User discusses the processed transcript in chat after ingestion completes.

## Binding Rule

Uploaded files do not define project or personas.

The UI session created before upload supplies:

- `project_id`
- active personas
- meeting focus
- preloaded context

## Product Guidance

- Upload is needed only for this mode.
- Upload is not required for live local OBS mode.
- In Phase 1, direct file upload is simpler than importing from Teams links.

## Future Extension

Later versions may allow importing a Teams recording link, but that should still resolve to a normal `session_id` before processing starts.
