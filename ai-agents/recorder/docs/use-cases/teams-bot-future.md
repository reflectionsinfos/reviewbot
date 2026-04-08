# Use Case: Teams Bot Participant

## Goal

Allow the system to join a meeting automatically as a bot participant and run the same downstream intelligence pipeline.

## Applies To

- Phase 3 and later

## Workflow

1. User schedules or enables Nexus for a Teams meeting.
2. Bot joins as a named participant.
3. Recording and transcript assets are obtained through Microsoft Graph APIs.
4. System creates or resumes a matching `session_id`.
5. Retrieved media is attached to that session.
6. Standard transcription, retrieval, persona, and briefing flows run.
7. Shared summary and role-specific outputs may be posted back to Teams.

## Important Clarification

This is not part of the primary Phase 1 MVP.

Phase 1 should not depend on:

- bot registration
- fake meeting accounts
- Teams auto-join
- Graph-based recording download

## Binding Rule

Even in the Teams bot future flow, the core ownership model stays the same:

- media is processed under a `session_id`
- the session determines `project_id`
- the session determines active personas and meeting context
