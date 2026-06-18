"""
People discovery — the URAP "people finder".

Strategy, in priority order:
  1. Apollo.io People Search (`mixed_people/search`) — the legitimate, ToS-compliant
     source of LinkedIn-grade people data: name, title, company, LinkedIn URL,
     seniority, department, location. Primary source.
  2. DuckDuckGo public-web sourcing of `linkedin.com/in` profiles — free, no key,
     used only when Apollo returns nothing. Parses name + headline (title @ company)
     from public SERP snippets. Best-effort; never scrapes behind LinkedIn's auth wall.

Apollo's free/low tiers LOCK emails (returns an `email_not_unlocked@…` placeholder).
That's by design — URAP's value layer is the existing enrichment waterfall
(Prospeo → Snov → Hunter), which reveals + verifies the real email from the
discovered name + company domain. People without a usable email are passed through
that waterfall before the result is returned.
"""
from __future__ import annotations

import asyncio
import os
import re
import uuid
from html import unescape
from typing import Optional

import httpx

APOLLO_API_KEY = os.getenv("APOLLO_API_KEY", "")
BRAVE_SEARCH_API_KEY = os.getenv("BRAVE_SEARCH_API_KEY", "")

_DOMAIN_RE = re.compile(r"\b[\w-]+\.(?:com|io|ai|co|net|org|app|us|tech|dev|biz|info)\b", re.I)

# Map free-text seniority words → Apollo's controlled `person_seniorities` values.
_SENIORITY_MAP = {
    "owner": "owner", "founder": "founder", "co-founder": "founder", "cofounder": "founder",
    "c-suite": "c_suite", "csuite": "c_suite", "c suite": "c_suite",
    "ceo": "c_suite", "cto": "c_suite", "cfo": "c_suite", "coo": "c_suite",
    "cmo": "c_suite", "cio": "c_suite", "chief": "c_suite", "executive": "c_suite",
    "partner": "partner", "vp": "vp", "vice president": "vp",
    "head": "head", "director": "director", "manager": "manager",
    "senior": "senior", "entry": "entry", "intern": "intern",
}

# Map free-text headcount → Apollo `organization_num_employees_ranges` buckets.
_SIZE_BUCKETS = [
    (1, 10, "1,10"), (11, 50, "11,50"), (51, 200, "51,200"),
    (201, 500, "201,500"), (501, 1000, "501,1000"),
    (1001, 5000, "1001,5000"), (5001, 10000, "5001,10000"),
    (10001, 1_000_000, "10001,1000000"),
]

_LOCKED_EMAIL = re.compile(r"email_not_unlocked|not_unlocked|locked@", re.I)


def _split_csv(s: Optional[str]) -> list[str]:
    if not s:
        return []
    return [p.strip() for p in re.split(r"[,;]", s) if p.strip()]


def _map_seniorities(raw: Optional[str]) -> list[str]:
    out: list[str] = []
    for token in _split_csv(raw):
        low = token.lower()
        for key, val in _SENIORITY_MAP.items():
            if key in low and val not in out:
                out.append(val)
    return out


def _map_employee_ranges(raw: Optional[str]) -> list[str]:
    """Pull every integer out of a free-text size string and return the buckets they touch."""
    if not raw:
        return []
    nums = [int(n) for n in re.findall(r"\d[\d,]*", raw.replace(",", ""))]
    if not nums:
        return []
    lo, hi = min(nums), max(nums)
    return [bucket for blo, bhi, bucket in _SIZE_BUCKETS if not (bhi < lo or blo > hi)]


def _is_locked(email: str) -> bool:
    return not email or bool(_LOCKED_EMAIL.search(email)) or "@" not in email


def _full_name(first: str, last: str, fallback: str = "") -> str:
    return f"{first or ''} {last or ''}".strip() or fallback


# ── Apollo people search ──────────────────────────────────────────────────────

async def _apollo_people(filters: dict, limit: int) -> list[dict]:
    """Query Apollo mixed_people/search and normalize to URAP person dicts."""
    if not APOLLO_API_KEY:
        return []

    payload: dict = {"page": 1, "per_page": min(max(limit, 1), 100)}

    titles = _split_csv(filters.get("titles"))
    if titles:
        payload["person_titles"] = titles

    seniorities = _map_seniorities(filters.get("seniority"))
    if seniorities:
        payload["person_seniorities"] = seniorities

    departments = _split_csv(filters.get("department"))
    if departments:
        payload["person_departments"] = [d.lower() for d in departments]

    locations = _split_csv(filters.get("location"))
    if locations:
        payload["person_locations"] = locations

    domains = _split_csv(filters.get("domain"))
    if domains:
        payload["q_organization_domains"] = "\n".join(domains)

    ranges = _map_employee_ranges(filters.get("employeeSize"))
    if ranges:
        payload["organization_num_employees_ranges"] = ranges

    # Industry + keywords + free-text query all fold into Apollo's keyword match.
    kw_parts = [
        filters.get("industry") or "",
        filters.get("keywords") or "",
        filters.get("query") or "",
    ]
    kw = " ".join(p.strip() for p in kw_parts if p and p.strip()).strip()
    if kw:
        payload["q_keywords"] = kw

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            r = await client.post(
                "https://api.apollo.io/v1/mixed_people/search",
                json=payload,
                headers={
                    "Content-Type": "application/json",
                    "Cache-Control": "no-cache",
                    "X-Api-Key": APOLLO_API_KEY,
                },
            )
        if r.status_code != 200:
            return []
        people = r.json().get("people", []) or []
    except Exception:
        return []

    out: list[dict] = []
    for p in people:
        org = p.get("organization") or p.get("account") or {}
        domain = (org.get("primary_domain") or "") or ""
        if not domain:
            web = org.get("website_url") or ""
            m = _DOMAIN_RE.search(web)
            if m:
                domain = m.group(0).lower()
        loc = ", ".join(filter(None, [p.get("city") or "", p.get("state") or "", p.get("country") or ""]))
        email = p.get("email") or ""
        if _is_locked(email):
            email = ""
        out.append({
            "first_name": p.get("first_name") or "",
            "last_name":  p.get("last_name") or "",
            "name":       p.get("name") or _full_name(p.get("first_name") or "", p.get("last_name") or ""),
            "title":      p.get("title") or "",
            "company":    org.get("name") or "",
            "domain":     domain,
            "linkedin_url": p.get("linkedin_url") or "",
            "location":   loc,
            "seniority":  p.get("seniority") or "",
            "email":      email,
            "source":     "apollo",
        })
    return out


# ── Hunter.io people-per-company (free, keyed) ────────────────────────────────
# The reliable free path on current plans: discover companies (Google Places / Yelp /
# Foursquare — already keyed), then pull the NAMED people + titles + emails at each
# company's domain via Hunter.io domain-search. Title/seniority filters are applied
# to Hunter's `position` field.

_PRIORITY_TITLES = ["owner", "founder", "ceo", "president", "chief", "partner",
                    "vp", "vice president", "head", "director", "manager"]

# Cap companies we sweep so a single search can't blow Hunter's 50-req/month free quota.
_MAX_COMPANIES_SWEPT = 8


def _wanted_title_tokens(filters: dict) -> list[str]:
    tokens = [t.lower() for t in _split_csv(filters.get("titles"))]
    # Seniority maps to representative title words for substring matching.
    for sv in _map_seniorities(filters.get("seniority")):
        tokens += {
            "owner": ["owner"], "founder": ["founder", "co-founder"],
            "c_suite": ["chief", "ceo", "cto", "cfo", "coo", "cmo", "cio"],
            "partner": ["partner"], "vp": ["vp", "vice president"],
            "head": ["head"], "director": ["director"], "manager": ["manager"],
        }.get(sv, [])
    return list(dict.fromkeys(tokens))


def _title_matches(position: str, wanted: list[str]) -> bool:
    if not wanted:
        return True
    low = (position or "").lower()
    return any(tok in low for tok in wanted)


async def _company_sweep_people(filters: dict, limit: int) -> list[dict]:
    """Discover companies (free local providers) → pull named people at each domain
    via Prospeo (primary) then Hunter (fallback). Both run on the keyed free plans."""
    from tier3.hunter.client import HunterClient
    from tier3.prospeo.client import ProspeoClient
    from modules.m1_intelligence.company_search import search_companies

    hunter = HunterClient()
    prospeo = ProspeoClient()
    if not (os.getenv("HUNTER_API_KEY", "") or os.getenv("PROSPEO_API_KEY", "")):
        return []

    # 1. Resolve the set of companies (domain + display name) to sweep.
    domains = _split_csv(filters.get("domain"))
    companies: list[dict] = [{"domain": d, "name": ""} for d in domains]

    if not companies:
        kw_parts = [filters.get("keywords") or "", filters.get("query") or ""]
        keywords = " ".join(p.strip() for p in kw_parts if p and p.strip()).strip()
        try:
            found = await search_companies(
                keywords=keywords,
                location=filters.get("location") or "",
                industry=filters.get("industry") or "",
                limit=_MAX_COMPANIES_SWEPT,
            )
        except Exception:
            found = []
        for c in found:
            if c.get("domain"):
                companies.append({"domain": c["domain"], "name": c.get("name") or ""})

    companies = companies[:_MAX_COMPANIES_SWEPT]
    if not companies:
        return []

    wanted = _wanted_title_tokens(filters)

    async def _sweep(co: dict) -> list[dict]:
        domain = co["domain"]
        company_name = co.get("name") or domain
        rows: list[dict] = []

        # Prospeo first — richer (often includes LinkedIn URL + verified flag).
        try:
            for p in await prospeo.domain_search(domain, limit=10):
                if not getattr(p, "email", "") or not _title_matches(getattr(p, "title", "") or "", wanted):
                    continue
                rows.append({
                    "first_name": p.first_name or "", "last_name": p.last_name or "",
                    "name": _full_name(p.first_name or "", p.last_name or "", p.email.split("@")[0]),
                    "title": getattr(p, "title", "") or "", "company": company_name, "domain": domain,
                    "linkedin_url": getattr(p, "linkedin_url", "") or "", "location": "", "seniority": "",
                    "email": p.email, "email_verified": bool(getattr(p, "verified", False)),
                    "source": "prospeo",
                })
        except Exception:
            pass

        # Hunter fallback when Prospeo found nothing at this domain.
        if not rows:
            try:
                for h in await hunter.domain_search(domain, limit=10):
                    if not h.email or not _title_matches(h.title or "", wanted):
                        continue
                    rows.append({
                        "first_name": h.first_name or "", "last_name": h.last_name or "",
                        "name": _full_name(h.first_name or "", h.last_name or "", h.email.split("@")[0]),
                        "title": h.title or "", "company": company_name, "domain": domain,
                        "linkedin_url": "", "location": "", "seniority": "",
                        "email": h.email, "email_verified": (h.confidence or 0) >= 70,
                        "source": "hunter",
                    })
            except Exception:
                pass
        return rows

    swept = await asyncio.gather(*[_sweep(c) for c in companies])

    people: list[dict] = []
    seen: set[str] = set()
    # Priority-title people first, then the rest, deduped by email.
    flat = [r for batch in swept for r in batch]
    flat.sort(key=lambda r: 0 if _title_matches(r["title"], _PRIORITY_TITLES) else 1)
    for r in flat:
        if r["email"] in seen:
            continue
        seen.add(r["email"])
        people.append(r)
        if len(people) >= limit:
            break
    return people


# ── Brave Search — public LinkedIn profile sourcing (free tier: 2k queries/mo) ─
# The reliable free way to surface public LinkedIn profiles by role/industry/location.
# We query `site:linkedin.com/in <terms>` and parse name/title/company from the SERP.
# Returns people WITHOUT emails (no scraping behind LinkedIn's auth wall) — when a
# company domain is resolvable, the orchestrator's enrichment waterfall reveals the email.

def _brave_query(filters: dict) -> str:
    terms = " ".join(filter(None, [
        filters.get("titles") or filters.get("seniority") or "",
        filters.get("industry") or "",
        filters.get("keywords") or "",
        filters.get("location") or "",
        filters.get("query") or "",
    ])).strip()
    return f"site:linkedin.com/in {terms}".strip()


async def _brave_people(filters: dict, limit: int) -> list[dict]:
    if not BRAVE_SEARCH_API_KEY:
        return []
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            r = await client.get(
                "https://api.search.brave.com/res/v1/web/search",
                params={"q": _brave_query(filters), "count": min(max(limit, 1), 20), "result_filter": "web"},
                headers={
                    "Accept": "application/json",
                    "X-Subscription-Token": BRAVE_SEARCH_API_KEY,
                },
            )
        if r.status_code != 200:
            return []
        results = (r.json().get("web", {}) or {}).get("results", []) or []
    except Exception:
        return []

    out: list[dict] = []
    seen: set[str] = set()
    for item in results:
        url = (item.get("url") or "").split("?")[0].rstrip("/")
        if "linkedin.com/in/" not in url or url in seen:
            continue
        seen.add(url)
        # Brave's title is usually "Name - Title - Company | LinkedIn"; description backs it up.
        name, title, company = _parse_linkedin_title(_strip_tags(item.get("title") or ""))
        if (not title or not company):
            d_name, d_title, d_company = _parse_linkedin_title(_strip_tags(item.get("description") or ""))
            title = title or d_title
            company = company or d_company
        if not name:
            continue
        first, _, last = name.partition(" ")
        out.append({
            "first_name": first, "last_name": last, "name": name,
            "title": title, "company": company, "domain": "",
            "linkedin_url": url, "location": "", "seniority": "",
            "email": "", "source": "brave",
        })
        if len(out) >= limit:
            break
    return out


# ── DuckDuckGo public LinkedIn fallback (free, no key) ────────────────────────

_DDG_RESULT_RE = re.compile(
    r'<a[^>]+class="result__a"[^>]+href="([^"]+linkedin\.com/in/[^"]+)"[^>]*>(.*?)</a>',
    re.I | re.S,
)
_TAG_RE = re.compile(r"<[^>]+>")


def _strip_tags(s: str) -> str:
    return unescape(_TAG_RE.sub("", s)).strip()


def _parse_linkedin_title(headline: str) -> tuple[str, str, str]:
    """A LinkedIn result title looks like 'Jane Doe - VP Sales - Acme Corp | LinkedIn'.
    Returns (name, title, company)."""
    head = re.split(r"\|\s*LinkedIn", headline, flags=re.I)[0].strip()
    parts = [p.strip() for p in head.split(" - ") if p.strip()]
    name = parts[0] if parts else head
    title = parts[1] if len(parts) > 1 else ""
    company = parts[2] if len(parts) > 2 else ""
    return name, title, company


async def _duckduckgo_people(filters: dict, limit: int) -> list[dict]:
    terms = " ".join(filter(None, [
        filters.get("titles") or filters.get("seniority") or "",
        filters.get("industry") or "",
        filters.get("keywords") or "",
        filters.get("location") or "",
        filters.get("query") or "",
    ])).strip()
    query = f'site:linkedin.com/in {terms}'.strip()
    try:
        async with httpx.AsyncClient(timeout=12.0, follow_redirects=True) as client:
            r = await client.post(
                "https://html.duckduckgo.com/html/",
                data={"q": query},
                headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"},
            )
        if r.status_code != 200:
            return []
        html = r.text
    except Exception:
        return []

    out: list[dict] = []
    seen: set[str] = set()
    for href, raw_title in _DDG_RESULT_RE.findall(html):
        url = href.split("?")[0].rstrip("/")
        if url in seen:
            continue
        seen.add(url)
        name, title, company = _parse_linkedin_title(_strip_tags(raw_title))
        if not name:
            continue
        first, _, last = name.partition(" ")
        out.append({
            "first_name": first, "last_name": last, "name": name,
            "title": title, "company": company, "domain": "",
            "linkedin_url": url, "location": "", "seniority": "",
            "email": "", "source": "duckduckgo",
        })
        if len(out) >= limit:
            break
    return out


# ── Orchestrator ──────────────────────────────────────────────────────────────

def _to_contact(tenant_id: str, person: dict) -> dict:
    return {
        "lead_id": str(uuid.uuid4()),
        "tenant_id": tenant_id,
        "name": person.get("name") or _full_name(person.get("first_name", ""), person.get("last_name", "")),
        "email": person.get("email") or "",
        "company": person.get("company") or person.get("domain") or "",
        "title": person.get("title") or "",
        "phone": person.get("phone") or "",
        "linkedin_url": person.get("linkedin_url") or "",
        "location": person.get("location") or "",
        "email_verified": bool(person.get("email_verified")),
        "enrichment_source": person.get("source") or "",
        "global_status": "prospecting",
        "channel_state": {"email": "idle", "sms": "idle", "linkedin": "idle", "voice": "idle"},
        "intent_signals": [],
    }


async def discover_people(
    tenant_id: str,
    filters: dict,
    enrichment_service,
    limit: int = 25,
    max_parallel: int = 5,
) -> list[dict]:
    """
    Find top-level people matching the filter set, then reveal + verify their email
    via the enrichment waterfall.

    `filters` keys (all optional): titles, seniority, department, location, domain,
    industry, keywords, employeeSize, query (raw natural-language box).
    `enrichment_service` is an EnrichmentService instance (its waterfall reveals emails).
    """
    # Source priority:
    #   1. Apollo people search (best data; paywalled on free plans → []),
    #   2. Brave Search public-LinkedIn sourcing (free 2k/mo when keyed),
    #   3. company-sweep (discover companies → named execs via Prospeo/Hunter),
    #   4. DuckDuckGo public LinkedIn (no key, best-effort).
    people = await _apollo_people(filters, limit)
    if not people:
        people = await _brave_people(filters, limit)
    if not people:
        people = await _company_sweep_people(filters, limit)
    if not people:
        people = await _duckduckgo_people(filters, limit)
    if not people:
        return []

    sem = asyncio.Semaphore(max_parallel)

    async def _finish(person: dict) -> dict:
        # Already has a real email from the discovery source — keep it.
        if person.get("email"):
            if "email_verified" not in person:
                person["email_verified"] = person.get("source") == "apollo"
            return _to_contact(tenant_id, person)

        # Resolve a domain from the company name when discovery didn't supply one
        # (Brave/DuckDuckGo give a company name, not a domain) so the waterfall can fire.
        if not person.get("domain") and person.get("company"):
            try:
                from modules.m1_intelligence.contact_discover import _guess_domain_from_name
                async with sem:
                    guessed = await _guess_domain_from_name(person["company"])
                if guessed:
                    person["domain"] = guessed
            except Exception:
                pass

        # No email yet — run the enrichment waterfall on name + domain.
        if person.get("domain") and (person.get("first_name") or person.get("last_name")):
            async with sem:
                try:
                    enriched = await enrichment_service.enrich_contact(
                        tenant_id=tenant_id,
                        first_name=person.get("first_name") or None,
                        last_name=person.get("last_name") or None,
                        domain=person["domain"],
                        title=person.get("title") or None,
                    )
                except Exception:
                    enriched = None
            if enriched:
                # Keep the richer discovery metadata, layer in the revealed email.
                enriched["linkedin_url"] = person.get("linkedin_url") or enriched.get("linkedin_url", "")
                enriched["location"] = person.get("location") or ""
                if person.get("company"):
                    enriched["company"] = person["company"]
                if person.get("title"):
                    enriched["title"] = person["title"]
                enriched["enrichment_source"] = f"{person['source']}+{enriched.get('enrichment_source', '')}".rstrip("+")
                return enriched

        # No email could be found — still return the person (LinkedIn lead with no email yet).
        return _to_contact(tenant_id, person)

    contacts = list(await asyncio.gather(*[_finish(p) for p in people]))

    # Cache anything that ended up with an email.
    emailed = [c for c in contacts if c.get("email")]
    if emailed:
        try:
            enrichment_service._cache_many(emailed)  # type: ignore[attr-defined]
        except Exception:
            pass

    return contacts
