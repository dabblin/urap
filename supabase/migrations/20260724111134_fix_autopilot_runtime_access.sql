-- The engine authenticates to PostgREST as service_role. Tables created from
-- the SQL editor do not automatically grant that role table privileges.
grant select, insert, update, delete
on table public.urap_autopilot_configs, public.urap_warp_jobs
to service_role;

-- The live scheduler and Vercel app both use dev-tenant. The earlier sector
-- update targeted Dabblin_Cloud, so persist the working environment fallback
-- under the tenant that actually runs.
insert into public.urap_autopilot_configs (
  tenant_id,
  enabled,
  icp,
  schedule_hours,
  daily_send_limit,
  route_after_warp,
  route_marketplace_id,
  route_min_score,
  updated_at
)
values (
  'dev-tenant',
  true,
  '{
    "keywords": "barbershop",
    "sectors": [
      "Barbershops",
      "Restaurants",
      "Law Offices",
      "Dental Offices",
      "Gyms & Fitness",
      "Pet Services",
      "Nail Salons",
      "Florists",
      "Childcare",
      "Cleaning Services",
      "Auto Repair",
      "Med Spas"
    ],
    "location": "Bronx, NY",
    "locations": [
      "Bronx, NY",
      "Harlem, New York, NY",
      "Manhattan, NY",
      "Brooklyn, NY",
      "Queens, NY",
      "Yonkers, NY",
      "Mount Vernon, NY",
      "New Rochelle, NY",
      "Jersey City, NJ",
      "Staten Island, NY"
    ],
    "industry": "",
    "value_prop": "a 24/7 AI receptionist that answers your phone, books appointments, and never misses a customer call",
    "icp_label": "multi-sector-daily",
    "limit": 25,
    "from_email": "djdabblin@gmail.com",
    "from_name": "Dennis Day II — Dabblin Cloud Technologies"
  }'::jsonb,
  24,
  120,
  false,
  '',
  60,
  now()
)
on conflict (tenant_id) do update set
  enabled = excluded.enabled,
  icp = excluded.icp,
  schedule_hours = excluded.schedule_hours,
  daily_send_limit = excluded.daily_send_limit,
  route_after_warp = excluded.route_after_warp,
  route_marketplace_id = excluded.route_marketplace_id,
  route_min_score = excluded.route_min_score,
  updated_at = excluded.updated_at;
