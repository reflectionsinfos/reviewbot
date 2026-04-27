# ReviewBot — API Endpoint Reference

> Complete endpoint inventory. Auth = JWT Bearer unless noted.
> Last updated: 2026-04-27

---

## Auth `/api/auth`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/auth/register` | — | Register new user (accepts organization_id) |
| POST | `/api/auth/login` | — | Get JWT access token |
| GET | `/api/auth/me` | any | Current user info including organization_id |
| POST | `/api/auth/change-password` | any | Change own password |
| GET | `/api/auth/dev-config` | — | Dev credentials (local env only) |

---

## Organizations `/api/organizations`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/organizations/` | any | List active organizations |
| GET | `/api/organizations/mine` | any | Get current user's organization |
| GET | `/api/organizations/{id}` | any | Get one organization |
| POST | `/api/organizations/` | admin | Create organization |
| PUT | `/api/organizations/{id}` | admin | Update organization |
| DELETE | `/api/organizations/{id}` | admin | Soft-delete organization (sets is_active=False) |

---

## Projects `/api/projects`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/projects/` | any | List projects |
| POST | `/api/projects/` | any | Create project (accepts organization_id) |
| GET | `/api/projects/{id}` | any | Get project |
| PUT | `/api/projects/{id}` | any | Update project |
| DELETE | `/api/projects/{id}` | any | Delete project |
| GET | `/api/projects/{id}/checklists` | any | List project checklists |
| POST | `/api/projects/{id}/upload-checklist` | any | Upload Excel checklist |
| POST | `/api/projects/{id}/clone-template/{template_id}` | any | Clone global template into project |

---

## Checklists `/api/checklists`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/checklists/templates/global` | any | List global templates (org-scoped) |
| POST | `/api/checklists/templates/global` | admin | Create global template (accepts organization_id) |
| POST | `/api/checklists/templates/global/upload` | admin | Upload global template from Excel |
| GET | `/api/checklists/{id}` | any | Get checklist with items |
| PUT | `/api/checklists/{id}` | any | Update checklist metadata |
| DELETE | `/api/checklists/{id}` | any | Delete checklist (blocked if reviews reference it) |
| GET | `/api/checklists/{id}/items` | any | List items |
| POST | `/api/checklists/{id}/items` | any | Create item (accepts team_category, guidance, applicability_tags) |
| PUT | `/api/checklists/{id}/items/{item_id}` | any | Update item |
| DELETE | `/api/checklists/{id}/items/{item_id}` | any | Delete item |
| POST | `/api/checklists/{id}/sync` | any | Sync from source global template |
| POST | `/api/checklists/{id}/optimize` | any | AI recommendations |
| PUT | `/api/checklists/{id}/items/reorder` | any | Reorder items |

---

## Reviews `/api/reviews`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/reviews/` | any | List reviews (org-scoped) |
| POST | `/api/reviews/` | any | Create online review session |
| GET | `/api/reviews/{id}` | any | Get review |
| POST | `/api/reviews/{id}/start` | any | Start AI LangGraph agent |
| POST | `/api/reviews/{id}/respond` | any | Submit text response |
| POST | `/api/reviews/{id}/voice-response` | any | Submit audio response |
| POST | `/api/reviews/{id}/complete` | any | Complete review |
| POST | `/api/reviews/{id}/share` | any | Create a share link (portal_url derived from Request) |
| GET | `/api/reviews/{id}/shares` | any | List share links for a review |
| POST | `/api/reviews/offline` | any | Create offline (Excel) review + send invitation email |
| GET | `/api/reviews/offline/pending` | any | List pending offline reviews |
| POST | `/api/reviews/{id}/resend-email` | any | Resend offline invitation |
| POST | `/api/reviews/manual` | any | Create manual/self review (token-gated portal) |
| GET | `/api/reviews/portal/{review_id}` | token | Get review data via upload_token (no login) |
| POST | `/api/reviews/portal/{review_id}/submit` | token | Submit responses via portal |
| GET | `/api/reviews/upload/{token}` | — | Get offline review data via upload token |
| POST | `/api/reviews/upload/{token}` | — | Upload completed Excel responses |

---

## Reports `/api/reports`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/reports/` | any | List reports |
| GET | `/api/reports/{id}` | any | Get report |
| POST | `/api/reports/{id}/approve` | manager/admin | Approve report |
| POST | `/api/reports/{id}/reject` | manager/admin | Reject with comments |
| GET | `/api/reports/{id}/download/{format}` | any | Download: `markdown` or `pdf` |

---

## Autonomous Reviews `/api/autonomous-reviews`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/autonomous-reviews/` | any | Start autonomous review job |
| GET | `/api/autonomous-reviews/` | any | List jobs |
| GET | `/api/autonomous-reviews/{id}` | any | Get job |
| GET | `/api/autonomous-reviews/{id}/results` | any | Get results |
| POST | `/api/autonomous-reviews/{id}/results/{result_id}/override` | any | Override RAG finding |
| GET | `/api/autonomous-reviews/{id}/action-plan` | any | Get AI action plan |
| WebSocket | `/api/autonomous-reviews/{id}/ws` | — | Live progress updates |

---

## Integrations `/api/integrations`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/integrations/` | admin | List all (secrets masked in response) |
| POST | `/api/integrations/` | admin | Create integration |
| GET | `/api/integrations/{id}` | admin | Get one |
| PATCH | `/api/integrations/{id}` | admin | Update |
| DELETE | `/api/integrations/{id}` | admin | Delete |
| POST | `/api/integrations/{id}/test` | admin | Test connectivity |
| POST | `/api/integrations/{id}/dispatch/{job_id}` | admin/manager | Manual dispatch |
| GET | `/api/integrations/dispatches/{job_id}` | any | Dispatch history for a job |

---

## LLM Configs `/api/llm-configs`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/llm-configs/` | admin | List LLM configs |
| POST | `/api/llm-configs/` | admin | Create config |
| PUT | `/api/llm-configs/{id}` | admin | Update config |
| DELETE | `/api/llm-configs/{id}` | admin | Delete config |
| POST | `/api/llm-configs/{id}/test` | admin | Test LLM connectivity |
| PUT | `/api/llm-configs/{id}/default` | admin | Set as default |

---

## System Settings `/api/settings`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/settings/` | admin | List all settings |
| PUT | `/api/settings/{key}` | admin | Update a setting value |

---

## Error Response Format

```json
{
  "detail": "Error message describing what went wrong"
}
```

Common status codes:
- `400` Bad Request — invalid input
- `401` Unauthorized — missing/invalid JWT
- `403` Forbidden — insufficient role
- `404` Not Found
- `409` Conflict — e.g., duplicate name
- `422` Unprocessable Entity — validation error
- `500` Internal Server Error
