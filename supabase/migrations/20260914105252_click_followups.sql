-- Persist provider correlation and industry context for scheduled click follow-ups.
alter table public.urap_campaign_sends add column if not exists message_id text;
alter table public.urap_campaign_sends add column if not exists sector text not null default '';
alter table public.urap_campaign_sends add column if not exists company text not null default '';

create table public.urap_click_followups (
  id uuid primary key default gen_random_uuid(),
  tenant_id text not null,
  to_email text not null check (to_email = lower(trim(to_email))),
  source_send_id uuid not null references public.urap_campaign_sends(id),
  lead_id text not null default '',
  company text not null default '',
  sector text not null default '',
  clicked_url text not null,
  clicked_at timestamptz not null,
  next_send_at timestamptz not null,
  step int not null default 0 check (step between 0 and 2),
  status text not null default 'pending' check (status in ('pending','processing','complete','suppressed','review')),
  reason text not null default '',
  last_sent_at timestamptz,
  created_at timestamptz not null default now(),
  unique (tenant_id, to_email)
);
create index on public.urap_click_followups(tenant_id, status, next_send_at);
alter table public.urap_click_followups enable row level security;
grant select, insert, update on public.urap_click_followups to service_role;
-- Existing engine state guards were silently failing with permission denied.
grant select, update on public.urap_contacts to service_role;
grant select on public.urap_sequence_enrollments to service_role;

-- A tenant lease serializes scheduled/manual runs across Cloud Run instances.
create table public.urap_autopilot_leases (
 tenant_id text primary key, token uuid not null, expires_at timestamptz not null
);
alter table public.urap_autopilot_leases enable row level security;
grant select, insert, update, delete on public.urap_autopilot_leases to service_role;
create function public.urap_acquire_autopilot(p_tenant text, p_token uuid)
returns boolean language plpgsql set search_path = public as $$
begin
 insert into urap_autopilot_leases values (p_tenant, p_token, now() + interval '30 minutes')
 on conflict (tenant_id) do update set token = excluded.token, expires_at = excluded.expires_at
 where urap_autopilot_leases.expires_at < now();
 return found;
end $$;
revoke all on function public.urap_acquire_autopilot(text, uuid) from public, anon, authenticated;
grant execute on function public.urap_acquire_autopilot(text, uuid) to service_role;
