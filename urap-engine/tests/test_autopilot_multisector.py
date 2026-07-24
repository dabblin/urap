from types import SimpleNamespace

import pytest

from modules.m3_agents import warp_mode
from modules.m3_agents.warp_mode import WarpLead, WarpModeAgent
from modules.m5_api.autopilot_runner import AutopilotRunner


@pytest.mark.asyncio
async def test_multisector_run_sources_and_keeps_every_sector(monkeypatch):
    runner = AutopilotRunner()
    sectors = [f"Sector {index}" for index in range(12)]
    config = {
        "enabled": True,
        "daily_send_limit": 120,
        "icp": {
            "sectors": sectors,
            "keywords": "legacy keyword",
            "limit": 25,
            "icp_label": "multi-sector-test",
        },
    }
    sourced_sectors = []
    captured = {}

    monkeypatch.setattr(runner, "get_config", lambda _tenant_id: config)
    monkeypatch.setattr(runner, "_unsubscribe_rate", lambda _tenant_id: 0.0)
    monkeypatch.setattr(runner, "_sent_today", lambda _tenant_id: 0)
    monkeypatch.setattr(runner, "_dedup_leads", lambda _tenant_id, leads: (leads, 0))
    monkeypatch.setattr(runner, "_log_run", lambda _tenant_id, _stats: None)

    async def source_leads(icp):
        sector = icp["keywords"]
        sourced_sectors.append(sector)
        assert icp["limit"] == 10
        return [
            {
                "lead_id": f"{sector}-{index}",
                "name": f"{sector} Lead {index}",
                "email": f"{sector.lower().replace(' ', '-')}-{index}@example.com",
                "title": "Owner",
                "company": f"{sector} Company {index}",
            }
            for index in range(10)
        ]

    async def run_job(_self, icp, tenant_id, leads=None):
        captured["icp"] = icp
        captured["tenant_id"] = tenant_id
        captured["leads"] = leads
        return SimpleNamespace(
            job_id="job-1",
            leads_found=len(leads),
            sequences_queued=len(leads),
            generated=[],
        )

    monkeypatch.setattr(runner, "_source_leads", source_leads)
    monkeypatch.setattr(WarpModeAgent, "run_job", run_job)

    result = await runner.run("dev-tenant")

    assert set(sourced_sectors) == set(sectors)
    assert len(captured["leads"]) == 120
    assert captured["icp"]["limit"] == 120
    assert result.leads_found == 120
    assert result.sector_stats == {sector: 10 for sector in sectors}


@pytest.mark.asyncio
async def test_warp_mode_accepts_batches_larger_than_25(monkeypatch):
    agent = WarpModeAgent()
    leads = [
        {
            "lead_id": f"lead-{index}",
            "name": f"Lead {index}",
            "email": f"lead-{index}@example.com",
            "title": "Owner",
            "company": f"Company {index}",
        }
        for index in range(30)
    ]

    async def generate(lead, _icp):
        return WarpLead(
            lead_id=lead["lead_id"],
            name=lead["name"],
            email=lead["email"],
            title=lead["title"],
            company=lead["company"],
            subject="Subject",
            body_html="<p>Body</p>",
            copy_status="generated",
        )

    class FakeQuery:
        def insert(self, _record):
            return self

        def execute(self):
            return None

    class FakeDb:
        def table(self, _name):
            return FakeQuery()

    monkeypatch.setattr(agent, "_generate_copy_for_lead", generate)
    monkeypatch.setattr(agent, "_db", lambda: FakeDb())
    monkeypatch.setattr(warp_mode, "notify_warp_job_done", lambda *_args: None)

    result = await agent.run_job(
        icp={"icp_label": "limit-test", "limit": 30},
        tenant_id="dev-tenant",
        leads=leads,
    )

    assert result.leads_found == 30
    assert result.sequences_queued == 30
    assert len(result.generated) == 30
