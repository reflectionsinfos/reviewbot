# Use Case: Live Local OBS Session

## Goal

Process a meeting live on the local machine without a bot joining Teams.

## Applies To

- Phase 1 primary MVP
- developer and early-user local workflow

## Workflow

1. User selects an existing project in the UI.
2. User clicks `Start Live Capture`.
3. UI creates a new session and asks for meeting title, meeting focus, active personas, primary persona, and any meeting-specific context.
4. System creates `session_id` and marks it as the active live capture session.
5. OBS records locally and writes segmented mp4 files.
6. The file watcher binds new mp4 files to the active `session_id`.
7. Because the session already knows `project_id`, active personas, and the primary persona, each transcript chunk is processed in the correct project and role context.
8. User opens chat or Q&A for that same session during or after the meeting.

## Start Next Session

For recurring meetings, the meetings grid should provide a `Start Next Session` action so users do not need to re-enter the same setup every time.

When the user clicks `Start Next Session`, the UI should prefill:

- `project_id`
- meeting mode
- active personas
- `primary_persona`
- recurring meeting title or title pattern
- previously linked session as `previous_session_id`
- unresolved action items
- unresolved open questions
- still-open risks or conflicts

The user should then only update:

- today's meeting focus
- anything materially changed since the previous session
- personas to add or remove for this meeting

## Carry-Forward Preview

Before creating the next linked session, the UI should show a carry-forward preview.

Suggested preview content:

- continuing from session X
- unresolved action items count
- unresolved questions count
- reused personas
- prior meeting summary available

Suggested actions:

- `Start with Carry-Forward`
- `Start Fresh`
- `Customize`

This is the preferred product flow because it keeps recurring meetings fast to start while still letting the user break continuity when needed.

## Binding Rule

The mp4 file does not identify the project or personas by itself.

Ownership comes from the session created in the UI before processing begins:

- `session_id` -> `project_id`
- `session_id` -> active personas
- `session_id` -> `primary_persona_id`
- `session_id` -> `previous_session_id` (optional)
- `session_id` -> `meeting_series_id` (optional)
- `session_id` -> meeting focus and preloaded context

Meeting continuity should be user-controlled:

- user can link a session to the previous one
- user can unlink it later
- user can re-link to a different prior session
- user can mark a session as standalone even inside the same project

## Persona Setup

Persona selection must happen before live processing begins.

The UI should support:

- selecting one or more active personas for the session
- reusing a saved persona profile or creating a new one
- marking one persona as the `primary_persona`
- capturing accountability areas, irrelevant topics, and open questions for each active persona

This persona setup is what makes role-specific summaries, action items, risks, and "what matters to you" outputs possible.

## Phase 1 Notes

- No Teams bot joins the meeting.
- No fake participant account is required.
- This is the simplest and recommended MVP path.
- The MVP should support only one active live capture session at a time on a local machine.
- Phase 1 may use the Default Expert as the main runtime agent, but the session should still be persona-aware.
- Transcription stays shared and neutral; role-specific interpretation and outcomes are generated from the shared transcript plus persona profiles.

## Storage Recommendation

Prefer a session-scoped segment location such as `data/sessions/<session_id>/segments/`.

If OBS must write to a shared watch folder first, the app should immediately move or register the segment under the active session before downstream processing.
