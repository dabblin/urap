-- Update Dabblin_Cloud Autopilot Config with 12 Sectors
UPDATE urap_autopilot_configs
SET 
    daily_send_limit = 120,
    icp = icp::jsonb || '{
        "sectors": [
            "Barbershops", "Restaurants", "Law Offices", "Dental Offices", 
            "Gyms & Fitness", "Pet Services", "Nail Salons", "Florists", 
            "Childcare", "Cleaning Services", "Auto Repair", "Med Spas"
        ]
    }'::jsonb
WHERE tenant_id = 'Dabblin_Cloud';
