"""Dabblin's existing website videos, shared by outreach and follow-ups."""
from html import escape
from urllib.parse import urlencode
import re

# IDs match dabblin.com WhoWeServeShowcase and its public asset filenames.
VIDEOS = {
    'barbershops': ('Barbershops', ('barber', 'barbershop'), 'booking haircuts while your team is with clients'),
    'restaurants': ('Restaurants', ('restaurant', 'dining'), 'handling reservation calls during service'),
    'law_offices': ('Law Offices', ('law office', 'law firm', 'legal', 'attorney', 'lawyer'), 'capturing intake requests while your team is in consultations'),
    'dental_offices': ('Dental Offices', ('dental', 'dentist'), 'handling appointment requests while your team cares for patients'),
    'gyms_fitness': ('Gyms & Fitness', ('gym', 'fitness'), 'answering membership questions while your team coaches'),
    'pet_services': ('Pet Services', ('pet', 'groomer', 'grooming'), 'capturing grooming appointments while your hands are full'),
    'nail_salons': ('Nail Salons', ('nail', 'manicure', 'pedicure'), 'booking appointments while your technicians are with clients'),
    'florists': ('Florists', ('florist', 'floral', 'flower'), 'capturing order inquiries while you prepare arrangements'),
    'childcare': ('Childcare', ('childcare', 'child care', 'daycare', 'day care'), 'answering enrollment questions while your team cares for children'),
    'cleaning_services': ('Cleaning Services', ('cleaning', 'cleaner', 'janitorial'), 'capturing quote requests while your teams are on site'),
    'auto_repair': ('Auto Repair', ('auto repair', 'mechanic', 'automotive'), 'booking service requests while your team works in the bays'),
    'med_spas': ('Med Spas', ('med spa', 'medical spa', 'aesthetic'), 'capturing consultation requests while your team is with clients'),
}


def resolve_sector(*values: str) -> str:
    for value in values:
        if value in VIDEOS:
            return value
        text = re.sub(r'[_-]+', ' ', (value or '').lower())
        matches = [key for key, (_, aliases, _) in VIDEOS.items()
                   if any(re.search(r'\b' + re.escape(alias) + r'\w*\b', text) for alias in aliases)]
        if len(matches) == 1:
            return matches[0]
        if len(matches) > 1:
            return ''  # ambiguous businesses receive a general demo, never an invented match
    return ''


def video_url(sector: str, campaign: str = 'autopilot') -> str:
    query = urlencode({'utm_source': 'urap', 'utm_medium': 'email',
                       'utm_campaign': campaign, 'utm_content': f'video_{sector}' if sector else 'demo_cta'})
    if sector in VIDEOS:
        return f'https://dabblin.com/?industry={sector}&{query}#industry-videos'
    return f'https://dabblin.com/demo/?{query}'


def video_card(sector: str, campaign: str = 'autopilot') -> str:
    url = escape(video_url(sector, campaign), quote=True)
    if sector not in VIDEOS:
        return f'<p><a href="{url}">Hear how the AI handles an incoming call</a></p>'
    label = escape(VIDEOS[sector][0])
    return (f'<p><a href="{url}" style="display:inline-block;color:#2563eb;text-decoration:none;">'
            f'<img src="https://dabblin.com/thumbnails/{sector}.jpg" width="240" '
            f'alt="Watch the {label} video on dabblin.com" '
            'style="display:block;width:240px;max-width:100%;height:auto;border:0;border-radius:12px;">'
            f'<span style="display:block;padding-top:10px;font-weight:bold;">&#9654; Watch: {label}</span>'
            '</a></p>')


def followup_copy(company: str, sector: str, step: int) -> tuple[str, str]:
    business = company or 'your business'
    focus = VIDEOS.get(sector, ('', (), 'answering customer calls while your team is busy'))[2]
    if step == 0:
        subject = f'How would this fit {business}?'
        body = (f'<p>Following up on the example I sent for {escape(business)}.</p>'
                f'<p>For your team, the useful starting point is {focus}. '
                'We can tailor the greeting, common questions, and handoff to your existing process.</p>'
                '<p>Which is the bigger challenge for you: calls during busy hours, or after closing? '
                'Reply and I can suggest a starting point.</p>')
    else:
        subject = f'A next step for {business}'
        body = (f'<p>One last follow-up for {escape(business)}.</p>'
                f'<p>If {focus} would help, reply with the call you most often miss. '
                'We can walk through what the receptionist would say and when it should hand off to you.</p>'
                '<p>Would a short walkthrough be useful? If the timing is off, no problem — '
                'I will leave it here.</p>')
    return subject, body
