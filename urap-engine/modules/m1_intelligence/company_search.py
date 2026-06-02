"""
Company search — two modes:
  1. Domain enrichment: domain provided → Hunter.io + Snov.io waterfall (rich metadata for 1 co.)
  2. Discovery search:  keywords/location/industry → Google Places + Yelp + Foursquare in parallel
"""
from __future__ import annotations
import asyncio, os, re
import httpx

HUNTER_API_KEY        = os.getenv("HUNTER_API_KEY", "")
SNOV_CLIENT_ID        = os.getenv("SNOV_CLIENT_ID", "")
SNOV_CLIENT_SECRET    = os.getenv("SNOV_CLIENT_SECRET", "")
APOLLO_API_KEY        = os.getenv("APOLLO_API_KEY", "")
GOOGLE_PLACES_API_KEY = os.getenv("GOOGLE_PLACES_API_KEY", "")
YELP_API_KEY          = os.getenv("YELP_API_KEY", "")
FOURSQUARE_API_KEY    = os.getenv("FOURSQUARE_API_KEY", "")

_DOMAIN_RE = re.compile(r"[\w-]+\.(com|io|ai|co|net|org|app|us|tech|dev)", re.I)


def _name_to_domain(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]", "", name.lower())
    return f"{slug}.com" if slug else ""


# ── Apollo.io — discovery search ─────────────────────────────────────────────

async def _apollo_search(
    keywords: str = "",
    location: str = "",
    industry: str = "",
    name:     str = "",
    limit:    int = 25,
) -> list[dict]:
    if not APOLLO_API_KEY:
        return []

    payload: dict = {
        "per_page": min(limit, 100),
        "page":     1,
    }
    if keywords:
        payload["q_keywords"] = keywords
    if name:
        payload["q_organization_name"] = name
    if location:
        payload["organization_locations"] = [location]
    if industry:
        payload["organization_industries"] = [industry.lower()]

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            r = await client.post(
                "https://api.apollo.io/v1/mixed_companies/search",
                json=payload,
                headers={"Content-Type": "application/json", "Cache-Control": "no-cache", "X-Api-Key": APOLLO_API_KEY},
            )
        if r.status_code != 200:
            return []

        results = []
        for o in r.json().get("organizations", []):
            city    = o.get("city")    or ""
            state   = o.get("state")   or ""
            country = o.get("country") or ""
            loc     = ", ".join(filter(None, [city, state, country]))

            phone = ""
            pp = o.get("primary_phone")
            if isinstance(pp, dict):
                phone = pp.get("number") or pp.get("sanitized_number") or ""

            techs = o.get("technologies") or []
            tech_names = [
                t if isinstance(t, str) else (t.get("name") or "")
                for t in techs
            ]

            results.append({
                "name":          o.get("name") or "",
                "domain":        o.get("primary_domain") or "",
                "website":       o.get("website_url") or "",
                "industry":      o.get("industry") or "",
                "description":   o.get("short_description") or "",
                "location":      loc,
                "headcount":     str(o.get("estimated_num_employees") or ""),
                "company_type":  o.get("organization_type") or "",
                "technologies":  [t for t in tech_names if t],
                "email_pattern": "",
                "contact_count": o.get("total_employee_count") or 0,
                "linkedin":      o.get("linkedin_url") or "",
                "phone":         phone,
                "source":        "apollo",
            })
        return results
    except Exception:
        return []


# ── Google Places — local/SMB discovery search ───────────────────────────────

async def _google_places_search(
    keywords: str = "",
    location: str = "",
    limit:    int = 25,
) -> list[dict]:
    if not GOOGLE_PLACES_API_KEY:
        return []

    kw_s, loc_s = keywords.strip(), location.strip()
    if kw_s and loc_s:
        query = f"{kw_s} in {loc_s}"
    elif loc_s:
        query = loc_s
    else:
        query = kw_s
    fields = ",".join([
        "places.displayName",
        "places.formattedAddress",
        "places.nationalPhoneNumber",
        "places.websiteUri",
        "places.types",
        "places.businessStatus",
        "places.rating",
        "places.userRatingCount",
    ])

    try:
        async with httpx.AsyncClient(timeout=12.0) as client:
            r = await client.post(
                "https://places.googleapis.com/v1/places:searchText",
                json={"textQuery": query, "maxResultCount": min(limit, 20)},
                headers={
                    "Content-Type":    "application/json",
                    "X-Goog-Api-Key":  GOOGLE_PLACES_API_KEY,
                    "X-Goog-FieldMask": fields,
                },
            )
        if r.status_code != 200:
            return []

        results = []
        for p in r.json().get("places", []):
            name    = p.get("displayName", {}).get("text", "") or ""
            address = p.get("formattedAddress", "") or ""
            phone   = p.get("nationalPhoneNumber", "") or ""
            website = p.get("websiteUri", "") or ""
            status  = p.get("businessStatus", "") or ""

            # Extract domain from website URI
            domain = ""
            if website:
                m = _DOMAIN_RE.search(website)
                if m:
                    domain = m.group(0).lower()

            # Derive city/state from formatted address (last two comma-parts before zip)
            addr_parts = [a.strip() for a in address.split(",")]
            loc_str = ", ".join(addr_parts[1:3]) if len(addr_parts) >= 3 else address

            # Map Google place types to a readable industry label
            types = p.get("types", []) or []
            industry = _places_industry(types)

            if status and status != "OPERATIONAL":
                continue

            results.append({
                "name":          name,
                "domain":        domain,
                "website":       website,
                "industry":      industry,
                "description":   address,
                "location":      loc_str,
                "headcount":     "",
                "company_type":  "local_business",
                "technologies":  [],
                "email_pattern": "",
                "contact_count": 0,
                "linkedin":      "",
                "phone":         phone,
                "source":        "google_places",
            })
        return results
    except Exception:
        return []


def _places_industry(types: list[str]) -> str:
    mapping = {
        "hair_care":       "Personal Care & Beauty",
        "beauty_salon":    "Personal Care & Beauty",
        "barber_shop":     "Personal Care & Beauty",
        "restaurant":      "Food & Beverage",
        "food":            "Food & Beverage",
        "gym":             "Health & Fitness",
        "health":          "Healthcare",
        "lawyer":          "Legal Services",
        "real_estate":     "Real Estate",
        "finance":         "Financial Services",
        "lodging":         "Hospitality",
        "store":           "Retail",
        "car_repair":      "Automotive",
        "dentist":         "Healthcare",
        "doctor":          "Healthcare",
        "school":          "Education",
        "church":          "Religious Organization",
    }
    for t in types:
        if t in mapping:
            return mapping[t]
    return "Local Business"


# ── Yelp Fusion — local/SMB discovery search ─────────────────────────────────

async def _yelp_search(
    keywords: str = "",
    location: str = "",
    limit:    int = 25,
) -> list[dict]:
    if not YELP_API_KEY:
        return []

    try:
        async with httpx.AsyncClient(timeout=12.0) as client:
            r = await client.get(
                "https://api.yelp.com/v3/businesses/search",
                params={
                    "term":     keywords,
                    "location": location or "United States",
                    "limit":    min(limit, 50),
                },
                headers={"Authorization": f"Bearer {YELP_API_KEY}"},
            )
        if r.status_code != 200:
            return []

        results = []
        for b in r.json().get("businesses", []):
            if b.get("is_closed"):
                continue

            loc_dict = b.get("location", {})
            city  = loc_dict.get("city", "")
            state = loc_dict.get("state", "")
            loc_str = ", ".join(filter(None, [city, state]))

            phone    = b.get("phone", "") or ""
            cats     = b.get("categories", []) or []
            industry = cats[0].get("title", "Local Business") if cats else "Local Business"
            yelp_id  = b.get("id", "") or ""

            results.append({
                "name":          b.get("name", ""),
                "domain":        "",
                "website":       "",
                "yelp_id":       yelp_id,
                "industry":      industry,
                "description":   loc_dict.get("address1", ""),
                "location":      loc_str,
                "headcount":     "",
                "company_type":  "local_business",
                "technologies":  [],
                "email_pattern": "",
                "contact_count": b.get("review_count", 0),
                "linkedin":      "",
                "phone":         phone,
                "source":        "yelp",
            })

        # Yelp's free API tier ignores the location param and returns SF-area results.
        # Always filter: drop any result whose city/state doesn't contain a significant
        # token from the requested location (e.g. "york" won't appear in "San Francisco, CA").
        if location.strip() and results:
            sig_tokens = [t for t in re.split(r"[\s,]+", location.lower()) if len(t) >= 4]
            if sig_tokens:
                results = [r for r in results if any(t in r["location"].lower() for t in sig_tokens)]

        return results
    except Exception:
        return []


# ── Foursquare Places — local/SMB discovery search ───────────────────────────

async def _foursquare_search(
    keywords: str = "",
    location: str = "",
    limit:    int = 25,
) -> list[dict]:
    if not FOURSQUARE_API_KEY:
        return []

    try:
        async with httpx.AsyncClient(timeout=12.0) as client:
            r = await client.get(
                "https://api.foursquare.com/v3/places/search",
                params={
                    "query": keywords,
                    "near":  location or "",
                    "limit": min(limit, 50),
                    "fields": "name,location,tel,website,categories",
                },
                headers={"Authorization": FOURSQUARE_API_KEY},
            )
        if r.status_code != 200:
            return []

        results = []
        for p in r.json().get("results", []):
            loc_dict = p.get("location", {})
            city  = loc_dict.get("locality", "")
            state = loc_dict.get("region", "")
            loc_str = ", ".join(filter(None, [city, state]))

            phone   = p.get("tel", "") or ""
            website = p.get("website", "") or ""
            cats    = p.get("categories", []) or []
            industry = cats[0].get("name", "Local Business") if cats else "Local Business"

            domain = ""
            if website:
                m = _DOMAIN_RE.search(website)
                if m:
                    domain = m.group(0).lower()

            results.append({
                "name":          p.get("name", ""),
                "domain":        domain,
                "website":       website,
                "industry":      industry,
                "description":   loc_dict.get("formatted_address", ""),
                "location":      loc_str,
                "headcount":     "",
                "company_type":  "local_business",
                "technologies":  [],
                "email_pattern": "",
                "contact_count": 0,
                "linkedin":      "",
                "phone":         phone,
                "source":        "foursquare",
            })
        return results
    except Exception:
        return []


def _dedup_results(lists: list[list[dict]]) -> list[dict]:
    """Merge results from multiple sources, dedup by phone or name+location."""
    seen: set[str] = set()
    merged = []
    for result_list in lists:
        for r in result_list:
            # Normalize phone to 10 digits
            raw_phone = re.sub(r"\D", "", r.get("phone", ""))
            phone_key = raw_phone[-10:] if len(raw_phone) >= 10 else ""

            # Normalize name for fuzzy dedup
            name_key = re.sub(r"[^a-z0-9]", "", r.get("name", "").lower())[:20]
            loc_key  = re.sub(r"[^a-z0-9]", "", r.get("location", "").lower())[:10]

            fingerprint = phone_key if phone_key else f"{name_key}_{loc_key}"
            if not fingerprint or fingerprint in seen:
                continue
            seen.add(fingerprint)
            merged.append(r)
    return merged


# ── Hunter.io — domain enrichment ────────────────────────────────────────────

async def _hunter_domain(domain: str) -> dict | None:
    if not HUNTER_API_KEY:
        return None
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.get(
                "https://api.hunter.io/v2/domain-search",
                params={"domain": domain, "api_key": HUNTER_API_KEY, "limit": 1},
            )
        if r.status_code != 200:
            return None
        d    = r.json().get("data", {})
        meta = r.json().get("meta", {})
        loc  = ", ".join(filter(None, [d.get("city",""), d.get("state",""), d.get("country","")]))
        return {
            "name":          d.get("organization") or domain.split(".")[0].title(),
            "domain":        domain,
            "website":       f"https://{domain}",
            "industry":      d.get("industry") or "",
            "description":   d.get("description") or "",
            "location":      loc,
            "headcount":     str(d.get("headcount") or ""),
            "company_type":  d.get("company_type") or "",
            "technologies":  d.get("technologies") or [],
            "email_pattern": d.get("pattern") or "",
            "contact_count": meta.get("results") or 0,
            "linkedin":      f"linkedin.com/company/{d['linkedin']}" if d.get("linkedin") else "",
            "phone":         "",
            "source":        "hunter",
        }
    except Exception:
        return None


# ── Snov.io — domain enrichment fallback ─────────────────────────────────────

_snov_token_cache: dict = {}

async def _snov_token() -> str:
    if _snov_token_cache.get("token"):
        return _snov_token_cache["token"]
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.post(
                "https://api.snov.io/v1/oauth/access_token",
                json={
                    "grant_type":    "client_credentials",
                    "client_id":     SNOV_CLIENT_ID,
                    "client_secret": SNOV_CLIENT_SECRET,
                },
            )
        token = r.json().get("access_token", "") if r.status_code == 200 else ""
        _snov_token_cache["token"] = token
        return token
    except Exception:
        return ""


async def _snov_domain(domain: str) -> dict | None:
    if not SNOV_CLIENT_ID:
        return None
    token = await _snov_token()
    if not token:
        return None
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.post(
                "https://api.snov.io/v2/get-domain-search-results",
                json={"domain": domain, "type": "all", "limit": 1},
                headers={"Authorization": f"Bearer {token}"},
            )
        if r.status_code != 200:
            return None
        data = r.json().get("data", {})
        return {
            "name":          data.get("companyName") or domain.split(".")[0].title(),
            "domain":        domain,
            "website":       f"https://{domain}",
            "industry":      data.get("industry") or "",
            "description":   "",
            "location":      data.get("locality") or "",
            "headcount":     str(data.get("size") or ""),
            "company_type":  "",
            "technologies":  [],
            "email_pattern": "",
            "contact_count": data.get("total") or 0,
            "linkedin":      data.get("linkedinUrl") or "",
            "phone":         "",
            "source":        "snov",
        }
    except Exception:
        return None


# ── Public API ────────────────────────────────────────────────────────────────

async def search_companies(
    domain:   str = "",
    name:     str = "",
    keywords: str = "",
    location: str = "",
    industry: str = "",
    limit:    int = 25,
) -> list[dict]:
    """
    Two modes:
    - domain provided  → Hunter.io enrichment + Snov.io fallback (single company, rich metadata)
    - keywords/location/industry → Apollo.io discovery (list of matching companies)
    """
    # ── Mode 1: domain enrichment ──────────────────────────────────────────────
    if domain.strip():
        target = domain.strip().lower()
        result = await _hunter_domain(target)
        if result:
            return [result]
        result = await _snov_domain(target)
        if result:
            return [result]
        return [{
            "name":          name or target.split(".")[0].title(),
            "domain":        target,
            "website":       f"https://{target}",
            "industry":      "",
            "description":   "No enrichment data found for this domain.",
            "location":      "",
            "headcount":     "",
            "company_type":  "",
            "technologies":  [],
            "email_pattern": "",
            "contact_count": 0,
            "linkedin":      "",
            "phone":         "",
            "source":        "placeholder",
        }]

    # ── Mode 2: discovery search ───────────────────────────────────────────────
    if keywords or location or industry or name:
        kw = keywords or name
        # When only industry is set (no keywords), use industry as the search term so
        # local providers (Yelp/Google/FSQ) get a non-empty term and respect the location.
        local_kw = kw or industry

        # Run all free local sources in parallel
        google_task = _google_places_search(keywords=local_kw, location=location, limit=limit) \
            if GOOGLE_PLACES_API_KEY and (local_kw or location) else asyncio.sleep(0, result=[])
        yelp_task = _yelp_search(keywords=local_kw, location=location, limit=limit) \
            if YELP_API_KEY and (local_kw or location) else asyncio.sleep(0, result=[])
        fsq_task = _foursquare_search(keywords=local_kw, location=location, limit=limit) \
            if FOURSQUARE_API_KEY and (local_kw or location) else asyncio.sleep(0, result=[])

        google_res, yelp_res, fsq_res = await asyncio.gather(
            google_task, yelp_task, fsq_task
        )

        # Merge with dedup — Google Places first (richest data), then Yelp, then Foursquare
        merged = _dedup_results([google_res, yelp_res, fsq_res])
        if merged:
            return merged

        # Apollo: B2B corporate search (requires paid plan)
        if APOLLO_API_KEY:
            results = await _apollo_search(
                keywords=keywords,
                location=location,
                industry=industry,
                name=name,
                limit=limit,
            )
            if results:
                return results

    return []
