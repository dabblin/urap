"""Module III — Warp Mode AI Copilot.

Given an ICP, autonomously:
  1. Queries the enrichment waterfall for matching leads
  2. Generates personalized email copy via Gemini 2.0 Flash (draft)
  3. Refines copy via Claude Sonnet 4.6 (review)
  4. Stores job results in Supabase urap_warp_jobs
  5. Fires Telegram alert on completion

Required env vars:
  GEMINI_API_KEY     — Google AI Studio key (free tier available)
  ANTHROPIC_API_KEY  — Anthropic API key (review pass; falls through if missing)
"""
import json
import os
import re
import sys
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

import httpx

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from modules.m1_intelligence.enrichment import EnrichmentService
from tier3.telegram.client import notify_warp_job_done

GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
CLAUDE_URL = "https://api.anthropic.com/v1/messages"
CLAUDE_MODEL = "claude-sonnet-4-6"


@dataclass
class WarpLead:
    lead_id: str
    name: str
    email: str
    title: str
    company: str
    subject: str
    body_html: str
    copy_status: str  # "generated" | "reviewed" | "fallback" | "error"


@dataclass
class WarpJobResult:
    job_id: str
    icp_label: str
    leads_found: int
    sequences_queued: int
    generated: list = field(default_factory=list)
    error: Optional[str] = None


class WarpModeAgent:
    def __init__(self) -> None:
        self._enrichment = EnrichmentService()
        self._supabase = None

    def _db(self):
        if self._supabase is None:
            from supabase import create_client
            self._supabase = create_client(
                os.environ["SUPABASE_URL"],
                os.environ["SUPABASE_ANON_KEY"],
            )
        return self._supabase

    # ── AI copy generation ────────────────────────────────────────────────────

    async def _draft_copy_gemini(self, lead: dict, icp: dict) -> tuple[str, str]:
        """Generate draft subject + body via Gemini Flash. Returns ("", "") on failure."""
        api_key = os.environ.get("GEMINI_API_KEY", "")
        if not api_key:
            return ("", "")

        prompt = f"""You are an expert B2B sales copywriter. Write a personalized cold outreach email.

Lead:
- Name: {lead.get('name', 'there')}
- Title: {lead.get('title', 'professional')}
- Company: {lead.get('company', '')}

ICP Context:
- Target Role: {icp.get('title', '')}
- Industry: {icp.get('industry', '')}
- Value Prop: {icp.get('value_prop', 'AI-powered revenue acceleration that cuts SDR overhead by 60%')}

Rules:
- Subject: 6–8 words, no emojis, curiosity-driven, no "quick" or "just"
- Body: 3 short paragraphs, under 150 words total
- No generic opener ("I hope this finds you well", "My name is...")
- First line references something specific about their role or company
- Clear single CTA: propose a 15-min call this week
- Tone: direct, peer-to-peer, no hype

Return valid JSON only: {{"subject": "...", "body_html": "<p>...</p><p>...</p><p>...</p>"}}"""

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{GEMINI_URL}?key={api_key}",
                    json={
                        "contents": [{"parts": [{"text": prompt}]}],
                        "generationConfig": {"responseMimeType": "application/json"},
                    },
                    timeout=30,
                )
            if resp.status_code != 200:
                return ("", "")
            data = resp.json()
            text = data["candidates"][0]["content"]["parts"][0]["text"]
            parsed = json.loads(text)
            return (parsed.get("subject", ""), parsed.get("body_html", ""))
        except Exception as e:
            print(f"[warp_mode] Gemini error: {e}")
            return ("", "")

    async def _review_copy_claude(self, subject: str, body_html: str, lead: dict) -> tuple[str, str, bool]:
        """Refine draft via Claude Sonnet. Returns (subject, body_html, was_reviewed)."""
        api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        if not api_key:
            return (subject, body_html, False)

        prompt = f"""Review this cold email and improve it if needed. Return the refined version as JSON.

Lead: {lead.get('name')} — {lead.get('title')} @ {lead.get('company')}

Draft Subject: {subject}
Draft Body:
{body_html}

Review criteria:
- If it's specific, concise, and has a clear CTA → return it unchanged
- Fix generic phrases, weak openers, or vague CTAs
- Keep the same structure and word count
- Preserve HTML paragraph tags

Return valid JSON only: {{"subject": "...", "body_html": "..."}}"""

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    CLAUDE_URL,
                    headers={
                        "x-api-key": api_key,
                        "anthropic-version": "2023-06-01",
                        "content-type": "application/json",
                    },
                    json={
                        "model": CLAUDE_MODEL,
                        "max_tokens": 1024,
                        "messages": [{"role": "user", "content": prompt}],
                    },
                    timeout=30,
                )
            if resp.status_code != 200:
                return (subject, body_html, False)
            data = resp.json()
            text = data["content"][0]["text"]
            match = re.search(r'\{.*\}', text, re.DOTALL)
            if match:
                parsed = json.loads(match.group())
                return (
                    parsed.get("subject", subject),
                    parsed.get("body_html", body_html),
                    True,
                )
            return (subject, body_html, False)
        except Exception as e:
            print(f"[warp_mode] Claude review error: {e}")
            return (subject, body_html, False)

    def _fallback_copy(self, lead: dict, icp: dict) -> tuple[str, str]:
        """Static template fallback when AI APIs are not configured."""
        name = lead.get("name", "there")
        first = name.split()[0] if name else "there"
        company = lead.get("company", "your company")
        value_prop = icp.get("value_prop", "AI-powered revenue acceleration")
        subject = f"Revenue acceleration for {company}"
        body_html = (
            f"<p>Hi {first},</p>"
            f"<p>I noticed {company} is scaling its revenue team — "
            f"we help teams like yours with {value_prop}.</p>"
            f"<p>Worth a 15-minute call this week to see if it's relevant?</p>"
        )
        return (subject, body_html)

    async def _generate_copy_for_lead(self, lead: dict, icp: dict) -> WarpLead:
        subject, body_html = await self._draft_copy_gemini(lead, icp)
        copy_status = "error"

        if subject and body_html:
            subject, body_html, reviewed = await self._review_copy_claude(subject, body_html, lead)
            copy_status = "reviewed" if reviewed else "generated"
        else:
            subject, body_html = self._fallback_copy(lead, icp)
            copy_status = "fallback"

        return WarpLead(
            lead_id=lead.get("lead_id", str(uuid.uuid4())),
            name=lead.get("name", ""),
            email=lead.get("email", ""),
            title=lead.get("title", ""),
            company=lead.get("company", ""),
            subject=subject,
            body_html=body_html,
            copy_status=copy_status,
        )

    # ── Job runner ────────────────────────────────────────────────────────────

    async def run_job(self, icp: dict, tenant_id: str) -> WarpJobResult:
        """Run a full Warp Mode job: enrich → generate copy → store → alert.

        icp keys: title, domain, industry, value_prop, icp_label, limit (default 10)
        """
        job_id = str(uuid.uuid4())
        icp_label = icp.get("icp_label", f"{icp.get('title', 'ICP')} @ {icp.get('domain', 'domain')}")
        limit = min(int(icp.get("limit", 10)), 25)

        # Step 1 — enrich leads
        leads: list[dict] = []
        domain = icp.get("domain", "")
        if domain:
            try:
                leads = await self._enrichment.bulk_enrich_domain(
                    tenant_id=tenant_id,
                    domain=domain,
                    limit=limit,
                )
            except Exception as e:
                print(f"[warp_mode] Enrichment error: {e}")

        if not leads:
            return WarpJobResult(
                job_id=job_id,
                icp_label=icp_label,
                leads_found=0,
                sequences_queued=0,
                error="No leads found for this ICP. Check domain or add more enrichment credits.",
            )

        # Step 2 — generate copy for each lead
        warp_leads: list[WarpLead] = []
        for lead in leads:
            wl = await self._generate_copy_for_lead(lead, icp)
            warp_leads.append(wl)

        sequences_queued = sum(1 for wl in warp_leads if wl.copy_status != "error")

        # Step 3 — store job in Supabase
        job_record = {
            "id": job_id,
            "tenant_id": tenant_id,
            "icp_label": icp_label,
            "icp": icp,
            "leads_found": len(leads),
            "sequences_queued": sequences_queued,
            "generated": [
                {
                    "lead_id": wl.lead_id,
                    "name": wl.name,
                    "email": wl.email,
                    "title": wl.title,
                    "company": wl.company,
                    "subject": wl.subject,
                    "body_preview": wl.body_html[:200],
                    "body_html": wl.body_html,
                    "copy_status": wl.copy_status,
                }
                for wl in warp_leads
            ],
            "status": "complete",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        try:
            self._db().table("urap_warp_jobs").insert(job_record).execute()
        except Exception as e:
            print(f"[warp_mode] Supabase store error: {e}")

        # Step 4 — Telegram alert
        notify_warp_job_done(icp_label, len(leads), sequences_queued)

        return WarpJobResult(
            job_id=job_id,
            icp_label=icp_label,
            leads_found=len(leads),
            sequences_queued=sequences_queued,
            generated=job_record["generated"],
        )

    def list_jobs(self, tenant_id: str, limit: int = 10) -> list[dict]:
        """Return recent Warp Mode jobs for this tenant, newest first."""
        try:
            result = (
                self._db()
                .table("urap_warp_jobs")
                .select("id,icp_label,leads_found,sequences_queued,status,created_at")
                .eq("tenant_id", tenant_id)
                .order("created_at", desc=True)
                .limit(limit)
                .execute()
            )
            return result.data or []
        except Exception:
            return []
