-- Fix: campaigns created from Companies Search lists always failed with 500.
-- urap_campaigns.list_id was uuid + FK to urap_campaign_lists, but the app
-- passes "company:<uuid>" for company lists (see server/main.py dispatch_campaign).
-- Relax to text so both list kinds work.
-- Paste into: supabase.com/dashboard/project/rtyzrrbezivflqhaernb/sql/new

alter table urap_campaigns drop constraint if exists urap_campaigns_list_id_fkey;
alter table urap_campaigns alter column list_id type text using list_id::text;
