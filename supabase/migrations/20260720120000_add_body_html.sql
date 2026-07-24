-- Add body_html column to store the full email body

ALTER TABLE urap_campaign_sends 
ADD COLUMN IF NOT EXISTS body_html text;
