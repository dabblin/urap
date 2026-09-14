from copy import deepcopy
from datetime import timedelta
from types import SimpleNamespace
from html import unescape

import pytest

from modules.m2_outreach import click_followups as module
from modules.m2_outreach.click_followups import ClickFollowups, utcnow, website_click
from modules.m2_outreach.industry_video import VIDEOS, resolve_sector, followup_copy
from modules.m5_api.autopilot_runner import AutopilotRunner, build_outreach_html
from modules.m3_agents.warp_mode import WarpModeAgent


class Query:
    def __init__(self, db, table):
        self.db, self.table = db, table
        self.filters, self.action, self.payload = [], 'select', None
    def select(self, *args, **kwargs): return self
    def eq(self, k, v): self.filters.append(lambda r: r.get(k) == v); return self
    def in_(self, k, v): self.filters.append(lambda r: r.get(k) in v); return self
    def gte(self, k, v): self.filters.append(lambda r: r.get(k, '') >= v); return self
    def lte(self, k, v): self.filters.append(lambda r: r.get(k, '') <= v); return self
    def order(self, *args, **kwargs): return self
    def limit(self, *args): return self
    def update(self, row): self.action, self.payload = 'update', row; return self
    def insert(self, row): self.action, self.payload = 'insert', row; return self
    def upsert(self, row, **kwargs): self.action, self.payload = 'upsert', row; return self
    def delete(self): self.action = 'delete'; return self
    def execute(self):
        rows = self.db.rows.setdefault(self.table, [])
        found = [r for r in rows if all(f(r) for f in self.filters)]
        if self.action in ('insert', 'upsert'):
            if self.action == 'upsert' and any(r['tenant_id'] == self.payload['tenant_id'] and r['to_email'] == self.payload['to_email'] for r in rows):
                return SimpleNamespace(data=[])
            row = deepcopy(self.payload); row.setdefault('id', str(len(rows)))
            if self.table == 'urap_click_followups': row.update(status='pending', step=0)
            rows.append(row); found = [row]
        elif self.action == 'update':
            for r in found: r.update(self.payload)
        elif self.action == 'delete':
            self.db.rows[self.table] = [r for r in rows if r not in found]
        return SimpleNamespace(data=deepcopy(found))


class DB:
    def __init__(self, rows): self.rows = deepcopy(rows)
    def table(self, table): return Query(self, table)


def fixture_db():
    now = utcnow()
    source = {'id': 'source', 'tenant_id': 'tenant', 'campaign_id': '11111111-1111-1111-1111-111111111111',
              'status': 'sent', 'to_email': 'owner@example.com', 'subject': 'A useful example',
              'lead_id': 'lead', 'message_id': '<message>', 'sent_at': (now - timedelta(days=5)).isoformat(),
              'company': 'Example Nails', 'sector': 'nail_salons'}
    event = {'event': 'clicks', 'email': 'OWNER@example.com', 'messageId': '<message>',
             'date': (now - timedelta(days=2)).isoformat(), 'link': 'https://dabblin.com/demo/'}
    db = DB({'urap_campaign_sends': [source], 'urap_campaigns': [{'id': source['campaign_id'],
             'tenant_id': 'tenant', 'name': 'Autopilot — daily'}]})
    return db, event


@pytest.mark.parametrize('sector', VIDEOS)
def test_each_video_is_a_single_tracked_preview(sector):
    html = unescape(build_outreach_html('<p>Hello</p>', sector))
    assert html.count('<a ') == 1
    assert f'industry={sector}' in html
    assert f'/thumbnails/{sector}.jpg' in html
    assert '<video' not in html
    assert f'utm_content=video_{sector}' in html


@pytest.mark.parametrize('value,expected', [('barber', 'barbershops'), ('mobile pet groomer','pet_services'),
    ('nail salon','nail_salons'), ('unknown',''), ('law firm and dental office','')])
def test_sector_mapping(value, expected):
    assert resolve_sector(value) == expected


@pytest.mark.parametrize('event', [{'event':'opened','link':'https://dabblin.com/'},
    {'event':'clicks','link':'https://dabblin.com.evil.test/'},
    {'event':'clicks','link':'https://dabblin.com/unsubscribe'},
    {'event':'clicks','link':'http://dabblin.com/'},
    {'event':'clicks','link':'https://dabblin.com/','isBot':True}])
def test_non_qualifying_events(event): assert not website_click(event)


@pytest.mark.asyncio
async def test_sync_dedupes_and_does_not_reset_cadence_or_cross_tenants(monkeypatch):
    db, event = fixture_db(); service = ClickFollowups(db)
    async def events(*args, **kwargs): return [event, event]
    monkeypatch.setattr(service, 'events', events)
    stats = await service.sync('tenant')
    assert stats['enrolled'] == 1
    row = db.rows['urap_click_followups'][0]
    row.update(step=1, next_send_at=(utcnow()+timedelta(days=3)).isoformat())
    before = deepcopy(row)
    await service.sync('tenant')
    assert db.rows['urap_click_followups'] == [before]
    assert (await service.sync('other-tenant'))['enrolled'] == 0


@pytest.mark.asyncio
async def test_send_path_schedules_second_step_then_completes(monkeypatch):
    db, event = fixture_db(); service = ClickFollowups(db)
    async def events(*args, **kwargs): return [event]
    async def token(*args): return 'token'
    async def suppression(*args): return ''
    sent = []
    async def send(_self, **kwargs):
        sent.append(kwargs)
        return SimpleNamespace(success=True, message_id='sent-id', error=None)
    monkeypatch.setattr(service, 'events', events)
    monkeypatch.setattr(service, 'gmail_token', token)
    monkeypatch.setattr(service, 'suppression', suppression)
    from tier3.brevo.client import BrevoClient
    monkeypatch.setattr(BrevoClient, 'send', send)
    icp = {'from_email':'sender@example.com'}
    assert (await service.run('tenant', icp, 1))['sent'] == 1
    row = db.rows['urap_click_followups'][0]
    assert row['step'] == 1 and row['status'] == 'pending'
    assert module.timestamp(row['next_send_at']) - module.timestamp(row['last_sent_at']) == timedelta(days=3)
    assert (await service.run('tenant', icp, 1))['sent'] == 0
    row['next_send_at'] = (utcnow()-timedelta(seconds=1)).isoformat()
    assert (await service.run('tenant', icp, 0))['sent'] == 0
    assert (await service.run('tenant', icp, 1))['sent'] == 1
    assert row['status'] == 'complete' and row['step'] == 2
    assert (await service.run('tenant', icp, 1))['sent'] == 0
    assert len(sent) == 2
    assert 'video_nail_salons' in sent[0]['body_html']

@pytest.mark.asyncio
@pytest.mark.parametrize('reason', ['Inbound reply', 'Brevo blocked', 'error'])
async def test_stops_or_holds_when_suppression_unavailable(monkeypatch, reason):
    db, event = fixture_db(); service = ClickFollowups(db)
    async def events(*args, **kwargs): return [event]
    async def token(*args): return 'token'
    async def suppression(*args):
        if reason == 'error': raise RuntimeError('Gmail unavailable')
        return reason
    monkeypatch.setattr(service, 'events', events)
    monkeypatch.setattr(service, 'gmail_token', token)
    monkeypatch.setattr(service, 'suppression', suppression)
    result = await service.run('tenant', {}, 1)
    assert result['sent'] == 0
    assert db.rows['urap_click_followups'][0]['status'] == ('pending' if reason == 'error' else 'suppressed')
    assert len(db.rows['urap_campaign_sends']) == 1


def test_copy_never_claims_tracking_or_video_view_and_escapes_company():
    for step in (0, 1):
        subject, body = followup_copy('<script>business</script>', 'barbershops', step)
        assert '<script>' not in body
        assert not any(word in body.lower() for word in ('you clicked', 'you watched', 'tracking'))


@pytest.mark.asyncio
async def test_sector_survives_warp_generation(monkeypatch):
    agent = WarpModeAgent()
    async def draft(*args): return '', ''
    monkeypatch.setattr(agent, '_draft_copy_gemini', draft)
    lead = await agent._generate_copy_for_lead({'company':'Some Company', '_autopilot_sector':'Pet Services'}, {})
    assert lead.sector == 'pet_services'

@pytest.mark.asyncio
async def test_ambiguous_delivery_is_not_retried(monkeypatch):
    db, event = fixture_db(); service = ClickFollowups(db)
    async def events(*args, **kwargs): return [event]
    async def token(*args): return 'token'
    async def suppression(*args): return ''
    calls = []
    async def send(_self, **kwargs):
        calls.append(kwargs)
        return SimpleNamespace(success=False, message_id=None, error='Timeout')
    from tier3.brevo.client import BrevoClient
    monkeypatch.setattr(service, 'events', events)
    monkeypatch.setattr(service, 'gmail_token', token)
    monkeypatch.setattr(service, 'suppression', suppression)
    monkeypatch.setattr(BrevoClient, 'send', send)
    await service.run('tenant', {}, 2)
    await service.run('tenant', {}, 2)
    assert len(calls) == 1
    assert db.rows['urap_click_followups'][0]['status'] == 'review'


@pytest.mark.asyncio
async def test_suppression_checks_actual_provider_and_gmail_paths(monkeypatch):
    import httpx
    db, event = fixture_db(); service = ClickFollowups(db)
    async def events(*args, **kwargs): return [event]
    monkeypatch.setattr(service, 'events', events)
    monkeypatch.setenv('BREVO_API_KEY', 'test-key')
    await service.sync('tenant')
    row = db.rows['urap_click_followups'][0]
    Query.single = lambda self: self
    original_execute = Query.execute
    # Supabase .single() wraps one row as an object for the source timestamp.
    def execute(self):
        result = original_execute(self)
        if self.table == 'urap_campaign_sends' and len(self.filters) == 2:
            result.data = result.data[0]
        return result
    monkeypatch.setattr(Query, 'execute', execute)
    def respond(request):
        if request.url.path.endswith('blockedContacts'):
            return httpx.Response(200, json={'contacts': []})
        if request.url.path.endswith('/messages'):
            assert 'after:' in request.url.params['q']
            assert request.url.params['includeSpamTrash'] == 'true'
            return httpx.Response(200, json={'messages': [{'id': 'reply'}]})
        raise AssertionError(f'Unexpected request: {request.url}')
    async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
        assert 'Inbound reply' in await service.suppression(client, 'token', row)


@pytest.mark.asyncio
async def test_autopilot_prioritizes_followups_and_releases_lease(monkeypatch):
    from modules.m5_api import autopilot_runner as runner_module
    db = DB({'urap_autopilot_leases': [{'tenant_id': 'tenant'}]})
    def acquire(name, args):
        db.rows['urap_autopilot_leases'][0]['token'] = args['p_token']
        return SimpleNamespace(execute=lambda: SimpleNamespace(data=True))
    db.rpc = acquire
    monkeypatch.setattr(runner_module, '_db', lambda: db)
    runner = AutopilotRunner(); calls = []
    monkeypatch.setattr(runner, 'get_config', lambda t: {'enabled':True,'daily_send_limit':120,'icp':{'click_followups':True}})
    monkeypatch.setattr(runner, '_unsubscribe_rate', lambda t:0)
    monkeypatch.setattr(runner, '_sent_today', lambda t:119)
    monkeypatch.setattr(runner, '_log_run', lambda *args:None)
    async def followups(_self, tenant, icp, budget):
        calls.append(('followups', budget)); return {'sent':1}
    async def fresh(tenant):
        calls.append(('fresh', 0)); return runner_module.AutopilotRunResult(tenant,'',0,0,0,False,'limit')
    monkeypatch.setattr(ClickFollowups, 'run', followups)
    monkeypatch.setattr(runner, '_run_fresh', fresh)
    result = await runner.run('tenant')
    assert calls == [('followups',1),('fresh',0)]
    assert result.followup_stats == {'sent':1}
    assert db.rows['urap_autopilot_leases'] == []
