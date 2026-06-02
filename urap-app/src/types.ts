export interface UrapTool {
  id: string;
  label: string;
  pillar: 'data' | 'engagement' | 'automation';
  icon: string;
  route: string;
  featureFlag?: string;
  sprint: number;
}

export interface ContactResult {
  leadId: string;
  name: string;
  title: string;
  company: string;
  email: string;
  phone?: string;
  linkedinUrl?: string;
  globalStatus: string;
  emailVerified: boolean;
  enrichmentSource: string;
  intentSignals: string[];
}
