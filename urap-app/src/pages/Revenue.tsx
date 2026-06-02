import { useState, useEffect } from 'react';

import { ENGINE, TENANT } from '../lib/config.js';
const API_KEY = '';

// ── Types ──────────────────────────────────────────────────────────────────────

type Category = 'all' | 'ppl' | 'directory' | 'saas' | 'agency';

interface Program {
  name: string;
  ppl: string;
  notes: string;
}

interface IncomeMethod {
  id: string;
  category: Category;
  title: string;
  subtitle: string;
  monthlyMin: number;
  monthlyMax: number;
  difficulty: 'Easy' | 'Medium';
  timeToFirstDollar: string;
  description: string;
  steps: string[];
  programs: Program[];
  revenueMath: string;
  canRace: boolean; // PPL methods can run CPL auction
}

interface BidResult {
  marketplace_id: string;
  marketplace_name: string;
  cpl: number;
  accepted: boolean;
  error: string;
}

interface RaceResult {
  auction_id: string;
  lead_id: string;
  winner_marketplace_id: string;
  winner_marketplace_name: string;
  winning_cpl: number;
  all_bids: BidResult[];
  dispatched: boolean;
  error: string;
  created_at: string;
}

interface RaceSummary {
  results: RaceResult[];
  total_auctions: number;
  auctions_won: number;
  total_earned: number;
}

// ── Method Catalog ─────────────────────────────────────────────────────────────

const METHODS: IncomeMethod[] = [
  {
    id: 'ppl-insurance',
    category: 'ppl',
    title: 'Pay Per Lead: Insurance',
    subtitle: 'Insurance quote referrals — auto, home, life, health',
    monthlyMin: 5000,
    monthlyMax: 25000,
    difficulty: 'Easy',
    timeToFirstDollar: '1–3 days',
    description: 'Sign up as a publisher on insurance lead marketplaces. Drive traffic to a quote form. Every completed form = payment. You never sell insurance — you connect businesses to carriers who pay per lead.',
    steps: [
      'Sign up on EverQuote Publishers and MediaAlpha',
      'Build a landing page: "Compare Insurance Quotes — Free in 2 Min"',
      'URAP Prospector → search business owners (restaurants, contractors, retail)',
      'Email: "Free insurance quote comparison for your business"',
      'Campaigns → send to 500 contacts → form fills → payment',
      'Lead Router → add publisher webhook for auto-routing',
    ],
    programs: [
      { name: 'EverQuote Publishers', ppl: '$5–$40/lead', notes: 'Auto, home, life, health. Weekly ACH.' },
      { name: 'MediaAlpha', ppl: '$8–$60/lead', notes: 'Major carriers bid in real time. Net 30.' },
      { name: 'All Web Leads', ppl: '$8–$45/lead', notes: 'Auto, home, life. Fast approval.' },
      { name: 'SmartFinancial', ppl: '$7–$50/lead', notes: 'All insurance lines. Net 30.' },
    ],
    revenueMath: '500 outreach emails → 50 click → 20 fill form → 20 × $25 avg = $500/campaign. Daily = $15,000/mo',
    canRace: true,
  },
  {
    id: 'ppl-solar',
    category: 'ppl',
    title: 'Pay Per Lead: Solar & Home Services',
    subtitle: 'Homeowner quote referrals — solar, HVAC, roofing',
    monthlyMin: 8000,
    monthlyMax: 40000,
    difficulty: 'Easy',
    timeToFirstDollar: '2–5 days',
    description: 'Home improvement companies pay $30–$120 for a homeowner requesting a quote. Find homeowners, email a free quote offer, collect the lead fee when they fill the form.',
    steps: [
      'Sign up on Modernize (Solar, HVAC, Roofing)',
      'They give you an embeddable form widget for your landing page',
      'URAP Prospector → search residential/homeowner categories in your city',
      'Email: "Get 3 free solar quotes — $0 upfront, see savings in 60 sec"',
      'Launch Campaigns to 1,000 homeowner contacts',
      'Each completed quote form = $30–$120 direct deposit',
    ],
    programs: [
      { name: 'Modernize', ppl: '$15–$120/lead', notes: 'Solar, HVAC, Roofing, Windows. Best CPL.' },
      { name: 'BuyerLink', ppl: '$8–$50/lead', notes: 'All home services. Real-time bids.' },
      { name: 'QuinStreet', ppl: '$10–$80/lead', notes: 'Home improvement + insurance. Net 30.' },
      { name: 'PX Marketplace', ppl: '$25–$200/lead', notes: 'RTB — all verticals including home.' },
    ],
    revenueMath: '1,000 homeowner emails → 100 clicks → 40 fill form → 40 × $60 avg solar = $2,400/campaign. Weekly = $9,600/mo',
    canRace: true,
  },
  {
    id: 'ppl-legal',
    category: 'ppl',
    title: 'Pay Per Lead: Legal',
    subtitle: 'Personal injury & legal referrals — highest CPL in the industry',
    monthlyMin: 10000,
    monthlyMax: 50000,
    difficulty: 'Medium',
    timeToFirstDollar: '3–7 days',
    description: 'Law firms are the highest-paying lead buyers. A PI attorney pays $200–$800 for a qualified accident victim because they earn $10K–$100K per case. Find people who need legal help and connect them with attorneys.',
    steps: [
      'Sign up on PX Marketplace, LeadsMarket, and ReviMedia (Legal vertical)',
      'Create landing page: "Injured in an accident? Get free legal consultation"',
      'Prospector → search hospitals, emergency clinics, auto body shops',
      'Campaign → offer free legal consultation referral',
      'Qualified leads fill form → attorneys bid in real time → you get paid',
      'Lead Router → route to PX Legal at $100–$500/lead via webhook',
    ],
    programs: [
      { name: 'PX Marketplace (Legal)', ppl: '$100–$500/lead', notes: 'PI, DUI, family law. RTB auction.' },
      { name: 'LeadsMarket (Legal)', ppl: '$50–$260/lead', notes: 'Finance + legal leads. Weekly pay.' },
      { name: 'ReviMedia (Legal)', ppl: '$30–$150/lead', notes: 'PI and DUI focus. Net 30.' },
      { name: 'BuyerLink (Legal)', ppl: '$30–$100/lead', notes: 'PI and mass tort.' },
    ],
    revenueMath: '100 qualified legal leads/mo × $200 avg = $20,000/mo. Just 5 PI leads/day pays the bills.',
    canRace: true,
  },
  {
    id: 'directory',
    category: 'directory',
    title: 'Directory Site Business Model',
    subtitle: '"Best [service] in [city]" passive lead engine',
    monthlyMin: 3000,
    monthlyMax: 30000,
    difficulty: 'Medium',
    timeToFirstDollar: '2–8 weeks',
    description: 'Build a local service directory that ranks on Google. People searching "best HVAC in Miami" find your site, fill a quote form, and you sell the lead. Once ranked, leads flow 24/7.',
    steps: [
      'Pick a niche: Senior Care, Solar, PI, Addiction Treatment, HVAC',
      'Prospector → scrape every business in that category in 10 cities',
      'Export contacts for directory page content',
      'Build landing page with lead capture form (e.g. "Best HVAC in Miami — 2026 Guide")',
      'On-page SEO + submit Google Business Profile',
      'Connect form to PX Marketplace / Modernize via Route webhook',
    ],
    programs: [
      { name: 'Modernize (Solar)', ppl: '$30–$120/lead', notes: 'Build solar directory → route leads here.' },
      { name: 'PX Marketplace', ppl: '$25–$200/lead', notes: 'Works for any directory niche.' },
      { name: 'GoHealth (Medicare)', ppl: '$20–$80/lead', notes: 'Build Medicare directory → route here.' },
    ],
    revenueMath: 'Directory gets 200 visits/day → 10 form fills → 10 × $60 = $600/day → $18,000/mo passive after ranking',
    canRace: false,
  },
  {
    id: 'saas-bizreach',
    category: 'saas',
    title: 'BizReach Pro Affiliate',
    subtitle: '30% recurring commissions on every subscriber you refer',
    monthlyMin: 2000,
    monthlyMax: 20000,
    difficulty: 'Easy',
    timeToFirstDollar: 'Same day',
    description: 'Earn 30% recurring monthly commission for every subscriber you refer to BizReach Pro. 50 subscribers at $79/mo = $1,185/mo passive. Compounds with every new referral.',
    steps: [
      'Contact Coalescent Mind to set up your affiliate account',
      'Prospector → search "marketing agency", "real estate agent", "insurance broker"',
      'Email subject that works: "I found 47 leads in Miami in 3 min — tool I use"',
      'Include affiliate link in email + Campaigns sequence',
      'Earn 30% recurring for every subscriber — forever',
    ],
    programs: [
      { name: 'BizReach Pro Starter', ppl: '$8.70/mo per sub', notes: '$29/mo plan. 30% recurring.' },
      { name: 'BizReach Pro Pro', ppl: '$23.70/mo per sub', notes: '$79/mo plan. 30% recurring.' },
      { name: 'BizReach Pro Agency', ppl: '$59.70/mo per sub', notes: '$199/mo plan. 30% recurring.' },
    ],
    revenueMath: '100 referrals × $79 avg × 30% = $2,370/mo forever. Keep adding → income compounds.',
    canRace: false,
  },
  {
    id: 'saas-ghl',
    category: 'saas',
    title: 'GoHighLevel Affiliate',
    subtitle: '40% recurring on every agency you refer',
    monthlyMin: 3000,
    monthlyMax: 20000,
    difficulty: 'Easy',
    timeToFirstDollar: '1 week',
    description: 'GoHighLevel is a $97–$497/mo SaaS used by marketing agencies. Their affiliate program pays 40% recurring. Use URAP to find agencies who need a white-label CRM/funnel tool.',
    steps: [
      'Sign up at gohighlevel.com/affiliate',
      'Prospector → search "marketing agency", "digital marketing", "web design"',
      'Email showing how GHL saves agencies $2,000/mo in tool costs',
      'Campaigns → send to 500 agencies with your GHL affiliate link',
      'Track in GHL dashboard → 40% recurring for life',
    ],
    programs: [
      { name: 'GHL Starter', ppl: '$38.80/mo per agency', notes: '$97/mo plan. 40% recurring.' },
      { name: 'GHL Agency', ppl: '$118.80/mo per agency', notes: '$297/mo plan. 40% recurring.' },
      { name: 'GHL Agency Pro', ppl: '$198.80/mo per agency', notes: '$497/mo plan. 40% recurring.' },
    ],
    revenueMath: '50 agencies × $97 avg × 40% = $1,940/mo recurring. 200 agencies = $7,760/mo.',
    canRace: false,
  },
  {
    id: 'saas-crm',
    category: 'saas',
    title: 'CRM & Marketing SaaS Affiliates',
    subtitle: 'HubSpot, ActiveCampaign, ClickFunnels, Brevo, SEMrush',
    monthlyMin: 2000,
    monthlyMax: 15000,
    difficulty: 'Easy',
    timeToFirstDollar: '3–7 days',
    description: 'Stack multiple SaaS affiliate programs. One-time payouts from HubSpot + recurring commissions from ActiveCampaign and ClickFunnels compound into a steady MRR stream.',
    steps: [
      'Sign up for all programs (links in table below)',
      'Prospector → search "marketing agency", "startup", "ecommerce store"',
      'Email: "The 3 tools that saved my agency $2,000/mo"',
      'Campaigns → send to 500 prospects per program',
      'Track conversions in each affiliate dashboard',
    ],
    programs: [
      { name: 'HubSpot', ppl: '$250–$1,000 per signup', notes: 'One-time. Huge brand = easy close.' },
      { name: 'ActiveCampaign', ppl: '30% recurring', notes: '$9–$229/mo plans. Best recurring for email.' },
      { name: 'Brevo', ppl: 'Up to $150/signup', notes: 'Free plan converts easily. 20% lifetime.' },
      { name: 'ClickFunnels', ppl: '$38.80/mo recurring', notes: '40% recurring. $97/mo plan.' },
      { name: 'SEMrush', ppl: '$200 per signup', notes: 'One-time. Easy for agencies.' },
    ],
    revenueMath: '10 HubSpot × $500 + 30 ActiveCampaign × $30/mo = $5,900/mo combined',
    canRace: false,
  },
  {
    id: 'saas-ai',
    category: 'saas',
    title: 'AI Tool Affiliates',
    subtitle: 'Jasper, Copy.ai, Writesonic, Descript',
    monthlyMin: 1000,
    monthlyMax: 8000,
    difficulty: 'Easy',
    timeToFirstDollar: '2–5 days',
    description: 'AI writing and content tools have generous affiliate programs with 25–30% recurring commissions. Easy to pitch to any business that creates content.',
    steps: [
      'Sign up for all AI affiliate programs',
      'Prospector → search "content creator", "marketing director", "agency owner"',
      'Email: "The AI tool that writes better copy than our old copywriter"',
      'Campaigns → send to 500 content-producing businesses',
      'Track signups in each affiliate portal',
    ],
    programs: [
      { name: 'Jasper AI', ppl: '25% recurring', notes: '$39–$99/mo. 25% recurring forever.' },
      { name: 'Copy.ai', ppl: '30% recurring', notes: 'Free plan converts well. $49/mo paid.' },
      { name: 'Writesonic', ppl: '30% recurring', notes: '$19–$99/mo. Easy to promote.' },
      { name: 'Descript', ppl: '$25–$50 per signup', notes: 'Video/podcast AI. $12–$24/mo plans.' },
    ],
    revenueMath: '200 signups/mo across tools × $15 avg = $3,000/mo recurring AI affiliate income',
    canRace: false,
  },
  {
    id: 'agency',
    category: 'agency',
    title: 'Done-For-You Lead Gen Agency',
    subtitle: 'Sell lead gen as a managed service — $800–$6,000/mo retainers',
    monthlyMin: 5000,
    monthlyMax: 50000,
    difficulty: 'Medium',
    timeToFirstDollar: '1 week',
    description: 'Businesses need leads but don\'t have time to run outreach. You charge $800–$6,000/mo to run it for them using URAP. Cost: ~$200/mo tooling. Revenue: 5 clients × $2,000 = $10,000/mo.',
    steps: [
      'Pick a niche: HVAC, real estate, dental, insurance, roofing',
      'Prospector → search businesses in that niche across 10 cities',
      'Cold email: "I run outreach for HVAC companies — got 14 new clients for a Miami HVAC co last month"',
      'Pitch: $500 setup + $1,500/mo retainer — use URAP to deliver leads',
      'Use one URAP account for all clients (different contact lists per client)',
      'Upsell: add directory sites for passive lead flow',
    ],
    programs: [
      { name: 'Clutch.co', ppl: 'Inbound RFQs', notes: 'List your lead gen agency. Free.' },
      { name: 'DesignRush', ppl: 'Inbound RFQs', notes: 'Get RFQs from real businesses.' },
      { name: 'Bark.com', ppl: 'Leads $5–$20', notes: 'Buy leads, close $2k/mo contracts.' },
    ],
    revenueMath: '5 clients × $2,000/mo = $10,000/mo. Scale to 10 = $20,000/mo. Margin after URAP: $19,800/mo.',
    canRace: false,
  },
];

const CATEGORY_LABELS: Record<Category, string> = {
  all: 'All Methods',
  ppl: 'Pay Per Lead',
  directory: 'Directory Sites',
  saas: 'SaaS Affiliates',
  agency: 'Agency Model',
};

const CATEGORY_COLORS: Record<Category, string> = {
  all: 'text-gray-400',
  ppl: 'text-amber-400',
  directory: 'text-emerald-400',
  saas: 'text-violet-400',
  agency: 'text-sky-400',
};

const CATEGORY_BADGE: Record<Category, string> = {
  all: '',
  ppl: 'bg-amber-900/40 text-amber-300 border border-amber-800',
  directory: 'bg-emerald-900/40 text-emerald-300 border border-emerald-800',
  saas: 'bg-violet-900/40 text-violet-300 border border-violet-800',
  agency: 'bg-sky-900/40 text-sky-300 border border-sky-800',
};

function fmtMoney(n: number) {
  return n >= 1000 ? `$${(n / 1000).toFixed(0)}K` : `$${n}`;
}

function difficultyColor(d: string) {
  return d === 'Easy' ? 'text-emerald-400' : 'text-yellow-400';
}

function headers() {
  return { 'Content-Type': 'application/json', 'x-api-key': API_KEY, 'x-tenant-id': TENANT };
}

// ── Method Card ────────────────────────────────────────────────────────────────

interface MethodCardProps {
  method: IncomeMethod;
  onRace: (method: IncomeMethod) => void;
  racing: boolean;
}

function MethodCard({ method, onRace, racing }: MethodCardProps) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="rounded border border-gray-800 bg-gray-900 overflow-hidden">
      {/* Header — always visible */}
      <button
        onClick={() => setExpanded(e => !e)}
        className="w-full text-left px-4 py-3 flex items-start gap-3 hover:bg-gray-800/50 transition-colors"
      >
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap mb-0.5">
            <span className={`text-xs px-1.5 py-0.5 rounded font-medium ${CATEGORY_BADGE[method.category]}`}>
              {CATEGORY_LABELS[method.category]}
            </span>
            <span className={`text-xs ${difficultyColor(method.difficulty)}`}>{method.difficulty}</span>
            <span className="text-xs text-gray-500">{method.timeToFirstDollar} to first $</span>
          </div>
          <p className="text-sm font-semibold text-white">{method.title}</p>
          <p className="text-xs text-gray-500 mt-0.5">{method.subtitle}</p>
        </div>
        <div className="flex-shrink-0 text-right">
          <p className="text-sm font-bold text-amber-400">
            {fmtMoney(method.monthlyMin)}–{fmtMoney(method.monthlyMax)}
          </p>
          <p className="text-xs text-gray-600">/mo potential</p>
        </div>
        <span className="text-gray-600 text-xs mt-1">{expanded ? '▲' : '▼'}</span>
      </button>

      {/* Expanded body */}
      {expanded && (
        <div className="border-t border-gray-800 px-4 py-3 space-y-3">
          <p className="text-xs text-gray-400">{method.description}</p>

          {/* Steps */}
          <div>
            <p className="text-xs text-gray-500 font-medium uppercase tracking-wider mb-1">Setup</p>
            <ol className="space-y-1">
              {method.steps.map((step, i) => (
                <li key={i} className="flex gap-2 text-xs text-gray-400">
                  <span className="text-amber-600 font-medium flex-shrink-0">{i + 1}.</span>
                  <span>{step}</span>
                </li>
              ))}
            </ol>
          </div>

          {/* Programs table */}
          <div>
            <p className="text-xs text-gray-500 font-medium uppercase tracking-wider mb-1.5">Programs to Sign Up For</p>
            <div className="rounded border border-gray-800 overflow-hidden">
              <table className="w-full text-xs">
                <thead className="bg-gray-800">
                  <tr>
                    <th className="text-left px-2 py-1.5 text-gray-400 font-medium">Program</th>
                    <th className="text-left px-2 py-1.5 text-gray-400 font-medium">Pay Per Lead</th>
                    <th className="text-left px-2 py-1.5 text-gray-400 font-medium hidden sm:table-cell">Notes</th>
                  </tr>
                </thead>
                <tbody>
                  {method.programs.map((p, i) => (
                    <tr key={i} className={i % 2 === 0 ? 'bg-gray-900' : 'bg-gray-900/50'}>
                      <td className="px-2 py-1.5 text-white font-medium">{p.name}</td>
                      <td className="px-2 py-1.5 text-amber-400">{p.ppl}</td>
                      <td className="px-2 py-1.5 text-gray-500 hidden sm:table-cell">{p.notes}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Revenue math */}
          <div className="bg-amber-950/20 border border-amber-900/40 rounded px-3 py-2">
            <p className="text-xs text-gray-500 font-medium uppercase tracking-wider mb-0.5">Revenue Math</p>
            <p className="text-xs text-amber-300">{method.revenueMath}</p>
          </div>

          {/* CPL Race button for PPL methods */}
          {method.canRace && (
            <button
              onClick={() => onRace(method)}
              disabled={racing}
              className="w-full bg-amber-700 hover:bg-amber-600 disabled:opacity-40 text-white text-xs font-semibold rounded px-3 py-2 transition-colors"
            >
              {racing ? '⚡ Running CPL Auction…' : '⚡ Run CPL Race — Best Buyer Wins'}
            </button>
          )}
        </div>
      )}
    </div>
  );
}

// ── Main Page ──────────────────────────────────────────────────────────────────

export function Revenue() {
  const [category, setCategory] = useState<Category>('all');
  const [raceSummary, setRaceSummary] = useState<RaceSummary | null>(null);
  const [racingMethod, setRacingMethod] = useState<string | null>(null);
  const [lastRaceResult, setLastRaceResult] = useState<RaceResult | null>(null);
  const [loadingResults, setLoadingResults] = useState(true);

  useEffect(() => { fetchRaceResults(); }, []);

  async function fetchRaceResults() {
    setLoadingResults(true);
    try {
      const res = await fetch(`${ENGINE}/race/results`, { headers: headers() });
      const data: RaceSummary = await res.json();
      setRaceSummary(data);
    } catch {/* silent */} finally {
      setLoadingResults(false);
    }
  }

  async function handleRace(method: IncomeMethod) {
    setRacingMethod(method.id);
    setLastRaceResult(null);
    try {
      // Pull scored leads from LeadRouter's intent queue
      const leadsRes = await fetch(`${ENGINE}/outreach/intent/score`, {
        method: 'POST',
        headers: headers(),
        body: JSON.stringify({ limit: 10 }),
      });
      const leadsData = await leadsRes.json();
      const leads: unknown[] = leadsData.contacts || [];

      if (!leads.length) {
        alert('No scored leads available. Run Warp Mode or add contacts first.');
        return;
      }

      const res = await fetch(`${ENGINE}/race/run`, {
        method: 'POST',
        headers: headers(),
        body: JSON.stringify({ leads: leads.slice(0, 5), timeout: 5.0 }),
      });
      const data = await res.json();
      if (data.results?.length) setLastRaceResult(data.results[0]);
      await fetchRaceResults();
    } catch {/* silent */} finally {
      setRacingMethod(null);
    }
  }

  const filtered = category === 'all' ? METHODS : METHODS.filter(m => m.category === category);
  const totalMinPotential = METHODS.reduce((sum, m) => sum + m.monthlyMin, 0);
  const totalMaxPotential = METHODS.reduce((sum, m) => sum + m.monthlyMax, 0);

  return (
    <div className="flex flex-col md:flex-row gap-4 p-4 md:h-full overflow-auto md:overflow-hidden">
      {/* Left sidebar */}
      <div className="w-full md:w-72 md:flex-shrink-0 flex flex-col gap-3 md:overflow-auto">
        <div>
          <h2 className="text-sm font-semibold text-gray-200 uppercase tracking-wider">Revenue</h2>
          <p className="text-xs text-gray-500 mt-1">
            9 income methods. Stack them all for $27K–$133K/mo combined.
          </p>
        </div>

        {/* Stack potential card */}
        <div className="rounded border border-amber-900/50 bg-amber-950/20 px-4 py-3">
          <p className="text-xs text-gray-500 uppercase tracking-wider font-medium">Full Stack Potential</p>
          <p className="text-2xl font-bold text-amber-400 mt-1">
            {fmtMoney(totalMinPotential)}–{fmtMoney(totalMaxPotential)}
          </p>
          <p className="text-xs text-gray-500">/mo if all 9 methods running</p>
          <div className="mt-2 space-y-1 text-xs">
            <div className="flex justify-between">
              <span className="text-amber-400">Pay Per Lead</span>
              <span className="text-gray-400">$23K–$115K</span>
            </div>
            <div className="flex justify-between">
              <span className="text-emerald-400">Directory Sites</span>
              <span className="text-gray-400">$3K–$30K</span>
            </div>
            <div className="flex justify-between">
              <span className="text-violet-400">SaaS Affiliates</span>
              <span className="text-gray-400">$8K–$63K</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sky-400">Agency Model</span>
              <span className="text-gray-400">$5K–$50K</span>
            </div>
          </div>
        </div>

        {/* Race results */}
        {!loadingResults && raceSummary && (
          <div className="rounded border border-gray-800 bg-gray-900 px-4 py-3">
            <p className="text-xs text-gray-500 uppercase tracking-wider font-medium mb-2">CPL Auction Stats</p>
            <div className="grid grid-cols-3 gap-2 text-center">
              <div>
                <p className="text-lg font-bold text-white">{raceSummary.total_auctions}</p>
                <p className="text-xs text-gray-600">Auctions</p>
              </div>
              <div>
                <p className="text-lg font-bold text-emerald-400">{raceSummary.auctions_won}</p>
                <p className="text-xs text-gray-600">Won</p>
              </div>
              <div>
                <p className="text-lg font-bold text-amber-400">${raceSummary.total_earned.toFixed(0)}</p>
                <p className="text-xs text-gray-600">Earned</p>
              </div>
            </div>
          </div>
        )}

        {/* Last race result */}
        {lastRaceResult && (
          <div className={`rounded border px-3 py-2 text-xs space-y-1 ${lastRaceResult.dispatched ? 'border-emerald-800 bg-emerald-950/20' : 'border-red-800 bg-red-950/20'}`}>
            <p className="text-gray-400 font-medium uppercase tracking-wider">Last Auction</p>
            {lastRaceResult.dispatched ? (
              <>
                <p className="text-emerald-400">Winner: <span className="text-white font-medium">{lastRaceResult.winner_marketplace_name}</span></p>
                <p className="text-amber-400">CPL: <span className="text-white font-bold">${lastRaceResult.winning_cpl.toFixed(2)}</span></p>
                <p className="text-gray-500">Bids received: {lastRaceResult.all_bids.length}</p>
              </>
            ) : (
              <p className="text-red-400">{lastRaceResult.error || 'No bids received'}</p>
            )}
          </div>
        )}

        {/* Quick start */}
        <div className="rounded border border-gray-800 bg-gray-900/50 px-4 py-3 text-xs text-gray-500 space-y-2">
          <p className="text-gray-400 font-medium">Fastest Path to First $</p>
          <ol className="space-y-1">
            <li>1. Sign up EverQuote Publishers</li>
            <li>2. Sign up SmartFinancial</li>
            <li>3. Prospector → "restaurant" in your city → 100 contacts</li>
            <li>4. Email → insurance pitch</li>
            <li>5. Lead Router → paste EverQuote webhook</li>
            <li className="text-amber-500 font-medium">→ Earn $8–$60 per completed form</li>
          </ol>
        </div>
      </div>

      {/* Right panel */}
      <div className="flex-1 flex flex-col gap-3 overflow-auto">
        {/* Category filter */}
        <div className="flex gap-1 flex-wrap">
          {(Object.keys(CATEGORY_LABELS) as Category[]).map(cat => (
            <button
              key={cat}
              onClick={() => setCategory(cat)}
              className={`px-3 py-1.5 rounded text-xs font-medium transition-colors ${
                category === cat
                  ? 'bg-gray-700 text-white'
                  : 'text-gray-500 hover:text-gray-300'
              }`}
            >
              {CATEGORY_LABELS[cat]}
              {cat !== 'all' && (
                <span className={`ml-1 ${CATEGORY_COLORS[cat]}`}>
                  ({METHODS.filter(m => m.category === cat).length})
                </span>
              )}
            </button>
          ))}
        </div>

        {/* Method cards */}
        <div className="space-y-2">
          {filtered.map(method => (
            <MethodCard
              key={method.id}
              method={method}
              onRace={handleRace}
              racing={racingMethod === method.id}
            />
          ))}
        </div>

        {/* Recent auction log */}
        {!loadingResults && raceSummary && raceSummary.results.length > 0 && (
          <div className="rounded border border-gray-800 bg-gray-900 overflow-hidden">
            <div className="px-4 py-2 border-b border-gray-800">
              <p className="text-xs font-medium text-gray-400 uppercase tracking-wider">Recent CPL Auctions</p>
            </div>
            <table className="w-full text-xs">
              <thead className="bg-gray-800">
                <tr>
                  <th className="text-left px-3 py-1.5 text-gray-500 font-medium">Lead</th>
                  <th className="text-left px-3 py-1.5 text-gray-500 font-medium">Winner</th>
                  <th className="text-right px-3 py-1.5 text-gray-500 font-medium">CPL</th>
                  <th className="text-right px-3 py-1.5 text-gray-500 font-medium hidden sm:table-cell">Bids</th>
                  <th className="text-right px-3 py-1.5 text-gray-500 font-medium">Status</th>
                </tr>
              </thead>
              <tbody>
                {raceSummary.results.slice(0, 10).map(r => (
                  <tr key={r.auction_id} className="border-t border-gray-800/50 hover:bg-gray-800/30">
                    <td className="px-3 py-1.5 text-gray-400 font-mono">{r.lead_id.slice(0, 12)}…</td>
                    <td className="px-3 py-1.5 text-white">{r.winner_marketplace_name || '—'}</td>
                    <td className="px-3 py-1.5 text-amber-400 text-right">
                      {r.winning_cpl > 0 ? `$${r.winning_cpl.toFixed(2)}` : '—'}
                    </td>
                    <td className="px-3 py-1.5 text-gray-500 text-right hidden sm:table-cell">{r.all_bids?.length ?? 0}</td>
                    <td className="px-3 py-1.5 text-right">
                      {r.dispatched
                        ? <span className="text-emerald-400">✓ Dispatched</span>
                        : <span className="text-red-400">✗ {r.error?.slice(0, 20) || 'Failed'}</span>
                      }
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
