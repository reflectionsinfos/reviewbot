# ReviewBot Detailed Overview

This document is meant to be a clean source document for demos, executive reviews, onboarding, and AI-generated explainer videos. It separates what is already implemented from what is still planned so that customers and developers get an accurate picture of the product.

## One-Line Summary

ReviewBot is an AI-assisted review platform that helps teams assess software projects against structured technical and delivery checklists, generate evidence-backed findings, and turn those findings into actionable remediation plans.

## What Problem ReviewBot Solves

Software reviews are often inconsistent, slow, and hard to repeat across teams. One reviewer focuses on architecture, another on delivery hygiene, another on security, and nobody captures the output in a reusable way. ReviewBot introduces a checklist-driven system so reviews become more standardized, auditable, and easier to scale.

## What ReviewBot Does Today

### For customers and delivery teams

- Creates and manages projects with domain, description, tech stack, and stakeholder context
- Uses reusable review checklists for technical or delivery assessments
- Runs autonomous code reviews and shows live progress
- Produces RAG-based findings with evidence for each checklist item
- Stores review history so teams can revisit results later
- Lets reviewers override AI findings with comments and reasoning
- Generates action plans from failed or partial checklist items
- Supports report history, traceability, and operational follow-up

### For developers

- Generates developer-ready remediation prompts from review findings
- Offers prompt formats for generic AI tools, Cursor, and Claude Code
- Supports AI enhancement of prompts using repository-specific context
- Provides an external agent bridge so local workspaces can be reviewed without uploading the entire repository into the browser
- Tracks LLM usage and can store redacted prompt/response audit trails for governance

### For admins and platform owners

- Manages users, roles, and password resets
- Manages global checklist templates and project-specific checklist copies
- Supports sync from global templates into project checklists
- Lets admins configure and activate LLM providers
- Supports system settings such as LLM audit visibility and public branding values

## Current Product Experience

The current product is centered on autonomous review.

1. A user signs in.
2. The user selects a project and checklist.
3. ReviewBot launches an autonomous review job.
4. The system scans the codebase or consumes metadata from an external review agent.
5. ReviewBot classifies each checklist item into the best analysis strategy.
6. It stores evidence and RAG outcomes item by item.
7. The UI streams progress live as the review runs.
8. The completed job appears in history, where users can inspect details, override findings, and generate action plans.
9. Teams can export the action plan or copy AI prompts directly into their coding workflow.

## Implemented Functionalities

### Core review engine

- Autonomous review jobs with persisted job and result records
- Strategy-based routing across deterministic and LLM-driven analysis modes
- File presence checks for documents, configs, and structural artifacts
- Pattern scanning for code and configuration anti-patterns
- Metadata checks for dependency and threshold-related evidence
- LLM-based analysis for code quality, architecture, and nuanced questions
- Human-required classification for questions that cannot be answered from repository evidence alone

### User and admin operations

- JWT login, register, current-user lookup, and password change
- Admin user creation, role updates, activation/deactivation, deletion, and password reset
- Local development auto-login support

### Project and checklist lifecycle

- Project CRUD
- Project checklist upload from Excel
- Global checklist upload and CRUD
- Project-specific checklist cloning from global templates
- Sync from global template into project checklist
- Checklist item add, edit, delete, reorder, and delete protection when history exists
- Routing-rule overrides per checklist item

### Review operations and history

- Live WebSocket progress updates
- Review history list with summary metrics
- Detailed result drill-down per job
- Source-path update for past jobs
- Result override history
- Regeneration hooks for reports
- LLM audit summaries and role-sensitive full trace access

### Action plans

- Automatic grouping of results into critical blockers, advisories, sign-off items, and already compliant items
- Human-readable remediation cards
- AI prompts for developers
- Export and copy-friendly presentation in the history UI
- Optional AI enhancement with prompt caching

### Configuration and operations

- Database-backed LLM configuration management
- LLM connectivity testing
- Active provider switching
- System settings management
- Docker-based local development
- GCP deployment automation scripts

## Important Current Boundaries

To keep the overview accurate, these points matter:

- The strongest implemented product flow is autonomous code review plus history and action-plan follow-up.
- The external agent-upload path is currently more mature than the direct repository-intake path in the web UI.
- Conversational review exists in backend code, but it is not yet the most polished user journey in the product.
- The database already includes future-oriented tables for self-review, schedules, reminders, meeting blocks, and trend analytics, but those workflows are not yet fully implemented in APIs and UI.

## Planned and Upcoming Features

### Near-term product roadmap

- Stabilized direct repository intake from GitHub, GitLab, Bitbucket, and Azure DevOps
- Stronger repository credential handling and provider-specific guidance
- Expanded review-source selection in the UI
- Continued maturation of action-plan and remediation workflows

### Next major capabilities

- Document review for HLD, LLD, runbooks, compliance docs, and architecture artifacts
- Knowledge quiz flows in text and voice mode
- Persona-based self-review before stakeholder meetings
- Recurring review schedules and milestone-triggered reviews
- Reminder and escalation workflows
- Stakeholder readiness and preparation tracking
- Trend analytics and readiness dashboards

### Longer-term direction

- Meeting participation integrations
- Review analytics across time and teams
- Broader workflow orchestration around readiness and accountability
- Marketplace or ecosystem-style extensions

## Technical View for Developers

ReviewBot is currently designed as a FastAPI monolith with strong internal modularity.

- FastAPI serves both the API and the static frontend pages
- SQLAlchemy async models persist users, projects, checklists, review jobs, overrides, reports, LLM configs, and future workflow entities
- Autonomous-review orchestration runs as background tasks
- WebSocket progress updates keep the UI in sync with long-running reviews
- Analyzer modules separate deterministic checks from LLM-based reasoning
- The action-plan generator sits on top of stored review results rather than requiring a second full review run
- The agent bridge allows external tools to upload workspace metadata and only send file contents when the server asks for them

## What Makes ReviewBot Distinct

- It is checklist-first rather than prompt-first, which makes reviews repeatable
- It mixes deterministic analysis, LLM analysis, and human validation instead of forcing everything through one method
- It treats post-review remediation as a first-class outcome, not an afterthought
- It is built for both operational users and engineering users: managers get structured findings, and developers get implementation-ready prompts

## Audience Summary

### For customers

ReviewBot gives your team a more consistent way to review software delivery and technical quality. It reduces the manual effort of checking evidence, preserves review history, and converts findings into follow-up actions your team can actually execute.

### For developers

ReviewBot is not just a scoring engine. It is a bridge between review findings and code changes. It can point to evidence, classify severity, and generate prompts that help move directly from a failed check to a concrete fix.

### For platform and engineering leaders

ReviewBot creates a foundation for scalable review operations: standard templates, stored evidence, configurable AI providers, auditability, and a roadmap toward readiness workflows, accountability, and analytics.

## Suggested Video Story Flow

If this document is used as source material for a product video, this is the cleanest story arc:

1. Start with the problem: software reviews are manual, inconsistent, and hard to scale.
2. Introduce ReviewBot as a checklist-driven AI review platform.
3. Show project and checklist setup.
4. Show an autonomous review launching and streaming live progress.
5. Show findings grouped into green, amber, red, and human-required items.
6. Show the history page with drill-down, overrides, and LLM traceability.
7. Show the action plan and AI prompts as the bridge from insight to implementation.
8. Close with the roadmap: document review, knowledge quiz, readiness workflows, scheduling, and analytics.

## Message to Preserve in External Content

When generating demos or customer-facing videos, present ReviewBot first as an autonomous review and remediation platform that already works today. Present document review, knowledge quiz, self-review, meeting integrations, and advanced analytics as the next wave of capabilities, not as shipped functionality.
