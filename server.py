"""
FUB MCP Server — ARIA Properties
William Cerqueira | LPT Realty
FastMCP Python — SSE transport for Claude.ai
"""

import os
import json
import httpx
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
from mcp.server.fastmcp import FastMCP

# ── CONFIG ─────────────────────────────────────────────────────────────────
FUB_API_KEY   = os.environ.get("FUB_API_KEY", "")
FUB_BASE      = "https://api.followupboss.com/v1"
META_TOKEN    = lambda: os.environ.get("META_ACCESS_TOKEN", "")
META_BASE     = "https://graph.facebook.com/v19.0"
ARIA_ACCOUNT  = "act_41421368"
OBJECTIVE_MAP = {
    "REACH":            "OUTCOME_AWARENESS",
    "BRAND_AWARENESS":  "OUTCOME_AWARENESS",
    "LEAD_GENERATION":  "OUTCOME_LEADS",
    "CONVERSIONS":      "OUTCOME_SALES",
    "MESSAGES":         "OUTCOME_ENGAGEMENT",
    "TRAFFIC":          "OUTCOME_TRAFFIC",
}

mcp = FastMCP("fub_mcp", dependencies=["httpx"])


# ── SHARED CLIENTS ──────────────────────────────────────────────────────────

def fub_auth() -> dict:
    return {"auth": (FUB_API_KEY, ""), "headers": {"Content-Type": "application/json"}}

async def fub_get(path: str, params: dict = {}) -> dict:
    async with httpx.AsyncClient(base_url=FUB_BASE, timeout=20) as c:
        r = await c.get(path, params=params, **fub_auth())
        r.raise_for_status()
        return r.json()

async def fub_post(path: str, body: dict = {}) -> dict:
    async with httpx.AsyncClient(base_url=FUB_BASE, timeout=20) as c:
        r = await c.post(path, json=body, **fub_auth())
        r.raise_for_status()
        return r.json()

async def fub_put(path: str, body: dict = {}) -> dict:
    async with httpx.AsyncClient(base_url=FUB_BASE, timeout=20) as c:
        r = await c.put(path, json=body, **fub_auth())
        r.raise_for_status()
        return r.json()

async def fub_paginate(path: str, params: dict = {}, max_pages: int = 10) -> list:
    results = []
    offset = 0
    limit = 100
    for _ in range(max_pages):
        data = await fub_get(path, {**params, "limit": limit, "offset": offset})
        items = data.get("people") or data.get("data") or []
        results.extend(items)
        if len(items) < limit:
            break
        offset += limit
    return results

async def meta_get(path: str, params: dict = {}) -> dict:
    token = META_TOKEN()
    if not token:
        raise ValueError("META_ACCESS_TOKEN not set")
    async with httpx.AsyncClient(base_url=META_BASE, timeout=20) as c:
        r = await c.get(path, params={"access_token": token, **params})
        r.raise_for_status()
        return r.json()

async def meta_post(path: str, data: dict = {}) -> dict:
    token = META_TOKEN()
    if not token:
        raise ValueError("META_ACCESS_TOKEN not set")
    async with httpx.AsyncClient(base_url=META_BASE, timeout=20) as c:
        r = await c.post(path, data={"access_token": token, **data})
        r.raise_for_status()
        return r.json()

def ok(data) -> str:
    return json.dumps(data, indent=2)

def err(e: Exception) -> str:
    if isinstance(e, httpx.HTTPStatusError):
        try:
            body = e.response.json()
            return f"Error {e.response.status_code}: {body}"
        except Exception:
            return f"Error {e.response.status_code}: {e.response.text}"
    return f"Error: {str(e)}"


# ══════════════════════════════════════════════════════════════════════════════
# FUB — CONTACTS
# ══════════════════════════════════════════════════════════════════════════════

class ListContactsInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    query:  Optional[str] = Field(None,  description="Free-text search (name, email, phone)")
    stage:  Optional[str] = Field(None,  description="Filter by stage e.g. Hot, Warm, Cold, Lead")
    tags:   Optional[str] = Field(None,  description="Filter by tag name")
    limit:  int           = Field(50,    description="Max results (1–200)", ge=1, le=200)
    offset: int           = Field(0,     description="Pagination offset", ge=0)


@mcp.tool(
    name="fub_list_contacts",
    annotations={"title": "List FUB Contacts", "readOnlyHint": True}
)
async def fub_list_contacts(params: ListContactsInput) -> str:
    """Search and filter contacts in Follow Up Boss CRM.

    Returns paginated list with id, name, emails, phones, stage, tags, source.

    Args:
        params: Search and filter options including query, stage, tags, limit, offset.

    Returns:
        JSON with totalCount and list of contact objects.
    """
    try:
        p = {"limit": params.limit, "offset": params.offset}
        if params.query: p["q"] = params.query
        if params.stage: p["stage"] = params.stage
        if params.tags:  p["tags"] = params.tags
        data = await fub_get("/people", p)
        return ok(data)
    except Exception as e:
        return err(e)


class GetContactInput(BaseModel):
    id: int = Field(..., description="FUB person ID", ge=1)


@mcp.tool(
    name="fub_get_contact",
    annotations={"title": "Get FUB Contact", "readOnlyHint": True}
)
async def fub_get_contact(params: GetContactInput) -> str:
    """Get full contact details by FUB person ID.

    Returns all contact fields including emails, phones, stage, tags,
    notes, tasks, source, assignedTo, and custom fields.

    Args:
        params: Contact ID to retrieve.

    Returns:
        JSON contact object with all fields.
    """
    try:
        data = await fub_get(f"/people/{params.id}")
        return ok(data)
    except Exception as e:
        return err(e)


class CreateContactInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    firstName: str           = Field(...,                    description="Contact first name", min_length=1)
    lastName:  Optional[str] = Field(None,                   description="Contact last name")
    email:     Optional[str] = Field(None,                   description="Email address")
    phone:     Optional[str] = Field(None,                   description="Phone number")
    source:    str           = Field("ARIA Properties",      description="Lead source")
    type:      str           = Field("General Inquiry",      description="Event type e.g. 'Registration', 'Buyer Inquiry', 'Seller Inquiry'")
    message:   Optional[str] = Field(None,                   description="Initial message/note")
    tags:      Optional[list[str]] = Field(None,             description="Tags to assign")


@mcp.tool(
    name="fub_create_contact",
    annotations={"title": "Create FUB Contact", "destructiveHint": False}
)
async def fub_create_contact(params: CreateContactInput) -> str:
    """Create a new lead in Follow Up Boss via the /events endpoint.

    Uses the events endpoint which properly triggers FUB automations,
    action plans, and notifications — do NOT use /people directly for
    new leads.

    Args:
        params: Contact details including name, email, phone, source, type.

    Returns:
        JSON with created contact ID and details.
    """
    try:
        person: dict = {"firstName": params.firstName}
        if params.lastName: person["lastName"] = params.lastName
        if params.email:    person["emails"] = [{"value": params.email}]
        if params.phone:    person["phones"] = [{"value": params.phone}]
        if params.tags:     person["tags"] = params.tags
        payload = {
            "source": params.source,
            "system": "ARIA-MCP",
            "type": params.type,
            "person": person,
        }
        if params.message: payload["message"] = params.message
        data = await fub_post("/events", payload)
        return ok(data)
    except Exception as e:
        return err(e)


class UpdateContactInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    id:          int                  = Field(...,  description="FUB person ID", ge=1)
    firstName:   Optional[str]        = Field(None, description="First name")
    lastName:    Optional[str]        = Field(None, description="Last name")
    email:       Optional[str]        = Field(None, description="Email address")
    phone:       Optional[str]        = Field(None, description="Phone number")
    stage:       Optional[str]        = Field(None, description="Stage e.g. Hot, Warm, Cold, Lead, Client")
    assignedTo:  Optional[str]        = Field(None, description="Assign to agent by email")
    tags:        Optional[list[str]]  = Field(None, description="Replace all tags")


@mcp.tool(
    name="fub_update_contact",
    annotations={"title": "Update FUB Contact", "idempotentHint": True}
)
async def fub_update_contact(params: UpdateContactInput) -> str:
    """Update an existing FUB contact's fields.

    Only fields provided are updated. To clear a field, pass an empty string.

    Args:
        params: Contact ID plus any fields to update.

    Returns:
        JSON updated contact object.
    """
    try:
        body: dict = {}
        if params.firstName:  body["firstName"] = params.firstName
        if params.lastName:   body["lastName"] = params.lastName
        if params.email:      body["emails"] = [{"value": params.email}]
        if params.phone:      body["phones"] = [{"value": params.phone}]
        if params.stage:      body["stage"] = params.stage
        if params.assignedTo: body["assignedTo"] = params.assignedTo
        if params.tags is not None: body["tags"] = params.tags
        data = await fub_put(f"/people/{params.id}", body)
        return ok(data)
    except Exception as e:
        return err(e)


class RankContactInput(BaseModel):
    id:   int           = Field(..., description="FUB person ID", ge=1)
    rank: str           = Field(..., description="Priority rank: Hot, Warm, or Cold")
    note: Optional[str] = Field(None, description="Optional note explaining the ranking")


@mcp.tool(
    name="fub_rank_contact",
    annotations={"title": "Rank Contact Hot/Warm/Cold", "idempotentHint": True}
)
async def fub_rank_contact(params: RankContactInput) -> str:
    """Set a contact's stage/priority to Hot, Warm, or Cold.

    Optionally adds a note explaining the ranking decision.
    This is the primary tool for AI lead scoring output.

    Args:
        params: Contact ID, rank (Hot/Warm/Cold), optional note.

    Returns:
        Confirmation string with contact ID and assigned rank.
    """
    try:
        await fub_put(f"/people/{params.id}", {"stage": params.rank})
        if params.note:
            await fub_post("/notes", {
                "personId": params.id,
                "body": f"[AI Rank: {params.rank}] {params.note}"
            })
        return f"Contact {params.id} ranked as {params.rank}."
    except Exception as e:
        return err(e)


class BulkRankInput(BaseModel):
    contacts: list[dict] = Field(..., description="List of {id, rank} objects e.g. [{id: 123, rank: 'Hot'}]", min_length=1, max_length=50)


@mcp.tool(
    name="fub_bulk_rank_contacts",
    annotations={"title": "Bulk Rank Contacts"}
)
async def fub_bulk_rank_contacts(params: BulkRankInput) -> str:
    """Rank multiple contacts at once (up to 50).

    Processes each contact individually and returns results summary.

    Args:
        params: List of {id, rank} objects where rank is Hot/Warm/Cold.

    Returns:
        JSON array of {id, rank, status} for each contact.
    """
    results = []
    for item in params.contacts:
        try:
            await fub_put(f"/people/{item['id']}", {"stage": item["rank"]})
            results.append({"id": item["id"], "rank": item["rank"], "status": "ok"})
        except Exception as e:
            results.append({"id": item["id"], "rank": item["rank"], "status": str(e)})
    return ok(results)


class GetAllContactsInput(BaseModel):
    stage: Optional[str] = Field(None, description="Filter by stage")
    tags:  Optional[str] = Field(None, description="Filter by tag")


@mcp.tool(
    name="fub_get_all_contacts",
    annotations={"title": "Get All FUB Contacts", "readOnlyHint": True}
)
async def fub_get_all_contacts(params: GetAllContactsInput) -> str:
    """Fetch ALL contacts from FUB with auto-pagination (max 1000).

    Use for bulk operations, exports, or full pipeline review.

    Args:
        params: Optional stage/tags filter.

    Returns:
        JSON with count and full contacts array.
    """
    try:
        f: dict = {}
        if params.stage: f["stage"] = params.stage
        if params.tags:  f["tags"] = params.tags
        people = await fub_paginate("/people", f)
        return ok({"count": len(people), "people": people})
    except Exception as e:
        return err(e)


# ══════════════════════════════════════════════════════════════════════════════
# FUB — NOTES & TASKS
# ══════════════════════════════════════════════════════════════════════════════

class AddNoteInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    personId: int = Field(..., description="FUB person ID", ge=1)
    body:     str = Field(..., description="Note content", min_length=1, max_length=5000)


@mcp.tool(
    name="fub_add_note",
    annotations={"title": "Add Note to Contact"}
)
async def fub_add_note(params: AddNoteInput) -> str:
    """Add a note to a contact's timeline in FUB.

    Notes appear in the contact's activity feed and are visible to all agents.
    Used for AI analysis results, call summaries, and follow-up details.

    Args:
        params: Person ID and note body text.

    Returns:
        JSON created note object with ID and timestamp.
    """
    try:
        data = await fub_post("/notes", {"personId": params.personId, "body": params.body})
        return ok(data)
    except Exception as e:
        return err(e)


class CreateTaskInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    personId:       int           = Field(...,  description="FUB person ID", ge=1)
    description:    str           = Field(...,  description="Task description", min_length=1)
    dueDate:        Optional[str] = Field(None, description="Due date in YYYY-MM-DD format")
    assignedUserId: Optional[int] = Field(None, description="Assign to specific user ID")


@mcp.tool(
    name="fub_create_task",
    annotations={"title": "Create Follow-Up Task"}
)
async def fub_create_task(params: CreateTaskInput) -> str:
    """Create a follow-up task for a contact in FUB.

    Tasks appear in the agent's task list and can trigger notifications.

    Args:
        params: Person ID, description, optional due date and assignee.

    Returns:
        JSON created task object with ID.
    """
    try:
        body: dict = {
            "personId": params.personId,
            "description": params.description,
        }
        if params.dueDate:        body["dueDate"] = params.dueDate
        if params.assignedUserId: body["assignedUserId"] = params.assignedUserId
        data = await fub_post("/tasks", body)
        return ok(data)
    except Exception as e:
        return err(e)


class TimelineInput(BaseModel):
    personId: int = Field(..., description="FUB person ID", ge=1)
    limit:    int = Field(30,  description="Max activity items (1-100)", ge=1, le=100)


@mcp.tool(
    name="fub_get_contact_timeline",
    annotations={"title": "Get Contact Activity Timeline", "readOnlyHint": True}
)
async def fub_get_contact_timeline(params: TimelineInput) -> str:
    """Get a contact's full activity timeline from FUB.

    Returns calls, emails, texts, notes, tasks, and stage changes in reverse
    chronological order.

    Args:
        params: Person ID and optional result limit.

    Returns:
        JSON events array with type, date, body, and author fields.
    """
    try:
        data = await fub_get("/events", {"personId": params.personId, "limit": params.limit})
        return ok(data)
    except Exception as e:
        return err(e)


# ══════════════════════════════════════════════════════════════════════════════
# FUB — ACTION PLANS
# ══════════════════════════════════════════════════════════════════════════════

class ListPlansInput(BaseModel):
    limit: int = Field(50, description="Max plans to return (1-100)", ge=1, le=100)


@mcp.tool(
    name="fub_list_action_plans",
    annotations={"title": "List FUB Action Plans", "readOnlyHint": True}
)
async def fub_list_action_plans(params: ListPlansInput) -> str:
    """List all Action Plans (drip sequences) available in FUB.

    Use this first to find the correct Action Plan ID before enrolling contacts.
    IMPORTANT: On this account, direct SMS/email endpoints return 403 —
    Action Plans are the ONLY way to send outreach.

    Args:
        params: Limit on number of plans to return.

    Returns:
        JSON list of action plans with id, name, and description.
    """
    try:
        data = await fub_get("/actionPlans", {"limit": params.limit})
        return ok(data)
    except Exception as e:
        return err(e)


class ApplyPlanInput(BaseModel):
    personId:     int = Field(..., description="FUB person ID", ge=1)
    actionPlanId: int = Field(..., description="Action Plan ID to enroll in", ge=1)


@mcp.tool(
    name="fub_apply_action_plan",
    annotations={"title": "Enroll Contact in Action Plan"}
)
async def fub_apply_action_plan(params: ApplyPlanInput) -> str:
    """Enroll a contact in a FUB Action Plan (drip sequence).

    This is the ONLY approved outreach method on this account —
    direct /textMessages and /emails return 403.

    Args:
        params: Person ID and Action Plan ID.

    Returns:
        Confirmation string.
    """
    try:
        await fub_post("/events", {
            "source": "ARIA-MCP",
            "system": "ARIA-MCP",
            "type": "Action Plan",
            "actionPlanId": params.actionPlanId,
            "person": {"id": params.personId},
        })
        return f"Contact {params.personId} enrolled in action plan {params.actionPlanId}."
    except Exception as e:
        return err(e)


class BulkApplyPlanInput(BaseModel):
    personIds:    list[int] = Field(..., description="List of FUB person IDs", min_length=1, max_length=100)
    actionPlanId: int       = Field(..., description="Action Plan ID", ge=1)


@mcp.tool(
    name="fub_bulk_apply_action_plan",
    annotations={"title": "Bulk Enroll in Action Plan"}
)
async def fub_bulk_apply_action_plan(params: BulkApplyPlanInput) -> str:
    """Enroll multiple contacts in the same Action Plan (up to 100).

    Args:
        params: List of person IDs and Action Plan ID.

    Returns:
        JSON array of {personId, status} results.
    """
    results = []
    for pid in params.personIds:
        try:
            await fub_post("/events", {
                "source": "ARIA-MCP",
                "system": "ARIA-MCP",
                "type": "Action Plan",
                "actionPlanId": params.actionPlanId,
                "person": {"id": pid},
            })
            results.append({"personId": pid, "status": "enrolled"})
        except Exception as e:
            results.append({"personId": pid, "status": str(e)})
    return ok(results)


@mcp.tool(
    name="fub_list_pipelines",
    annotations={"title": "List FUB Pipeline Stages", "readOnlyHint": True}
)
async def fub_list_pipelines() -> str:
    """List all pipeline stages configured in FUB.

    Returns:
        JSON list of stage objects with id and name.
    """
    try:
        data = await fub_get("/stages")
        return ok(data)
    except Exception as e:
        return err(e)


# ══════════════════════════════════════════════════════════════════════════════
# META ADS — ARIA PROPERTIES (act_41421368)
# ══════════════════════════════════════════════════════════════════════════════

@mcp.tool(
    name="meta_list_campaigns",
    annotations={"title": "List ARIA Meta Campaigns", "readOnlyHint": True}
)
async def meta_list_campaigns(adAccountId: Optional[str] = None) -> str:
    """List all Meta ad campaigns for ARIA Properties.

    Args:
        adAccountId: Optional override. Defaults to act_41421368 (ARIA Properties).

    Returns:
        JSON list of campaigns with id, name, status, objective, daily_budget.
    """
    try:
        account = adAccountId or ARIA_ACCOUNT
        data = await meta_get(f"/{account}/campaigns", {
            "fields": "id,name,status,objective,daily_budget,lifetime_budget,start_time,stop_time"
        })
        return ok(data)
    except Exception as e:
        return err(e)


class CreateCampaignInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    name:                 str            = Field(...,        description="Campaign name e.g. 'ARIA | 1094 Garden Lane | Reach'", min_length=1)
    objective:            str            = Field(...,        description="REACH, LEAD_GENERATION, TRAFFIC, CONVERSIONS, MESSAGES, BRAND_AWARENESS")
    specialAdCategories:  list[str]      = Field(["HOUSING"],description="Always include HOUSING for real estate")
    status:               str            = Field("PAUSED",   description="ACTIVE or PAUSED — use PAUSED for safety")
    dailyBudget:          Optional[int]  = Field(None,       description="Daily budget in CENTS (e.g. 500 = $5.00). Omit to use ad-set budgets instead of CBO.", ge=100)
    adAccountId:          Optional[str]  = Field(None,       description="Override ad account. Defaults to ARIA Properties.")


@mcp.tool(
    name="meta_create_campaign",
    annotations={"title": "Create ARIA Meta Campaign"}
)
async def meta_create_campaign(params: CreateCampaignInput) -> str:
    """Create a new Meta ad campaign for ARIA Properties.

    IMPORTANT: Always use specialAdCategories=['HOUSING'] for real estate listings.
    Omit dailyBudget unless you want Campaign Budget Optimization (CBO) —
    with CBO, ad sets cannot have their own budgets.

    Args:
        params: Campaign name, objective, special ad categories, status, optional budget.

    Returns:
        JSON with created campaign ID.
    """
    try:
        account = params.adAccountId or ARIA_ACCOUNT
        payload = {
            "name": params.name,
            "objective": OBJECTIVE_MAP.get(params.objective, params.objective),
            "special_ad_categories": json.dumps(params.specialAdCategories),
            "status": params.status,
        }
        if params.dailyBudget:
            payload["daily_budget"] = str(params.dailyBudget)
        data = await meta_post(f"/{account}/campaigns", payload)
        return ok(data)
    except Exception as e:
        return err(e)


class UpdateCampaignInput(BaseModel):
    campaignId:  str           = Field(...,  description="Meta campaign ID")
    status:      Optional[str] = Field(None, description="ACTIVE, PAUSED, or ARCHIVED")
    name:        Optional[str] = Field(None, description="New campaign name")
    dailyBudget: Optional[int] = Field(None, description="New daily budget in cents", ge=100)


@mcp.tool(
    name="meta_update_campaign",
    annotations={"title": "Update ARIA Meta Campaign", "idempotentHint": True}
)
async def meta_update_campaign(params: UpdateCampaignInput) -> str:
    """Pause, resume, rename, or change budget of an existing campaign.

    Args:
        params: Campaign ID plus fields to update.

    Returns:
        JSON with success confirmation.
    """
    try:
        payload: dict = {}
        if params.status:      payload["status"] = params.status
        if params.name:        payload["name"] = params.name
        if params.dailyBudget: payload["daily_budget"] = str(params.dailyBudget)
        data = await meta_post(f"/{params.campaignId}", payload)
        return ok(data)
    except Exception as e:
        return err(e)


class CreateAdSetInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    campaignId:  str           = Field(...,        description="Parent campaign ID")
    name:        str           = Field(...,        description="Ad set name", min_length=1)
    dailyBudget: Optional[int] = Field(None,       description="Daily budget in cents. Omit for CBO campaigns.", ge=100)
    status:      str           = Field("PAUSED",   description="ACTIVE or PAUSED")
    adAccountId: Optional[str] = Field(None,       description="Override ad account")


@mcp.tool(
    name="meta_create_ad_set",
    annotations={"title": "Create ARIA Meta Ad Set"}
)
async def meta_create_ad_set(params: CreateAdSetInput) -> str:
    """Create an ad set for an ARIA Properties campaign.

    HOUSING special ad category restrictions (Fair Housing Act):
    - No income targeting
    - No gender targeting
    - No narrow age targeting
    Uses broad US geo targeting only.

    Args:
        params: Campaign ID, name, optional daily budget, status.

    Returns:
        JSON with created ad set ID.
    """
    try:
        account = params.adAccountId or ARIA_ACCOUNT
        targeting = {"geo_locations": {"countries": ["US"]}}
        payload: dict = {
            "name": params.name,
            "campaign_id": params.campaignId,
            "optimization_goal": "REACH",
            "billing_event": "IMPRESSIONS",
            "status": params.status,
            "targeting": json.dumps(targeting),
        }
        if params.dailyBudget:
            payload["daily_budget"] = str(params.dailyBudget)
        data = await meta_post(f"/{account}/adsets", payload)
        return ok(data)
    except Exception as e:
        return err(e)


class GetInsightsInput(BaseModel):
    level:       str           = Field("campaign", description="account, campaign, adset, or ad")
    objectId:    Optional[str] = Field(None,       description="Specific campaign/adset/ad ID. Omit for account level.")
    datePreset:  str           = Field("last_7d",  description="today, yesterday, last_7d, last_14d, last_30d, last_month, this_month")
    adAccountId: Optional[str] = Field(None,       description="Override ad account")


@mcp.tool(
    name="meta_get_insights",
    annotations={"title": "Get ARIA Campaign Insights", "readOnlyHint": True}
)
async def meta_get_insights(params: GetInsightsInput) -> str:
    """Get performance metrics for ARIA Properties campaigns.

    Returns spend, reach, impressions, clicks, CTR, CPM for the specified
    date range and level.

    Args:
        params: Level (campaign/adset/ad), optional object ID, date preset.

    Returns:
        JSON insights data with all performance metrics.
    """
    try:
        account = params.adAccountId or ARIA_ACCOUNT
        endpoint = f"/{params.objectId}/insights" if params.objectId else f"/{account}/insights"
        data = await meta_get(endpoint, {
            "level": params.level,
            "date_preset": params.datePreset,
            "fields": "campaign_name,adset_name,spend,impressions,reach,frequency,clicks,ctr,cpm,actions",
        })
        return ok(data)
    except Exception as e:
        return err(e)


# ── ENTRY POINT ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    mcp.run(transport="sse", host="0.0.0.0", port=port)
