"""
Contact discovery — two strategies in priority order:
  1. Hunter.io domain search  — high-quality, B2B, 50 req/month free
  2. Website email scrape     — works for local businesses with real websites
"""
from __future__ import annotations
import asyncio, os, re
import httpx

HUNTER_API_KEY = os.getenv("HUNTER_API_KEY", "")
YELP_API_KEY   = os.getenv("YELP_API_KEY", "")

_EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", re.I)

_SKIP_PATTERNS = [
    "example.", "test@", "noreply", "no-reply", "wordpress", "wixpress",
    "schema.org", "sentry.io", "squarespace", "shopify", "emailprotected",
    "@2x", ".png", ".jpg", ".gif", ".svg", ".webp",
]

_LISTING_DOMAINS = {
    "yelp.com", "foursquare.com", "facebook.com", "instagram.com",
    "twitter.com", "linkedin.com", "tripadvisor.com", "yellowpages.com",
    "bing.com", "google.com", "mapquest.com",
}

_PRIORITY_TITLES = ["owner", "founder", "ceo", "president", "manager", "director"]

_SOCIAL_RE = {
    "linkedin":  re.compile(r'https?://(?:www\.)?linkedin\.com/company/[A-Za-z0-9\-_%]+', re.I),
    "instagram": re.compile(r'https?://(?:www\.)?instagram\.com/[A-Za-z0-9_.]+', re.I),
    "twitter":   re.compile(
        r'https?://(?:www\.)?(?:twitter|x)\.com/(?!share|intent|search|login|signup|home|settings|notifications|messages|i/|oauth)[A-Za-z0-9_]+',
        re.I,
    ),
    "youtube":   re.compile(r'https?://(?:www\.)?youtube\.com/(?:channel/[A-Za-z0-9_\-]+|@[A-Za-z0-9_\-]+)', re.I),
}


async def _scrape_socials(url: str) -> dict:
    """Scrape the homepage for social media profile links."""
    out = {"linkedin": "", "instagram": "", "twitter": "", "youtube": ""}
    if not url or _is_listing(url):
        return out
    if not url.startswith("http"):
        url = f"https://{url}"
    headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}
    try:
        async with httpx.AsyncClient(timeout=6.0, follow_redirects=True) as client:
            r = await client.get(url, headers=headers)
            if r.status_code == 200:
                html = r.text
                for platform, pattern in _SOCIAL_RE.items():
                    m = pattern.search(html)
                    if m:
                        out[platform] = m.group(0).split("?")[0].rstrip("/")
    except Exception:
        pass
    return out


async def _yelp_website(yelp_id: str) -> str:
    """Fetch the real business website URL from Yelp's details endpoint."""
    if not yelp_id or not YELP_API_KEY:
        return ""
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            r = await client.get(
                f"https://api.yelp.com/v3/businesses/{yelp_id}",
                headers={"Authorization": f"Bearer {YELP_API_KEY}"},
            )
        if r.status_code == 200:
            return r.json().get("website", "") or ""
    except Exception:
        pass
    return ""


_BUSINESS_SUFFIXES = re.compile(
    r"\b(law|legal|attorney|attorneys|lawyer|lawyers|dental|dentistry|dentist"
    r"|medical|medicine|health|therapy|group|associates|llc|inc|pc|dds|dmd|md"
    r"|esq|office|offices|firm|studio|clinic|center|services|solutions)\b",
    re.I,
)


async def _guess_domain_from_name(name: str) -> str:
    """Try several domain patterns derived from the business name, return first that resolves."""
    if not name:
        return ""

    base = name.lower()
    # Strip punctuation but keep spaces for now
    base_words = re.sub(r"[^a-z0-9\s]", "", base).split()
    if not base_words:
        return ""

    # Pattern set (ordered by likelihood of being the real domain):
    # 1. Full slug
    full = "".join(base_words)
    # 2. Slug without common business-type suffixes
    stripped_words = [w for w in base_words if not _BUSINESS_SUFFIXES.fullmatch(w)]
    short = "".join(stripped_words) if stripped_words else full
    # 3. First two words only
    two = "".join(base_words[:2])
    # 4. First word only (last resort)
    one = base_words[0]

    candidates = []
    for slug in dict.fromkeys([short, full, two, one]):  # deduplicated, order preserved
        if 6 <= len(slug) <= 40:  # min 6 avoids generic single-word hits (law.com, inc.com)
            candidates.append(f"{slug}.com")

    try:
        async with httpx.AsyncClient(timeout=3.0, follow_redirects=True) as client:
            for domain in candidates:
                try:
                    r = await client.head(f"https://{domain}", headers={"User-Agent": "Mozilla/5.0"})
                    if r.status_code < 400:
                        return domain
                except Exception:
                    continue
    except Exception:
        pass
    return ""


def _is_listing(s: str) -> bool:
    lower = s.lower()
    return any(ld in lower for ld in _LISTING_DOMAINS)


async def _hunter_find(domain: str) -> dict:
    if not HUNTER_API_KEY or not domain or _is_listing(domain):
        return {}
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.get(
                "https://api.hunter.io/v2/domain-search",
                params={"domain": domain, "api_key": HUNTER_API_KEY, "limit": 5},
            )
        if r.status_code != 200:
            return {}
        emails = r.json().get("data", {}).get("emails", [])
        if not emails:
            return {}
        for e in emails:
            if any(t in (e.get("position") or "").lower() for t in _PRIORITY_TITLES):
                return {
                    "email":      e.get("value", ""),
                    "first_name": e.get("first_name", ""),
                    "last_name":  e.get("last_name", ""),
                    "title":      e.get("position", ""),
                    "confidence": e.get("confidence", 0),
                }
        first = emails[0]
        return {
            "email":      first.get("value", ""),
            "first_name": first.get("first_name", ""),
            "last_name":  first.get("last_name", ""),
            "title":      first.get("position", ""),
            "confidence": first.get("confidence", 0),
        }
    except Exception:
        return {}


async def _scrape_email(url: str) -> str:
    if not url or _is_listing(url):
        return ""
    if not url.startswith("http"):
        url = f"https://{url}"
    base = url.rstrip("/")
    pages = [base, f"{base}/contact", f"{base}/contact-us"]
    headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}
    async with httpx.AsyncClient(timeout=6.0, follow_redirects=True) as client:
        for page in pages:
            try:
                r = await client.get(page, headers=headers)
                if r.status_code != 200:
                    continue
                for email in _EMAIL_RE.findall(r.text):
                    lower = email.lower()
                    if any(s in lower for s in _SKIP_PATTERNS):
                        continue
                    parts = lower.split("@")
                    if len(parts) != 2 or "." not in parts[1]:
                        continue
                    return email
            except Exception:
                continue
    return ""


async def discover_contact(
    name:     str = "",
    domain:   str = "",
    website:  str = "",
    phone:    str = "",
    yelp_id:  str = "",
) -> dict:
    """
    Discover contact info for a single business.
    Returns: { email, first_name, last_name, title, confidence, source, phone }
    """
    # For Yelp results: try to resolve the real business website.
    # Strategy 1: Yelp details API (reliable when filled in, ~40% of listings)
    # Strategy 2: guess <slug>.com from business name (catches the rest)
    if yelp_id and not domain and not website:
        real_site = await _yelp_website(yelp_id)
        if real_site and not _is_listing(real_site):
            website = real_site
            m = re.search(r"[\w-]+\.[a-z]{2,}", real_site)
            if m:
                domain = m.group(0).lower()
        if not domain and name:
            guessed = await _guess_domain_from_name(name)
            if guessed:
                domain  = guessed
                website = f"https://{guessed}"

    # Resolve target URL for scraping (used by both social and email scrapers)
    target = website if (website and not _is_listing(website)) else ""
    if not target and domain and not _is_listing(domain):
        target = f"https://{domain}"

    # 1. Hunter (B2B) + social scraping — run in parallel
    async def _maybe_hunter() -> dict:
        if domain and not _is_listing(domain):
            return await _hunter_find(domain)
        return {}

    hunter_result, socials = await asyncio.gather(
        _maybe_hunter(),
        _scrape_socials(target),
    )

    if hunter_result.get("email"):
        return {**hunter_result, "source": "hunter", "phone": phone, **socials}

    # 2. Website scrape (local businesses — runs after parallel step)
    if target:
        email = await _scrape_email(target)
        if email:
            return {
                "email": email, "first_name": "", "last_name": "",
                "title": "", "confidence": 60, "source": "website_scrape", "phone": phone,
                **socials,
            }

    return {
        "email": "", "first_name": "", "last_name": "",
        "title": "", "confidence": 0, "source": "not_found", "phone": phone,
        **socials,
    }


async def discover_contacts_batch(
    companies:    list[dict],
    max_parallel: int = 5,
) -> list[dict]:
    """Enrich a batch. Each dict needs: index, name, domain, website, phone."""
    sem = asyncio.Semaphore(max_parallel)

    async def _one(c: dict) -> dict:
        async with sem:
            result = await discover_contact(
                name=c.get("name", ""),
                domain=c.get("domain", ""),
                website=c.get("website", ""),
                phone=c.get("phone", ""),
                yelp_id=c.get("yelp_id", ""),
            )
            return {"index": c.get("index", 0), **result}

    return list(await asyncio.gather(*[_one(c) for c in companies]))
