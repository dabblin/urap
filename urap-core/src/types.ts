export interface LeadStatusObject {
  leadId: string;
  tenantId: string;
  contactData: {
    name: string;
    email: string;
    phone?: string;
    linkedinUrl?: string;
    company: string;
    title: string;
    intentSignals: string[];
  };
  channelState: {
    email: 'idle' | 'sent' | 'opened' | 'replied' | 'bounced' | 'paused';
    sms: 'idle' | 'sent' | 'replied' | 'opted_out' | 'paused';
    linkedin: 'idle' | 'connected' | 'messaged' | 'replied' | 'paused';
    voice: 'idle' | 'dialed' | 'answered' | 'voicemail' | 'paused';
  };
  globalStatus:
    | 'prospecting'
    | 'engaged'
    | 'interested'
    | 'meeting_set'
    | 'qualified'
    | 'not_interested'
    | 'unsubscribe';
  lastActivity: string;
  assignedAgent?: string;
  consentRecord?: {
    source: string;
    consentedAt: string;
    ipAddress: string;
    oneToOneRule: boolean;
    platformName: string;
  };
}

export interface UrapTool {
  id: string;
  label: string;
  pillar: 'data' | 'engagement' | 'automation';
  icon: string;
  route: string;
  featureFlag?: string;
  sprint: number;
}

export interface UrapConfig {
  apiKey: string;
  tenantId: string;
  engineUrl?: string;
}

export interface EmbedConfig {
  captureUrl: string;
  consentUrl: string;
  tenantId: string;
  formTitle?: string;
  submitLabel?: string;
  successMessage?: string;
  extraFields?: string[];
}
