-- Sprint 9A — Campaign Lists + Campaigns
-- Paste this entire block into: supabase.com/dashboard/project/rtyzrrbezivflqhaernb/sql/new

create table if not exists urap_campaign_lists (
  id            uuid primary key default gen_random_uuid(),
  tenant_id     text not null,
  name          text not null,
  contact_count int  not null default 0,
  created_at    timestamptz not null default now()
);

create table if not exists urap_campaign_list_contacts (
  id                 uuid primary key default gen_random_uuid(),
  list_id            uuid not null references urap_campaign_lists(id) on delete cascade,
  tenant_id          text not null,
  lead_id            text,
  name               text not null default '',
  title              text not null default '',
  company            text not null default '',
  email              text not null,
  phone              text not null default '',
  email_verified     boolean not null default false,
  enrichment_source  text not null default '',
  created_at         timestamptz not null default now()
);

create table if not exists urap_campaigns (
  id               uuid primary key default gen_random_uuid(),
  tenant_id        text not null,
  name             text not null,
  list_id          uuid references urap_campaign_lists(id) on delete set null,
  from_email       text not null,
  from_name        text not null default '',
  subject_template text not null,
  body_template    text not null,
  ai_personalize   boolean not null default false,
  status           text not null default 'draft',
  sent_count       int  not null default 0,
  failed_count     int  not null default 0,
  created_at       timestamptz not null default now()
);

create table if not exists urap_campaign_sends (
  id          uuid primary key default gen_random_uuid(),
  campaign_id uuid not null references urap_campaigns(id) on delete cascade,
  tenant_id   text not null,
  lead_id     text,
  to_email    text not null,
  subject     text,
  status      text not null default 'sent',
  provider    text,
  error       text,
  sent_at     timestamptz not null default now()
);

-- Sprint 9B — Campaign Landing Pages
create table if not exists urap_campaign_pages (
  id           uuid primary key default gen_random_uuid(),
  tenant_id    text not null,
  slug         text not null unique,
  headline     text not null,
  subheadline  text not null default '',
  cta_text     text not null default 'Get Started',
  brand_color  text not null default '#6366f1',
  form_fields  text[] not null default '{name,email,phone}',
  logo_url     text,
  company_name text,
  campaign_id  uuid references urap_campaigns(id) on delete set null,
  created_at   timestamptz not null default now()
);

-- Indexes for common queries
create index if not exists idx_campaign_lists_tenant    on urap_campaign_lists(tenant_id);
create index if not exists idx_campaign_list_contacts_list on urap_campaign_list_contacts(list_id);
create index if not exists idx_campaigns_tenant         on urap_campaigns(tenant_id);
create index if not exists idx_campaign_sends_campaign  on urap_campaign_sends(campaign_id);
create index if not exists idx_campaign_pages_slug      on urap_campaign_pages(slug);
create index if not exists idx_campaign_pages_tenant    on urap_campaign_pages(tenant_id);
