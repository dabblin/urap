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

# Role addresses a business actually reads, best first. Preferred over a random
# personal address picked up from a page footer.
_ROLE_PREFIXES = [
    "info", "contact", "hello", "office", "admin", "reception", "frontdesk",
    "front.desk", "appointments", "booking", "bookings", "inquiries",
    "enquiries", "sales", "team", "mail", "help", "support",
]

# Pages worth trying when a site doesn't link its contact page from the homepage.
_CONTACT_PATHS = [
    "", "/contact", "/contact-us", "/contact.html", "/contactus",
    "/about", "/about-us", "/get-in-touch", "/appointments", "/book",
]

_MAILTO_RE  = re.compile(r'mailto:([a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,})', re.I)
_CFEMAIL_RE = re.compile(r'data-cfemail=["\']([0-9a-fA-F]+)["\']')
_LINK_RE    = re.compile(r'href=["\']([^"\']+)["\']', re.I)
_CONTACT_LINK_RE = re.compile(r'(contact|about|appointment|book|get-in-touch|reach-us)', re.I)


def _decode_cfemail(hex_str: str) -> str:
    """Cloudflare obfuscates addresses as hex XORed with the first byte. Without
    this the page only yields the literal '[email protected]' placeholder, which
    is why so many scrapes came back empty."""
    try:
        key = int(hex_str[:2], 16)
        return "".join(
            chr(int(hex_str[i:i + 2], 16) ^ key)
            for i in range(2, len(hex_str), 2)
        )
    except Exception:
        return ""


# Small businesses very often publish a free-mail address as their real contact.
# It scores below an on-domain address but is still a legitimate lead.
_FREE_MAIL = {
    "gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "aol.com",
    "icloud.com", "msn.com", "live.com", "comcast.net", "verizon.net",
    "sbcglobal.net", "att.net", "me.com", "mac.com", "protonmail.com",
}

# Dummy addresses baked into templates — never a real lead.
_PLACEHOLDER_LOCALS = {
    "your", "youremail", "yourname", "email", "name", "username", "user",
    "someone", "firstname", "lastname", "domain", "address", "mail",
    "example", "sample", "abc", "xyz", "john.doe", "janedoe", "johndoe",
}


def _email_ok(addr: str) -> bool:
    low = addr.lower()
    if any(s in low for s in _SKIP_PATTERNS):
        return False
    local_part = low.partition("@")[0]
    if local_part in _PLACEHOLDER_LOCALS:
        return False
    if low.count("@") != 1:
        return False
    local, _, host = low.partition("@")
    if not local or "." not in host or len(host) < 4:
        return False
    # Strip things that look like filenames or hashes rather than addresses
    if len(local) > 40 or re.fullmatch(r"[0-9a-f]{16,}", local):
        return False
    return True


def _score_email(addr: str, site_domain: str) -> int:
    """Higher is better. Same-domain beats off-domain; a role address beats a
    personal one, so outreach lands in the inbox somebody actually monitors."""
    low = addr.lower()
    local, _, host = low.partition("@")
    score = 0
    if site_domain and (host == site_domain or host.endswith("." + site_domain)):
        score += 100
    elif host in _FREE_MAIL:
        score += 20  # a real small-business inbox, just not on their own domain
    for i, pref in enumerate(_ROLE_PREFIXES):
        if local == pref or local.startswith(pref + "."):
            score += 50 - i
            break
    return score


def _emails_from_html(html: str) -> list[str]:
    found: list[str] = []
    found.extend(_MAILTO_RE.findall(html))
    for hexed in _CFEMAIL_RE.findall(html):
        dec = _decode_cfemail(hexed)
        if dec:
            found.append(dec)
    found.extend(_EMAIL_RE.findall(html))
    out, seen = [], set()
    for e in found:
        low = e.lower().strip(".,;:)")
        if low not in seen and _email_ok(low):
            seen.add(low)
            out.append(low)
    return out

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
    """Pull the best contact address off a business website.

    Fetches the homepage, follows the contact/about links it actually advertises
    (falling back to common guesses), reads mailto: links and Cloudflare-obfuscated
    addresses as well as plain text, then ranks candidates so a monitored role
    inbox on the company's own domain wins over a stray address in a footer.
    """
    if not url or _is_listing(url):
        return ""
    if not url.startswith("http"):
        url = f"https://{url}"
    base = url.rstrip("/")

    m = re.search(r"https?://([^/]+)", base)
    site_domain = (m.group(1).lower().replace("www.", "") if m else "")

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
    }
    # Some sites' bot rules reject the full Chrome UA above but serve this shorter
    # one, so a block is retried rather than written off as "no email".
    fallback_headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
    }
    candidates: list[str] = []

    async with httpx.AsyncClient(timeout=8.0, follow_redirects=True) as client:

        async def fetch(page: str) -> str:
            try:
                r = await client.get(page, headers=headers)
                if r.status_code in (403, 406, 429):
                    r = await client.get(page, headers=fallback_headers)
                ct = r.headers.get("content-type", "")
                if r.status_code != 200 or "html" not in ct.lower():
                    return ""
                # Site builders (Wix, Squarespace) routinely emit >1MB of markup
                # with the contact address near the end — truncating too early
                # silently loses it.
                return r.text[:3_000_000]
            except Exception:
                return ""

        home = await fetch(base)
        if home:
            candidates.extend(_emails_from_html(home))

            # Prefer the contact pages the site actually links to; guessed paths
            # miss anything that isn't named conventionally.
            linked: list[str] = []
            for href in _LINK_RE.findall(home):
                if not _CONTACT_LINK_RE.search(href):
                    continue
                if href.startswith("#") or href.lower().startswith("mailto:"):
                    continue
                if href.startswith("http"):
                    if site_domain and site_domain not in href:
                        continue
                    full = href
                else:
                    full = base + "/" + href.lstrip("/")
                if full not in linked:
                    linked.append(full)
                if len(linked) >= 4:
                    break

            pages = linked + [base + p for p in _CONTACT_PATHS if p]
            seen_pages, to_fetch = set(), []
            for p in pages:
                key = p.rstrip("/")
                if key not in seen_pages:
                    seen_pages.add(key)
                    to_fetch.append(p)
                if len(to_fetch) >= 6:
                    break

            for html in await asyncio.gather(*[fetch(p) for p in to_fetch]):
                if html:
                    candidates.extend(_emails_from_html(html))

    if not candidates:
        return ""

    uniq = list(dict.fromkeys(candidates))
    best = max(uniq, key=lambda e: _score_email(e, site_domain))
    # An off-domain address with no role prefix is usually a vendor or a plugin
    # author scraped out of the markup, not the business — don't email it.
    return best if _score_email(best, site_domain) > 0 else ""


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
