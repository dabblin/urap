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

# Foursquare retired the v3 host in 2025; the current API needs a dated version header.
FSQ_API_VERSION = "2025-06-17"


def _note(diag, provider: str, status: str, detail: str = "", count: int = 0) -> None:
    """Record a provider's outcome so dead API keys surface instead of silently
    degrading the result set to zero."""
    if diag is None:
        return
    diag[provider] = {"status": status, "detail": detail, "count": count}


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
    diag:     dict | None = None,
) -> list[dict]:
    if not APOLLO_API_KEY:
        _note(diag, "apollo", "skipped", "APOLLO_API_KEY not set")
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
            _note(diag, "apollo", "error", f"HTTP {r.status_code}: {r.text[:200]}")
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
        _note(diag, "apollo", "ok", count=len(results))
        return results
    except Exception as exc:
        _note(diag, "apollo", "error", f"{type(exc).__name__}: {exc}")
        return []


# ── Google Places — local/SMB discovery search ───────────────────────────────

async def _google_places_search(
    keywords: str = "",
    location: str = "",
    limit:    int = 25,
    diag:     dict | None = None,
) -> list[dict]:
    if not GOOGLE_PLACES_API_KEY:
        _note(diag, "google_places", "skipped", "GOOGLE_PLACES_API_KEY not set")
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
        "places.location",
        "nextPageToken",
    ])

    def _place_key(p: dict) -> str:
        ph = re.sub(r"\D", "", p.get("nationalPhoneNumber", "") or "")[-10:]
        return ph or (p.get("formattedAddress", "") or "")

    try:
        err: list[str] = []

        async def _walk(client, text: str, rect: tuple | None, want: int) -> list[dict]:
            """searchText returns at most 20 per page and 60 per query. Walk
            nextPageToken until we have `want` or Google runs out."""
            got: list[dict] = []
            page_token = ""
            for _ in range(3):
                body: dict = {"textQuery": text, "maxResultCount": 20}
                if rect:
                    body["locationRestriction"] = {"rectangle": {
                        "low":  {"latitude": rect[0], "longitude": rect[1]},
                        "high": {"latitude": rect[2], "longitude": rect[3]},
                    }}
                if page_token:
                    body["pageToken"] = page_token
                r = await client.post(
                    "https://places.googleapis.com/v1/places:searchText",
                    json=body,
                    headers={
                        "Content-Type":    "application/json",
                        "X-Goog-Api-Key":  GOOGLE_PLACES_API_KEY,
                        "X-Goog-FieldMask": fields,
                    },
                )
                if r.status_code != 200:
                    err.append(f"HTTP {r.status_code}: {r.text[:200]}")
                    break
                payload = r.json()
                got.extend(payload.get("places", []) or [])
                page_token = payload.get("nextPageToken") or ""
                if not page_token or len(got) >= want:
                    break
            return got

        raw_places: list[dict] = []
        seen_keys: set[str] = set()

        def _absorb(places: list[dict]) -> None:
            for p in places:
                k = _place_key(p)
                if not k or k in seen_keys:
                    continue
                seen_keys.add(k)
                raw_places.append(p)

        async with httpx.AsyncClient(timeout=12.0) as client:
            _absorb(await _walk(client, query, None, limit))

            if not raw_places and err:
                _note(diag, "google_places", "error", err[0])
                return []

            # A single text query is capped at 60 results no matter the limit. To go
            # deeper, tile the area the seed results actually cover and re-query each
            # cell — this lifts a dense metro from ~60 to several hundred. The bounding
            # box comes from the results themselves, so it works for any location
            # without the Geocoding API. Only runs when the caller asked for >60.
            pts = [
                (p["location"]["latitude"], p["location"]["longitude"])
                for p in raw_places if p.get("location")
            ]
            if limit > 60 and len(pts) >= 5:
                lo_la, hi_la = min(p[0] for p in pts), max(p[0] for p in pts)
                lo_lo, hi_lo = min(p[1] for p in pts), max(p[1] for p in pts)
                if hi_la > lo_la and hi_lo > lo_lo:
                    n = 3
                    tiles = []
                    for i in range(n):
                        for j in range(n):
                            tiles.append((
                                lo_la + (hi_la - lo_la) * i / n,
                                lo_lo + (hi_lo - lo_lo) * j / n,
                                lo_la + (hi_la - lo_la) * (i + 1) / n,
                                lo_lo + (hi_lo - lo_lo) * (j + 1) / n,
                            ))
                    tile_kw = kw_s or loc_s
                    batches = await asyncio.gather(*[
                        _walk(client, tile_kw, t, 60) for t in tiles
                    ], return_exceptions=True)
                    for b in batches:
                        if isinstance(b, list):
                            _absorb(b)

        results = []
        for p in raw_places:
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
        results = results[:limit]
        _note(diag, "google_places", "ok", count=len(results))
        return results
    except Exception as exc:
        _note(diag, "google_places", "error", f"{type(exc).__name__}: {exc}")
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
    diag:     dict | None = None,
) -> list[dict]:
    if not YELP_API_KEY:
        _note(diag, "yelp", "skipped", "YELP_API_KEY not set")
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
            _note(diag, "yelp", "error", f"HTTP {r.status_code}: {r.text[:200]}")
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

        _note(diag, "yelp", "ok", count=len(results))
        return results
    except Exception as exc:
        _note(diag, "yelp", "error", f"{type(exc).__name__}: {exc}")
        return []


# ── Foursquare Places — local/SMB discovery search ───────────────────────────

async def _foursquare_search(
    keywords: str = "",
    location: str = "",
    limit:    int = 25,
    diag:     dict | None = None,
) -> list[dict]:
    if not FOURSQUARE_API_KEY:
        _note(diag, "foursquare", "skipped", "FOURSQUARE_API_KEY not set")
        return []

    try:
        async with httpx.AsyncClient(timeout=12.0) as client:
            r = await client.get(
                "https://places-api.foursquare.com/places/search",
                params={
                    "query": keywords,
                    "near":  location or "",
                    "limit": min(limit, 50),
                    "fields": "name,location,tel,website,categories",
                },
                headers={
                    "Authorization":        f"Bearer {FOURSQUARE_API_KEY}",
                    "X-Places-Api-Version": FSQ_API_VERSION,
                    "Accept":               "application/json",
                },
            )
        if r.status_code != 200:
            _note(diag, "foursquare", "error", f"HTTP {r.status_code}: {r.text[:200]}")
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
        _note(diag, "foursquare", "ok", count=len(results))
        return results
    except Exception as exc:
        _note(diag, "foursquare", "error", f"{type(exc).__name__}: {exc}")
        return []


_STREET_RE = re.compile(r"^\s*(\d+)\s+([a-z]+)", re.I)


def _street_key(r: dict) -> str:
    """Street number + first street word, e.g. '110 Bergen St (at Rutgers…)' → '110bergen'.
    Stable across providers, which format the rest of the address differently, while
    still separating branches of a chain that share a name."""
    addr = r.get("description", "") or ""
    m = _STREET_RE.match(addr.split(",")[0])
    return f"{m.group(1)}{m.group(2).lower()}" if m else ""


def _dedup_results(lists: list[list[dict]]) -> list[dict]:
    """Merge results from multiple sources.

    A record is a duplicate if EITHER its phone OR its name+address matches one
    already kept. Phone alone was not enough: providers list the same business
    under different numbers (main line vs. department), so identical storefronts
    survived twice and got emailed twice.
    """
    seen: set[str] = set()
    merged = []
    for result_list in lists:
        for r in result_list:
            # Normalize phone to 10 digits
            raw_phone = re.sub(r"\D", "", r.get("phone", ""))
            phone_key = raw_phone[-10:] if len(raw_phone) >= 10 else ""

            # Normalize name; prefer street address over city, so two branches of
            # the same chain in one city stay distinct. Fall back to city (digits
            # stripped — Google says "Bronx, NY 10467", Foursquare "Bronx, NY").
            name_key  = re.sub(r"[^a-z0-9]", "", r.get("name", "").lower())[:20]
            place_key = _street_key(r) or re.sub(r"[^a-z]", "", r.get("location", "").lower())[:10]
            if name_key and place_key:
                ident_key = f"{name_key}_{place_key}"
            else:
                # Corporate records (e.g. Hunter) carry a domain but no phone or
                # address. Without this they match on nothing and get dropped.
                ident_key = f"d:{r.get('domain','').lower()}" if r.get("domain") else ""

            keys = {k for k in (phone_key, ident_key) if k}
            if not keys or (keys & seen):
                continue
            seen |= keys
            merged.append(r)
    return merged


# ── Hunter.io — B2B corporate discovery ──────────────────────────────────────

async def _hunter_discover(
    keywords: str = "",
    location: str = "",
    industry: str = "",
    limit:    int = 25,
    diag:     dict | None = None,
) -> list[dict]:
    """Hunter's /discover finds companies by free-text description. Lower volume
    than the local directories, but every hit comes with a known-email count, so
    these are corporate leads that are actually contactable — the role Apollo was
    meant to fill before it turned out to need a paid plan."""
    if not HUNTER_API_KEY:
        _note(diag, "hunter_discover", "skipped", "HUNTER_API_KEY not set")
        return []

    parts = [p for p in (keywords, industry) if p and p.strip()]
    if location.strip():
        parts.append(f"in {location.strip()}")
    query = " ".join(parts).strip()
    if not query:
        _note(diag, "hunter_discover", "skipped", "no query terms")
        return []

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            # Hunter's free plan rejects any explicit limit other than 100
            # ("pagination_error"), so omit it and slice the page ourselves.
            r = await client.post(
                "https://api.hunter.io/v2/discover",
                params={"api_key": HUNTER_API_KEY},
                json={"query": query},
            )
        if r.status_code != 200:
            _note(diag, "hunter_discover", "error", f"HTTP {r.status_code}: {r.text[:200]}")
            return []

        payload = r.json()
        if payload.get("errors"):
            _note(diag, "hunter_discover", "error", str(payload["errors"])[:200])
            return []

        results = []
        for o in payload.get("data", []) or []:
            dom = (o.get("domain") or "").lower()
            if not dom:
                continue
            results.append({
                "name":          o.get("organization") or dom.split(".")[0].title(),
                "domain":        dom,
                "website":       f"https://{dom}",
                "industry":      industry or "",
                "description":   "",
                "location":      "",
                "headcount":     "",
                "company_type":  "",
                "technologies":  [],
                "email_pattern": "",
                "contact_count": (o.get("emails_count") or {}).get("total") or 0,
                "linkedin":      "",
                "phone":         "",
                "source":        "hunter_discover",
            })
        results = results[:limit]
        _note(diag, "hunter_discover", "ok", count=len(results))
        return results
    except Exception as exc:
        _note(diag, "hunter_discover", "error", f"{type(exc).__name__}: {exc}")
        return []


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
    diag:     dict | None = None,
) -> list[dict]:
    """
    Two modes:
    - domain provided  → Hunter.io enrichment + Snov.io fallback (single company, rich metadata)
    - keywords/location/industry → Apollo.io discovery (list of matching companies)

    Pass `diag` (a dict) to receive per-provider status, so a dead API key shows up
    as an error instead of silently shrinking the result set.
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

        # Run every source in parallel. Apollo used to be a fallback that only fired
        # when the local providers returned nothing — which for a located search was
        # never, so its B2B corporate records were unreachable. It now merges in.
        local_ok = bool(local_kw or location)
        google_task = _google_places_search(keywords=local_kw, location=location, limit=limit, diag=diag) \
            if local_ok else asyncio.sleep(0, result=[])
        yelp_task = _yelp_search(keywords=local_kw, location=location, limit=limit, diag=diag) \
            if local_ok else asyncio.sleep(0, result=[])
        fsq_task = _foursquare_search(keywords=local_kw, location=location, limit=limit, diag=diag) \
            if local_ok else asyncio.sleep(0, result=[])
        apollo_task = _apollo_search(
            keywords=keywords, location=location, industry=industry, name=name,
            limit=limit, diag=diag,
        )
        hunter_task = _hunter_discover(
            keywords=kw, location=location, industry=industry, limit=limit, diag=diag,
        )

        google_res, yelp_res, fsq_res, apollo_res, hunter_res = await asyncio.gather(
            google_task, yelp_task, fsq_task, apollo_task, hunter_task
        )

        # Merge with dedup — richest source first so its record wins a collision:
        # Google Places, then Foursquare (phone + website), Yelp, Apollo, Hunter.
        return _dedup_results(
            [google_res, fsq_res, yelp_res, apollo_res, hunter_res]
        )[:limit]

    return []
