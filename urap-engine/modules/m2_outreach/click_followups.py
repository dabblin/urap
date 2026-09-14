"""Provider-verified website clicks → two durable, reply-aware follow-ups.

Runs inside the existing daily Autopilot cycle. A click is an interest signal,
not proof of a human visit or a video view. No send occurs on event ingestion.
"""
import os
import re
import uuid
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse

import httpx

from modules.m2_outreach.industry_video import resolve_sector, followup_copy


def utcnow():
    return datetime.now(timezone.utc)


def timestamp(value):
    parsed = datetime.fromisoformat(str(value).replace('Z', '+00:00'))
    return parsed.replace(tzinfo=timezone.utc) if parsed.tzinfo is None else parsed


def website_click(event):
    if event.get('event') not in ('click', 'clicks'):
        return False
    try:
        url = urlparse(event.get('link', ''))
        return (url.scheme == 'https' and url.hostname in ('dabblin.com', 'www.dabblin.com')
                and not any(word in url.path.lower() for word in ('unsubscribe', 'opt-out', 'privacy'))
                and not event.get('isBot') and not event.get('is_bot'))
    except ValueError:
        return False


class ClickFollowups:
    def __init__(self, db):
        self.db = db
        self._blocked_contacts = None

    async def events(self, client, **params):
        events = []
        for offset in range(0, 10000, 100):
            resp = await client.get('https://api.brevo.com/v3/smtp/statistics/events',
                                    params={**params, 'limit': 100, 'offset': offset, 'sort': 'asc'},
                                    headers={'api-key': os.environ['BREVO_API_KEY']})
            resp.raise_for_status()
            page = resp.json().get('events', [])
            events.extend(page)
            if len(page) < 100:
                return events
        raise RuntimeError('Brevo event pagination exceeded 10000; follow-ups held')

    def correlate(self, tenant_id, event):
        email = (event.get('email') or '').strip().lower()
        if not re.fullmatch(r'[a-z0-9._%+\-]+@[a-z0-9.\-]+\.[a-z]{2,}', email):
            return None
        tag = event.get('tag') or ''
        tags = event.get('tags') or []
        tags = [tags] if isinstance(tags, str) else tags
        tags = ([tag] if isinstance(tag, str) else tag) + tags
        campaign_ids = [t[9:] for t in tags if isinstance(t, str) and t.startswith('campaign:')]
        message_id = event.get('messageId') or event.get('message-id')
        query = self.db.table('urap_campaign_sends').select('*').eq('tenant_id', tenant_id).eq('status', 'sent')
        if message_id:
            rows = query.eq('message_id', message_id).execute().data or []
            rows = [r for r in rows if r['to_email'].lower() == email]
            if len(rows) == 1:
                return rows[0]
        # Legacy sends predate message-id storage: require campaign, recipient,
        # subject and a single unambiguous row, not an email-only guess.
        for campaign_id in campaign_ids:
            if not re.fullmatch(r'[0-9a-fA-F-]{36}', campaign_id):
                continue
            rows = (self.db.table('urap_campaign_sends').select('*').eq('tenant_id', tenant_id)
                    .eq('campaign_id', campaign_id).eq('subject', event.get('subject', ''))
                    .eq('status', 'sent').execute().data or [])
            rows = [r for r in rows if r['to_email'].lower() == email and not r.get('message_id')]
            if len(rows) == 1:
                return rows[0]
        return None

    async def sync(self, tenant_id):
        added = ignored = 0
        async with httpx.AsyncClient(timeout=30) as client:
            events = await self.events(client, event='clicks', days=30)
        known = {r['to_email'] for r in self.list(tenant_id)}
        for event in events:
            if (event.get('email') or '').strip().lower() in known:
                continue
            if not website_click(event):
                ignored += 1
                continue
            source = self.correlate(tenant_id, event)
            if not source:
                ignored += 1
                continue
            clicked = timestamp(event['date'])
            if clicked < timestamp(source['sent_at']) or clicked > utcnow():
                ignored += 1
                continue
            # Do not enroll test/manual campaigns or recursively enroll follow-ups.
            campaigns = (self.db.table('urap_campaigns').select('name').eq('tenant_id', tenant_id)
                         .eq('id', source['campaign_id']).execute().data or [])
            if not campaigns or not campaigns[0]['name'].startswith('Autopilot —') or 'Click follow-up' in campaigns[0]['name']:
                ignored += 1
                continue
            email = source['to_email'].strip().lower()
            existing = (self.db.table('urap_click_followups').select('id').eq('tenant_id', tenant_id)
                        .eq('to_email', email).execute().data or [])
            if existing:
                continue
            company, sector = source.get('company', ''), source.get('sector', '')
            if not company or not sector:
                jobs = (self.db.table('urap_warp_jobs').select('generated').eq('tenant_id', tenant_id)
                        .gte('created_at', (timestamp(source['sent_at']) - timedelta(days=1)).isoformat())
                        .lte('created_at', source['sent_at']).execute().data or [])
                matches = [lead for job in jobs for lead in (job.get('generated') or [])
                           if lead.get('lead_id') == source.get('lead_id')]
                if matches:
                    company = company or matches[0].get('company', '')
                    sector = sector or matches[0].get('sector', '')
            row = {'tenant_id': tenant_id, 'to_email': email, 'source_send_id': source['id'],
                   'lead_id': source.get('lead_id') or '', 'company': company,
                   'sector': resolve_sector(sector, company), 'clicked_url': event['link'],
                   'clicked_at': clicked.isoformat(),
                   'next_send_at': max(clicked + timedelta(days=1), utcnow()).isoformat()}
            result = self.db.table('urap_click_followups').upsert(
                row, on_conflict='tenant_id,to_email', ignore_duplicates=True).execute()
            added += len(result.data or [])
            known.add(email)
        return {'enrolled': added, 'ignored_events': ignored, 'click_events': len(events)}

    def list(self, tenant_id):
        return (self.db.table('urap_click_followups').select('*').eq('tenant_id', tenant_id)
                .order('next_send_at').limit(500).execute().data or [])

    def suppress_lead(self, tenant_id, lead_id, reason):
        self.db.table('urap_click_followups').update({'status': 'suppressed', 'reason': reason}).eq(
            'tenant_id', tenant_id).eq('lead_id', lead_id).in_('status', ['pending', 'processing']).execute()

    async def gmail_token(self, client, expected_mailbox):
        resp = await client.post('https://oauth2.googleapis.com/token', data={
            'client_id': os.environ['FOLLOWUP_GMAIL_CLIENT_ID'],
            'client_secret': os.environ['FOLLOWUP_GMAIL_CLIENT_SECRET'],
            'refresh_token': os.environ['FOLLOWUP_GMAIL_REFRESH_TOKEN'], 'grant_type': 'refresh_token'})
        resp.raise_for_status()
        token = resp.json()['access_token']
        resp = await client.get('https://gmail.googleapis.com/gmail/v1/users/me/profile',
                                headers={'Authorization': f'Bearer {token}'})
        resp.raise_for_status()
        if resp.json().get('emailAddress', '').lower() != expected_mailbox.lower():
            raise RuntimeError('Reply mailbox does not match outreach sender; follow-ups held')
        return token

    async def suppression(self, client, token, row):
        tenant, email = row['tenant_id'], row['to_email']
        if self._blocked_contacts is None:
            blocked = set()
            for offset in range(0, 10000, 100):
                resp = await client.get('https://api.brevo.com/v3/smtp/blockedContacts',
                                        params={'limit': 100, 'offset': offset},
                                        headers={'api-key': os.environ['BREVO_API_KEY']})
                resp.raise_for_status()
                page = resp.json().get('contacts', [])
                blocked.update(c['email'].lower() for c in page)
                if len(page) < 100:
                    self._blocked_contacts = blocked
                    break
            if self._blocked_contacts is None:
                raise RuntimeError('Blocked-contact pagination incomplete; follow-ups held')
        if email in self._blocked_contacts:
            return 'Brevo transactional suppression'

        contacts = (self.db.table('urap_contacts').select('global_status,channel_state')
                    .eq('tenant_id', tenant).eq('email', email).execute().data or [])
        for contact in contacts:
            if contact.get('global_status') in ('not_interested', 'unsubscribe', 'unsubscribed', 'meeting_set', 'qualified', 'customer', 'won'):
                return 'CRM stop or handoff'
            if any(state in ('replied', 'paused', 'bounced', 'opted_out') for state in (contact.get('channel_state') or {}).values()):
                return 'CRM reply or blocked channel'
        enrollments = (self.db.table('urap_sequence_enrollments').select('status').eq('tenant_id', tenant)
                       .eq('to_email', email).execute().data or [])
        if any(e['status'] in ('active', 'replied', 'bounced', 'unsubscribed', 'paused') for e in enrollments):
            return 'Existing sequence or terminal enrollment'
        # Query all mail (including read/archive/spam), not only unread replies.
        source = (self.db.table('urap_campaign_sends').select('sent_at').eq('tenant_id', tenant)
                  .eq('id', row['source_send_id']).single().execute().data)
        after = int(timestamp(source['sent_at']).timestamp())
        resp = await client.get('https://gmail.googleapis.com/gmail/v1/users/me/messages',
                                headers={'Authorization': f'Bearer {token}'},
                                params={'q': f'from:({email}) after:{after} -in:sent',
                                        'includeSpamTrash': 'true', 'maxResults': 1})
        resp.raise_for_status()
        if resp.json().get('messages'):
            return 'Inbound reply — human follow-up required'
        events = await self.events(client, email=email, days=90)
        stop = {'hardBounces', 'hard_bounce', 'softBounces', 'soft_bounce', 'blocked', 'invalid', 'spam', 'unsubscribed', 'reply'}
        if any(e.get('event') in stop for e in events):
            return 'Brevo bounce, block, unsubscribe or complaint'
        resp = await client.get('https://api.brevo.com/v3/contacts/' + email,
                                headers={'api-key': os.environ['BREVO_API_KEY']})
        if resp.status_code != 404:
            resp.raise_for_status()
            if resp.json().get('emailBlacklisted'):
                return 'Brevo contact suppressed'
        return ''

    async def run(self, tenant_id, icp, budget):
        from modules.m5_api.autopilot_runner import build_outreach_html
        from tier3.brevo.client import BrevoClient
        stats = await self.sync(tenant_id)
        stats.update(sent=0, suppressed=0, held=0)
        due = (self.db.table('urap_click_followups').select('*').eq('tenant_id', tenant_id)
               .eq('status', 'pending').lte('next_send_at', utcnow().isoformat())
               .order('next_send_at').limit(min(max(budget, 0), 30)).execute().data or [])
        if not due or budget <= 0:
            return stats
        from_email = icp.get('from_email') or os.getenv('OUTREACH_FROM_EMAIL', 'djdabblin@gmail.com')
        from_name = icp.get('from_name') or 'Dennis Day II — Dabblin Cloud Technologies'
        async with httpx.AsyncClient(timeout=30) as client:
            token = await self.gmail_token(client, from_email)
            for row in due[:min(budget, 30)]:
                try:
                    reason = await self.suppression(client, token, row)
                except Exception:
                    stats['held'] += 1  # unavailable suppression source never permits a send
                    self.db.table('urap_click_followups').update({
                        'reason': 'Suppression check unavailable; held until next scheduled check'
                    }).eq('id', row['id']).eq('status', 'pending').execute()
                    continue
                if reason:
                    self.db.table('urap_click_followups').update({'status': 'suppressed', 'reason': reason}).eq('id', row['id']).execute()
                    stats['suppressed'] += 1
                    continue
                claimed = (self.db.table('urap_click_followups').update({'status': 'processing'})
                           .eq('tenant_id', tenant_id).eq('id', row['id']).eq('status', 'pending')
                           .eq('step', row['step']).execute().data or [])
                if not claimed:
                    continue
                # Persist a reservation before sending. A crash leaves processing/review;
                # it is never automatically retried because delivery could have occurred.
                campaign_id, send_id = str(uuid.uuid4()), str(uuid.uuid4())
                subject, body = followup_copy(row['company'], row['sector'], row['step'])
                html = build_outreach_html(body, row['sector'], f'click_followup_{row["step"] + 1}')
                self.db.table('urap_campaigns').insert({'id': campaign_id, 'tenant_id': tenant_id,
                    'name': f'Autopilot — Click follow-up {row["step"] + 1} — {utcnow().date()}',
                    'from_email': from_email, 'from_name': from_name, 'subject_template': subject,
                    'body_template': html, 'status': 'sending', 'sent_count': 1}).execute()
                self.db.table('urap_campaign_sends').insert({'id': send_id, 'tenant_id': tenant_id,
                    'campaign_id': campaign_id, 'lead_id': row['lead_id'], 'to_email': row['to_email'],
                    'subject': subject, 'body_html': html, 'status': 'processing', 'sector': row['sector'],
                    'company': row['company'], 'provider': 'brevo'}).execute()
                # Single provider: never fall through to another provider on suppression
                # or ambiguous timeout (that could send twice or bypass a Brevo block).
                result = await BrevoClient().send(to_email=row['to_email'], to_name=row['company'],
                    from_email=from_email, from_name=from_name, subject=subject, body_html=html,
                    reply_to=from_email, tag=f'campaign:{campaign_id}')
                now = utcnow()
                self.db.table('urap_campaign_sends').update({'status': 'sent' if result.success else 'failed',
                    'message_id': result.message_id, 'error': result.error, 'sent_at': now.isoformat()}).eq('id', send_id).execute()
                self.db.table('urap_campaigns').update({'status': 'sent' if result.success else 'failed',
                    'sent_count': 1 if result.success else 0,
                    'failed_count': 0 if result.success else 1}).eq('id', campaign_id).execute()
                update = {'status': 'review', 'reason': 'Provider failure or ambiguous delivery; review before retry'}
                if result.success:
                    stats['sent'] += 1
                    update = {'status': 'complete' if row['step'] == 1 else 'pending', 'step': row['step'] + 1,
                              'last_sent_at': now.isoformat(), 'next_send_at': (now + timedelta(days=3)).isoformat(), 'reason': ''}
                else:
                    stats['held'] += 1
                self.db.table('urap_click_followups').update(update).eq('id', row['id']).eq('status', 'processing').execute()
        return stats
