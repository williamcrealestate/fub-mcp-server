# FUB MCP Server — ARIA Properties

A full-featured Follow Up Boss MCP server for Claude. Connects your FUB CRM directly to Claude for contact management, lead ranking, outreach, campaigns, and Meta Ads audience sync.

## Tools Included

### Contacts
| Tool | Description |
|------|-------------|
| `fub_list_contacts` | Search/filter contacts |
| `fub_get_contact` | Full contact details by ID |
| `fub_create_contact` | Create new lead (via /events) |
| `fub_update_contact` | Update contact fields |
| `fub_rank_contact` | Set Hot / Warm / Cold |
| `fub_bulk_rank_contacts` | Rank multiple contacts at once |
| `fub_get_all_contacts` | Paginate all contacts |

### Outreach
| Tool | Description |
|------|-------------|
| `fub_send_sms` | Send native FUB SMS |
| `fub_send_email` | Send native FUB email |
| `fub_bulk_sms` | SMS blast to list (with {{firstName}} merge) |
| `fub_get_sms_history` | SMS thread for a contact |
| `fub_get_email_history` | Email history for a contact |
| `fub_add_note` | Add note to timeline |
| `fub_create_task` | Create follow-up task |

### Campaigns
| Tool | Description |
|------|-------------|
| `fub_list_action_plans` | List all Action Plans |
| `fub_apply_action_plan` | Enroll contact in Action Plan |
| `fub_bulk_apply_action_plan` | Bulk enroll contacts |
| `fub_list_smart_lists` | List Smart Lists |
| `fub_list_pipelines` | List pipeline stages |
| `fub_get_contact_timeline` | Full activity timeline |

### Meta Ads
| Tool | Description |
|------|-------------|
| `meta_list_ad_accounts` | List ad accounts |
| `meta_create_custom_audience` | Push FUB contacts to Meta |
| `meta_create_campaign` | Create Meta campaign |
| `meta_list_campaigns` | List campaigns + spend |
| `meta_push_hot_leads_audience` | One-click Hot/Warm/Cold → Meta audience |

---

## Setup

### 1. Install dependencies
```bash
cd fub-mcp-server
npm install
```

### 2. Build
```bash
npm run build
```

### 3. Test it works
```bash
FUB_API_KEY=your_key_here node dist/index.js
```
You should see: `FUB MCP Server running (stdio). Tools loaded: ...`
Press Ctrl+C to stop.

### 4. Add to Claude Desktop (claude_desktop_config.json)

Find your config file:
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **Mac**: `~/Library/Application Support/Claude/claude_desktop_config.json`

Add this block inside `"mcpServers"`:

```json
{
  "mcpServers": {
    "fub": {
      "command": "node",
      "args": ["C:\\PATH\\TO\\fub-mcp-server\\dist\\index.js"],
      "env": {
        "FUB_API_KEY": "YOUR_FUB_API_KEY_HERE",
        "META_ACCESS_TOKEN": "YOUR_META_TOKEN_HERE",
        "META_AD_ACCOUNT_ID": "act_1934648147412798"
      }
    }
  }
}
```

> Replace `C:\\PATH\\TO\\` with the actual path on your machine (e.g. `C:\\Users\\willi\\Desktop\\fub-mcp-server`).
> Use double backslashes on Windows.

### 5. Restart Claude Desktop

Fully quit and reopen. You'll see the FUB tools appear in Claude.

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `FUB_API_KEY` | ✅ Yes | Your FUB API key (Admin → API) |
| `META_ACCESS_TOKEN` | For Meta tools | Meta Business/User access token |
| `META_AD_ACCOUNT_ID` | For Meta tools | e.g. `act_1934648147412798` |

---

## Known FUB Limitations

- **SMS** (`fub_send_sms`): Requires an SMS provider configured at the FUB account owner level. Team sub-accounts get a 403. This is a FUB account setting, not a code issue.
- **Email** (`fub_send_email`): Also 403 on team sub-accounts. Requires account-level email setup.
- **Action Plans** can be applied via events endpoint even without native SMS/email — the Action Plan itself handles delivery if configured in FUB.
