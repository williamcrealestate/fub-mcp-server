# FUB MCP Server — ARIA Properties

Python FastMCP server connecting Follow Up Boss CRM and Meta Ads to Claude via SSE transport. Deploy once, use from claude.ai on any device.

## Tools

### Contacts
| Tool | Description |
|------|-------------|
| `fub_list_contacts` | Search/filter contacts by name, email, stage, or tag |
| `fub_get_contact` | Full contact details by ID |
| `fub_create_contact` | Create new lead (via /events — triggers automations) |
| `fub_update_contact` | Update contact fields |
| `fub_rank_contact` | Set Hot / Warm / Cold + optional note |
| `fub_bulk_rank_contacts` | Rank up to 50 contacts at once |
| `fub_get_all_contacts` | Paginate all contacts (up to 1000) |

### Notes & Tasks
| Tool | Description |
|------|-------------|
| `fub_add_note` | Add note to contact timeline |
| `fub_create_task` | Create follow-up task with optional due date |
| `fub_get_contact_timeline` | Full activity timeline (calls, emails, texts, notes) |

### Action Plans & Pipeline
| Tool | Description |
|------|-------------|
| `fub_list_action_plans` | List all drip sequences |
| `fub_apply_action_plan` | Enroll contact in Action Plan |
| `fub_bulk_apply_action_plan` | Bulk enroll up to 100 contacts |
| `fub_list_pipelines` | List pipeline stages |

### Meta Ads
| Tool | Description |
|------|-------------|
| `meta_list_campaigns` | List campaigns with spend/status |
| `meta_create_campaign` | Create campaign (HOUSING category enforced) |
| `meta_update_campaign` | Pause, resume, rename, or adjust budget |
| `meta_create_ad_set` | Create ad set under a campaign |
| `meta_get_insights` | Performance metrics by campaign/adset/ad |

---

## Deploy to Railway

1. Go to [railway.app](https://railway.app) → **New Project** → **Deploy from GitHub repo** → select `williamcrealestate/fub-mcp-server`
2. Railway detects the `Procfile` automatically — no config needed
3. **Variables** tab → add environment variables:

| Variable | Required | Description |
|----------|----------|-------------|
| `FUB_API_KEY` | Yes | FUB Admin → API |
| `META_ACCESS_TOKEN` | Meta tools only | Meta Business access token |

4. **Settings → Networking → Generate Domain** — copy the public URL

---

## Add to Claude.ai

1. [claude.ai](https://claude.ai) → profile → **Settings → Integrations**
2. **Add Integration**:
   - **Name:** FUB MCP Server
   - **URL:** `https://your-app.up.railway.app/sse`
3. Save — the FUB tools will appear in Claude

---

## Known FUB Limitations

- **Direct SMS/Email** (`/textMessages`, `/emails`): Returns 403 on team sub-accounts — Action Plans are the only approved outreach path on this account.
- **Action Plans** applied via `/events` work even without native SMS/email — the plan handles delivery if configured in FUB.
