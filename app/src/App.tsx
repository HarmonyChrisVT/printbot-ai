import { useState, useEffect } from 'react';
import {
  Activity,
  Palette,
  DollarSign,
  Share2,
  Package,
  TrendingUp,
  AlertCircle,
  CheckCircle,
  PauseCircle,
  PlayCircle,
  Settings,
  Shield,
  Zap,
  Briefcase,
  FileText,
  Eye,
  BarChart2,
  MessageSquare,
  Users,
  Heart,
  Crown,
  ArrowRight,
  Network,
  Target,
  RefreshCw,
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Separator } from '@/components/ui/separator';
import { ScrollArea } from '@/components/ui/scroll-area';
import './App.css';

// Types
interface AgentStatus {
  name: string;
  running: boolean;
  lastActivity: string;
  stats: Record<string, number | string>;
}

interface SystemStatus {
  running: boolean;
  agents: Record<string, AgentStatus>;
  config: Record<string, boolean>;
  deadMansSwitch: {
    isPaused: boolean;
    lastCheckin: string;
    timeUntilPause: number;
  };
}

interface Analytics {
  today: {
    orders: number;
    revenue: number;
    profit: number;
    designs: number;
    posts: number;
  };
  week: {
    orders: number;
    revenue: number;
    profit: number;
  };
}

interface OrchestratorDecision {
  at: string;
  mode: string;
  mode_label?: string;
  strategy: string;
  mode_changed: boolean;
  metrics: Record<string, number>;
}

interface IntelligenceFlow {
  from: string;
  to: string;
  signal: string;
  at: string;
}

interface OrchestratorStatus {
  running: boolean;
  eval_count: number;
  last_eval_at: string | null;
  next_eval_in: number;
  mode: string;
  mode_label: string;
  mode_color: string;
  strategy: string;
  priority_queue: string[];
  metrics: {
    total_products: number;
    approved_products: number;
    pending_designs: number;
    orders_today: number;
    orders_week: number;
    revenue: number;
    fulfillment_backlog: number;
    social_posts_today: number;
  };
  agent_insights: Record<string, Record<string, any>>;
  agent_collaboration: Record<string, string>;
  intelligence_flows: IntelligenceFlow[];
  recent_decisions: OrchestratorDecision[];
}

// Mock data for demo
const mockSystemStatus: SystemStatus = {
  running: true,
  agents: {
    design: {
      name: 'Design Agent',
      running: true,
      lastActivity: '2 minutes ago',
      stats: { designsToday: 2, designsTotal: 47, pendingApproval: 1 }
    },
    pricing: {
      name: 'Pricing Agent',
      running: true,
      lastActivity: '15 minutes ago',
      stats: { productsUpdated: 12, avgMargin: 32.5 }
    },
    social: {
      name: 'Social Agent',
      running: true,
      lastActivity: '1 hour ago',
      stats: { postsToday: 3, followers: 1247, engagement: 4.2 }
    },
    fulfillment: {
      name: 'Fulfillment Agent',
      running: true,
      lastActivity: '30 seconds ago',
      stats: { ordersToday: 5, pendingOrders: 2, shippedToday: 3 }
    },
    b2b: {
      name: 'B2B Agent',
      running: true,
      lastActivity: '45 minutes ago',
      stats: { leadsContacted: 8, dealsActive: 3, quotesSent: 5 }
    },
    content_writer: {
      name: 'Content Writer Agent',
      running: true,
      lastActivity: '20 minutes ago',
      stats: { descriptionsWritten: 14, abTestsActive: 3 }
    },
    competitor_spy: {
      name: 'Competitor Spy Agent',
      running: true,
      lastActivity: '2 hours ago',
      stats: { competitorsTracked: 5, priceChanges: 7, alertsTriggered: 2 }
    },
    inventory_prediction: {
      name: 'Inventory Prediction Agent',
      running: true,
      lastActivity: '3 hours ago',
      stats: { productsAnalyzed: 32, restockAlerts: 4, forecastAccuracy: 87 }
    },
    customer_service: {
      name: 'Customer Service Chatbot',
      running: true,
      lastActivity: '5 minutes ago',
      stats: { ticketsHandled: 11, avgResponseTime: 42, satisfactionRate: 94 }
    },
    affiliate: {
      name: 'Affiliate Agent',
      running: true,
      lastActivity: '1 hour ago',
      stats: { affiliatesActive: 12, clicksToday: 340, commissionsEarned: 28 }
    },
    customer_engagement: {
      name: 'Customer Engagement Agent',
      running: true,
      lastActivity: '10 minutes ago',
      stats: { emailsSent: 45, openRate: 38, campaignsActive: 2 }
    }
  },
  config: {
    shopify: true,
    printful: true,
    openai: true
  },
  deadMansSwitch: {
    isPaused: false,
    lastCheckin: new Date().toISOString(),
    timeUntilPause: 82800
  }
};

const mockAnalytics: Analytics = {
  today: {
    orders: 5,
    revenue: 247.95,
    profit: 89.25,
    designs: 2,
    posts: 3
  },
  week: {
    orders: 34,
    revenue: 1684.50,
    profit: 589.75
  }
};

// Components
function AgentCard({ agent, icon: Icon, color }: { agent: AgentStatus; icon: any; color: string }) {
  return (
    <Card className="hover:shadow-lg transition-shadow">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className={`p-2 rounded-lg ${color}`}>
              <Icon className="w-5 h-5 text-white" />
            </div>
            <div>
              <CardTitle className="text-sm font-medium">{agent.name}</CardTitle>
              <CardDescription className="text-xs">{agent.lastActivity}</CardDescription>
            </div>
          </div>
          <Badge variant={agent.running ? "default" : "secondary"}>
            {agent.running ? 'Running' : 'Stopped'}
          </Badge>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          {Object.entries(agent.stats).map(([key, value]) => (
            <div key={key} className="flex justify-between text-sm">
              <span className="text-muted-foreground capitalize">
                {key.replace(/([A-Z])/g, ' $1').trim()}
              </span>
              <span className="font-medium">{value}</span>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

function StatCard({ title, value, change, icon: Icon }: { title: string; value: string; change?: string; icon: any }) {
  return (
    <Card>
      <CardContent className="p-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-muted-foreground">{title}</p>
            <p className="text-2xl font-bold mt-1">{value}</p>
            {change && (
              <p className="text-xs text-green-600 mt-1">{change}</p>
            )}
          </div>
          <div className="p-3 bg-primary/10 rounded-full">
            <Icon className="w-5 h-5 text-primary" />
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function ConfigStatus({ name, connected }: { name: string; connected: boolean }) {
  return (
    <div className="flex items-center justify-between py-2">
      <span className="text-sm">{name}</span>
      <Badge variant={connected ? "default" : "destructive"} className="gap-1">
        {connected ? <CheckCircle className="w-3 h-3" /> : <AlertCircle className="w-3 h-3" />}
        {connected ? 'Connected' : 'Not Configured'}
      </Badge>
    </div>
  );
}

function DeadMansSwitch({ status }: { status: SystemStatus['deadMansSwitch'] }) {
  const hours = Math.floor(status.timeUntilPause / 3600);
  const minutes = Math.floor((status.timeUntilPause % 3600) / 60);
  const progress = ((24 * 3600 - status.timeUntilPause) / (24 * 3600)) * 100;
  const [checkinState, setCheckinState] = useState<'idle' | 'loading' | 'success' | 'error'>('idle');

  async function handleCheckin() {
    setCheckinState('loading');
    try {
      const res = await fetch('/api/checkin', { method: 'POST' });
      if (res.ok) {
        setCheckinState('success');
        setTimeout(() => setCheckinState('idle'), 3000);
      } else {
        setCheckinState('error');
        setTimeout(() => setCheckinState('idle'), 3000);
      }
    } catch {
      setCheckinState('error');
      setTimeout(() => setCheckinState('idle'), 3000);
    }
  }

  return (
    <Card className={status.isPaused ? 'border-red-500' : ''}>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base">
          <Shield className="w-5 h-5" />
          Dead Man's Switch
        </CardTitle>
        <CardDescription>
          System will pause if you don't check in within 24 hours
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {status.isPaused ? (
          <Alert variant="destructive">
            <AlertCircle className="w-4 h-4" />
            <AlertDescription>
              System is PAUSED. Check in to resume operations.
            </AlertDescription>
          </Alert>
        ) : (
          <>
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">Time until pause</span>
                <span className="font-medium">{hours}h {minutes}m</span>
              </div>
              <Progress value={progress} className="h-2" />
            </div>
          </>
        )}
        {checkinState === 'success' && (
          <Alert className="border-green-500 text-green-700">
            <CheckCircle className="w-4 h-4" />
            <AlertDescription>Check-in recorded successfully.</AlertDescription>
          </Alert>
        )}
        {checkinState === 'error' && (
          <Alert variant="destructive">
            <AlertCircle className="w-4 h-4" />
            <AlertDescription>Check-in failed. Is the backend running?</AlertDescription>
          </Alert>
        )}
        <Button
          className="w-full"
          variant={checkinState === 'success' ? 'default' : 'outline'}
          disabled={checkinState === 'loading'}
          onClick={handleCheckin}
        >
          <CheckCircle className="w-4 h-4 mr-2" />
          {checkinState === 'loading' ? 'Checking in…' : checkinState === 'success' ? 'Checked In!' : 'Check In Now'}
        </Button>
      </CardContent>
    </Card>
  );
}

// ── Manual design trigger button ─────────────────────────────────────────────

function TriggerDesignButton({ disabled }: { disabled: boolean }) {
  const [state, setState] = useState<'idle' | 'loading' | 'ok' | 'err'>('idle');

  async function handleTrigger() {
    setState('loading');
    try {
      const res = await fetch('/api/trigger/design', { method: 'POST' });
      setState(res.ok ? 'ok' : 'err');
      setTimeout(() => setState('idle'), 8000);
    } catch {
      setState('err');
      setTimeout(() => setState('idle'), 8000);
    }
  }

  return (
    <div className="space-y-2">
      <Button className="w-full" onClick={handleTrigger}
        disabled={disabled || state === 'loading' || state === 'ok'}>
        <Zap className="w-4 h-4 mr-2" />
        {state === 'loading' ? 'Triggering…'
          : state === 'ok'  ? '✅ Triggered! Check Shopify in ~60s'
          : state === 'err' ? '❌ Failed — check backend logs'
          : 'Trigger Design Now'}
      </Button>
      {disabled && (
        <p className="text-xs text-muted-foreground text-center">
          Connect Shopify and OpenAI first.
        </p>
      )}
    </div>
  );
}

// ── Setup / credentials form ──────────────────────────────────────────────────

interface CfgStatus {
  shopify_shop_url: boolean;
  shopify_access_token: boolean;
  openai_api_key: boolean;
  printful_api_key: boolean;
  design_auto_approve: boolean;
}

function SetupForm({ onSaved }: { onSaved: () => void }) {
  const [form, setForm] = useState({
    shopify_shop_url: '',
    shopify_access_token: '',
    openai_api_key: '',
    printful_api_key: '',
    design_auto_approve: true,
  });
  const [show, setShow] = useState({ shopify: false, openai: false, printful: false });
  const [saving, setSaving] = useState(false);
  const [result, setResult] = useState<null | {
    status: string;
    shopify_test: { ok: boolean; shop_name: string | null; message: string } | null;
  }>(null);
  const [cfg, setCfg] = useState<CfgStatus | null>(null);

  useEffect(() => {
    fetch('/api/config/status')
      .then(r => r.ok ? r.json() : null)
      .then(data => {
        if (data) {
          setCfg(data);
          setForm(f => ({ ...f, design_auto_approve: data.design_auto_approve ?? true }));
        }
      })
      .catch(() => {});
  }, []);

  async function handleSave(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    setResult(null);
    try {
      const res = await fetch('/api/config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(form),
      });
      const data = await res.json();
      setResult(data);
      if (data.status === 'saved') {
        onSaved();
        fetch('/api/config/status').then(r => r.json()).then(setCfg).catch(() => {});
        setForm(f => ({ ...f, shopify_access_token: '', openai_api_key: '', printful_api_key: '' }));
      }
    } catch {
      setResult({ status: 'error', shopify_test: null });
    } finally {
      setSaving(false);
    }
  }

  const shopifyOk  = cfg?.shopify_shop_url && cfg?.shopify_access_token;
  const openaiOk   = cfg?.openai_api_key;
  const printfulOk = cfg?.printful_api_key;

  function Section({ ok, required, children }: { ok: boolean | undefined; required?: boolean; children: React.ReactNode }) {
    const border = ok ? 'border-green-300 bg-green-50/40' : required ? 'border-red-300 bg-red-50/40' : 'border-gray-200 bg-gray-50/30';
    return <div className={`space-y-3 p-4 rounded-lg border-2 ${border}`}>{children}</div>;
  }

  function FieldRow({ label, placeholder, value, onChange, showKey, note }: {
    label: string; placeholder: string; value: string;
    onChange: (v: string) => void; showKey: keyof typeof show; note?: string;
  }) {
    return (
      <div>
        <label className="text-xs font-medium text-muted-foreground block mb-1">{label}</label>
        <div className="flex gap-2">
          <input
            type={show[showKey] ? 'text' : 'password'}
            placeholder={placeholder}
            value={value}
            onChange={e => onChange(e.target.value)}
            className="flex-1 px-3 py-2 border rounded-md text-sm bg-background focus:outline-none focus:ring-2 focus:ring-ring"
          />
          <Button type="button" variant="outline" size="sm"
            onClick={() => setShow(s => ({ ...s, [showKey]: !s[showKey] }))}>
            {show[showKey] ? 'Hide' : 'Show'}
          </Button>
        </div>
        {note && <p className="text-xs text-muted-foreground mt-1">{note}</p>}
      </div>
    );
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center gap-3">
          <Settings className="w-5 h-5" />
          <CardTitle>Connect Your Services</CardTitle>
        </div>
        <CardDescription>
          Enter your credentials here — saved instantly to the server and take effect without restarting.
          Leave a field blank to keep the current value.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSave} className="space-y-4">

          {/* Shopify */}
          <Section ok={shopifyOk} required>
            <div className="flex items-center justify-between">
              <p className="font-semibold text-sm flex items-center gap-2"><Package className="w-4 h-4" /> Shopify</p>
              <Badge variant={shopifyOk ? 'default' : 'destructive'} className="text-xs">
                {shopifyOk ? '✓ Connected' : '✗ Not Connected'}
              </Badge>
            </div>
            <div>
              <label className="text-xs font-medium text-muted-foreground block mb-1">Store URL</label>
              <input
                type="text"
                placeholder={cfg?.shopify_shop_url ? 'already set — leave blank to keep' : 'your-store.myshopify.com'}
                value={form.shopify_shop_url}
                onChange={e => setForm(f => ({ ...f, shopify_shop_url: e.target.value }))}
                className="w-full px-3 py-2 border rounded-md text-sm bg-background focus:outline-none focus:ring-2 focus:ring-ring"
              />
              <p className="text-xs text-muted-foreground mt-1">No https:// prefix — just your-store.myshopify.com</p>
            </div>
            <FieldRow
              label="Admin API Token (shpat_...)"
              placeholder={cfg?.shopify_access_token ? '••••• already set — leave blank to keep' : 'shpat_xxxxxxxxxxxxxxxxxx'}
              value={form.shopify_access_token}
              onChange={v => setForm(f => ({ ...f, shopify_access_token: v }))}
              showKey="shopify"
              note="Shopify Admin → Settings → Apps → Develop apps → your app → API credentials → Reveal token"
            />
          </Section>

          {/* OpenAI */}
          <Section ok={openaiOk} required>
            <div className="flex items-center justify-between">
              <p className="font-semibold text-sm flex items-center gap-2"><Zap className="w-4 h-4" /> OpenAI</p>
              <Badge variant={openaiOk ? 'default' : 'destructive'} className="text-xs">
                {openaiOk ? '✓ Configured' : '✗ Not Set'}
              </Badge>
            </div>
            <FieldRow
              label="API Key"
              placeholder={cfg?.openai_api_key ? '••••• already set' : 'sk-...'}
              value={form.openai_api_key}
              onChange={v => setForm(f => ({ ...f, openai_api_key: v }))}
              showKey="openai"
            />
          </Section>

          {/* Printful */}
          <Section ok={printfulOk}>
            <div className="flex items-center justify-between">
              <p className="font-semibold text-sm flex items-center gap-2"><Package className="w-4 h-4" /> Printful</p>
              <Badge variant={printfulOk ? 'default' : 'secondary'} className="text-xs">
                {printfulOk ? '✓ Configured' : 'Optional'}
              </Badge>
            </div>
            <FieldRow
              label="API Key"
              placeholder={cfg?.printful_api_key ? '••••• already set' : 'Your Printful API key'}
              value={form.printful_api_key}
              onChange={v => setForm(f => ({ ...f, printful_api_key: v }))}
              showKey="printful"
            />
          </Section>

          {/* Auto-approve toggle */}
          <div className={`flex items-center justify-between p-4 rounded-lg border-2 ${
            form.design_auto_approve ? 'border-green-300 bg-green-50/40' : 'border-amber-300 bg-amber-50/40'
          }`}>
            <div className="flex-1 mr-4">
              <p className="font-semibold text-sm">Auto-Approve Designs → Shopify</p>
              <p className="text-xs text-muted-foreground mt-0.5">
                {form.design_auto_approve
                  ? 'Designs will automatically become live Shopify products.'
                  : '⚠️ Off — designs are created but will never reach your Shopify store.'}
              </p>
            </div>
            <button
              type="button"
              onClick={() => setForm(f => ({ ...f, design_auto_approve: !f.design_auto_approve }))}
              className={`relative inline-flex h-7 w-12 shrink-0 items-center rounded-full transition-colors ${
                form.design_auto_approve ? 'bg-green-500' : 'bg-gray-300'
              }`}
            >
              <span className={`inline-block h-5 w-5 transform rounded-full bg-white shadow transition-transform ${
                form.design_auto_approve ? 'translate-x-6' : 'translate-x-1'
              }`} />
            </button>
          </div>

          {/* Result */}
          {result && (
            <Alert className={result.shopify_test?.ok ? 'border-green-500 bg-green-50' : ''}>
              <AlertDescription className="text-sm">
                {result.status === 'saved' && result.shopify_test?.ok
                  ? `✅ Saved! Shopify connected — shop: "${result.shopify_test.shop_name}". Products will appear within 30 min.`
                  : result.status === 'saved' && result.shopify_test
                  ? `⚠️ Saved, but Shopify test failed: ${result.shopify_test.message} — double-check your token.`
                  : result.status === 'saved'
                  ? '✅ Credentials saved.'
                  : '❌ Could not save — is the backend running?'}
              </AlertDescription>
            </Alert>
          )}

          <Button type="submit" className="w-full" disabled={saving}>
            {saving ? 'Saving & Testing Connection…' : 'Save & Test Connection'}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}

// Agent definitions: icon, color, description, detail rows
const agentConfig: Record<string, {
  icon: any;
  color: string;
  description: string;
  details: { label: string; value: string }[];
}> = {
  design: {
    icon: Palette,
    color: 'bg-gradient-to-br from-pink-500 to-rose-500',
    description: 'Scans trends and generates AI designs every 30 minutes',
    details: [
      { label: 'Daily Limit', value: '2 / 3 designs' },
      { label: 'Trend Sources', value: '4 active' },
      { label: 'Auto-Approve', value: 'Off' },
      { label: 'Next Scan', value: '18 minutes' },
    ],
  },
  pricing: {
    icon: DollarSign,
    color: 'bg-gradient-to-br from-green-500 to-emerald-500',
    description: 'Monitors competitors and adjusts prices every 2 hours',
    details: [
      { label: 'Anchor Margin', value: '40%' },
      { label: 'Floor Margin', value: '25%' },
      { label: 'Competitors', value: '5 tracked' },
      { label: 'Charm Pricing', value: 'Enabled' },
    ],
  },
  social: {
    icon: Share2,
    color: 'bg-gradient-to-br from-blue-500 to-cyan-500',
    description: 'Manages Instagram & TikTok presence every 6 hours',
    details: [
      { label: 'Daily Actions', value: '45 / 100' },
      { label: 'Instagram Accounts', value: '3 configured' },
      { label: 'TikTok Accounts', value: '3 configured' },
      { label: 'Auto-Like', value: 'Enabled' },
    ],
  },
  fulfillment: {
    icon: Package,
    color: 'bg-gradient-to-br from-orange-500 to-amber-500',
    description: 'Processes orders via Printful every 5 minutes',
    details: [
      { label: 'Pending Orders', value: '2 orders' },
      { label: 'Provider', value: 'Printful' },
      { label: 'Backup', value: 'Printify' },
      { label: 'Auto-Tracking', value: 'Enabled' },
    ],
  },
  b2b: {
    icon: Briefcase,
    color: 'bg-gradient-to-br from-violet-500 to-purple-500',
    description: 'Identifies and contacts wholesale & bulk order leads',
    details: [
      { label: 'Leads Contacted', value: '8 today' },
      { label: 'Active Deals', value: '3 in progress' },
      { label: 'Min Order Qty', value: '10 units' },
      { label: 'Wholesale Discount', value: '20%' },
    ],
  },
  content_writer: {
    icon: FileText,
    color: 'bg-gradient-to-br from-teal-500 to-green-500',
    description: 'Generates SEO-optimized product titles and descriptions',
    details: [
      { label: 'Descriptions Written', value: '14 today' },
      { label: 'A/B Tests Active', value: '3 running' },
      { label: 'SEO Optimizer', value: 'Enabled' },
      { label: 'Model', value: 'GPT-4' },
    ],
  },
  competitor_spy: {
    icon: Eye,
    color: 'bg-gradient-to-br from-slate-500 to-gray-600',
    description: 'Tracks competitor pricing and product launches',
    details: [
      { label: 'Competitors Tracked', value: '5 stores' },
      { label: 'Price Changes', value: '7 today' },
      { label: 'Alerts Triggered', value: '2 today' },
      { label: 'Scan Interval', value: 'Every 2 hours' },
    ],
  },
  inventory_prediction: {
    icon: BarChart2,
    color: 'bg-gradient-to-br from-indigo-500 to-blue-600',
    description: 'Predicts stock needs and triggers restock alerts',
    details: [
      { label: 'Products Analyzed', value: '32 SKUs' },
      { label: 'Restock Alerts', value: '4 active' },
      { label: 'Forecast Accuracy', value: '87%' },
      { label: 'Lookback Window', value: '90 days' },
    ],
  },
  customer_service: {
    icon: MessageSquare,
    color: 'bg-gradient-to-br from-sky-500 to-blue-500',
    description: 'Handles customer inquiries and support tickets automatically',
    details: [
      { label: 'Tickets Handled', value: '11 today' },
      { label: 'Avg Response Time', value: '42 seconds' },
      { label: 'Satisfaction Rate', value: '94%' },
      { label: 'Escalations', value: '1 today' },
    ],
  },
  affiliate: {
    icon: Users,
    color: 'bg-gradient-to-br from-rose-500 to-pink-600',
    description: 'Manages affiliate partners and tracks commissions',
    details: [
      { label: 'Active Affiliates', value: '12 partners' },
      { label: 'Clicks Today', value: '340' },
      { label: 'Commissions Earned', value: '$28 today' },
      { label: 'Commission Rate', value: '10%' },
    ],
  },
  customer_engagement: {
    icon: Heart,
    color: 'bg-gradient-to-br from-fuchsia-500 to-pink-500',
    description: 'Runs email campaigns and re-engagement sequences',
    details: [
      { label: 'Emails Sent', value: '45 today' },
      { label: 'Open Rate', value: '38%' },
      { label: 'Active Campaigns', value: '2 running' },
      { label: 'Unsubscribe Rate', value: '0.4%' },
    ],
  },
};

// ── Master Orchestrator card ──────────────────────────────────────────────────

const MODE_STYLES: Record<string, { bg: string; border: string; badge: string }> = {
  design:      { bg: 'bg-blue-50',   border: 'border-blue-300',  badge: 'bg-blue-500' },
  sell:        { bg: 'bg-green-50',  border: 'border-green-300', badge: 'bg-green-500' },
  outreach:    { bg: 'bg-orange-50', border: 'border-orange-300',badge: 'bg-orange-500' },
  fulfillment: { bg: 'bg-red-50',    border: 'border-red-300',   badge: 'bg-red-500' },
};

function MasterOrchestratorCard({ orch }: { orch: OrchestratorStatus }) {
  const style = MODE_STYLES[orch.mode] ?? MODE_STYLES['sell'];
  const m = orch.metrics;

  return (
    <Card className={`border-2 ${style.border} ${style.bg}`}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between flex-wrap gap-2">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-gradient-to-br from-yellow-400 to-amber-500 rounded-xl shadow">
              <Crown className="w-5 h-5 text-white" />
            </div>
            <div>
              <CardTitle className="text-base">Master Orchestrator</CardTitle>
              <CardDescription className="text-xs">
                Boss agent · eval #{orch.eval_count}
                {orch.last_eval_at
                  ? ` · last run ${new Date(orch.last_eval_at).toLocaleTimeString()}`
                  : ''}
              </CardDescription>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <span className={`px-3 py-1 rounded-full text-white text-xs font-semibold ${style.badge}`}>
              {orch.mode_label ?? orch.mode.replace('_', ' ').toUpperCase()}
            </span>
            <Badge variant={orch.running ? 'default' : 'secondary'}>
              {orch.running ? 'Active' : 'Stopped'}
            </Badge>
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Strategy text */}
        <p className="text-sm text-foreground leading-snug">{orch.strategy}</p>

        {/* Key metrics row */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-center">
          {[
            { label: 'Products', value: m.approved_products },
            { label: 'Orders Today', value: m.orders_today },
            { label: 'Revenue', value: `$${(m.revenue ?? 0).toLocaleString()}` },
            { label: 'Backlog', value: m.fulfillment_backlog },
          ].map(({ label, value }) => (
            <div key={label} className="bg-white/60 rounded-lg p-2">
              <p className="text-xs text-muted-foreground">{label}</p>
              <p className="font-bold text-sm">{value}</p>
            </div>
          ))}
        </div>

        {/* Priority queue */}
        {orch.priority_queue.length > 0 && (
          <div>
            <p className="text-xs font-medium text-muted-foreground mb-1 flex items-center gap-1">
              <Target className="w-3 h-3" /> Today's Priority Order
            </p>
            <div className="flex flex-wrap gap-1">
              {orch.priority_queue.slice(0, 6).map((agent, i) => (
                <span
                  key={agent}
                  className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                    i === 0 ? 'bg-amber-500 text-white' :
                    i === 1 ? 'bg-amber-200 text-amber-900' :
                    'bg-muted text-muted-foreground'
                  }`}
                >
                  {i + 1}. {agent.replace('_', ' ')}
                </span>
              ))}
              {orch.priority_queue.length > 6 && (
                <span className="text-xs px-2 py-0.5 rounded-full bg-muted text-muted-foreground">
                  +{orch.priority_queue.length - 6} more
                </span>
              )}
            </div>
          </div>
        )}

        {/* Next eval countdown */}
        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          <RefreshCw className="w-3 h-3" />
          Next evaluation in {Math.ceil((orch.next_eval_in ?? 300) / 60)} min
        </div>
      </CardContent>
    </Card>
  );
}

// ── Agent Collaboration panel ─────────────────────────────────────────────────

function AgentCollaborationPanel({ orch }: { orch: OrchestratorStatus }) {
  const flows = orch.intelligence_flows ?? [];
  const collab = orch.agent_collaboration ?? {};

  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-center gap-2">
          <Network className="w-5 h-5 text-purple-500" />
          <CardTitle className="text-base">Agent Collaboration</CardTitle>
        </div>
        <CardDescription>Real-time intelligence flows between agents</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Intelligence flows */}
        {flows.length > 0 ? (
          <ScrollArea className="h-44">
            <div className="space-y-2">
              {flows.map((flow, i) => (
                <div key={i} className="flex items-start gap-2 p-2 rounded-lg bg-muted/50 text-sm">
                  <Badge variant="outline" className="text-xs shrink-0">{flow.from}</Badge>
                  <ArrowRight className="w-3 h-3 mt-0.5 shrink-0 text-muted-foreground" />
                  <Badge variant="outline" className="text-xs shrink-0">{flow.to}</Badge>
                  <span className="text-xs text-muted-foreground flex-1">{flow.signal}</span>
                  <span className="text-xs text-muted-foreground shrink-0">
                    {new Date(flow.at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </span>
                </div>
              ))}
            </div>
          </ScrollArea>
        ) : (
          <p className="text-sm text-muted-foreground">
            Intelligence flows will appear here as agents share data.
          </p>
        )}

        {/* Current agent tasks */}
        {Object.keys(collab).length > 0 && (
          <>
            <Separator />
            <div>
              <p className="text-xs font-medium text-muted-foreground mb-2">Current Agent Tasks</p>
              <div className="space-y-1">
                {Object.entries(collab).slice(0, 6).map(([agent, task]) => (
                  <div key={agent} className="flex items-start gap-2 text-xs">
                    <span className="font-medium capitalize shrink-0 w-24">
                      {agent.replace('_', ' ')}
                    </span>
                    <span className="text-muted-foreground">{task}</span>
                  </div>
                ))}
              </div>
            </div>
          </>
        )}
      </CardContent>
    </Card>
  );
}

// ── Recent decisions log ──────────────────────────────────────────────────────

function OrchestratorDecisionsLog({ decisions }: { decisions: OrchestratorDecision[] }) {
  if (!decisions.length) return null;
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm flex items-center gap-2">
          <Crown className="w-4 h-4 text-amber-500" />
          Orchestrator Decision Log
        </CardTitle>
      </CardHeader>
      <CardContent>
        <ScrollArea className="h-48">
          <div className="space-y-2">
            {decisions.map((d, i) => (
              <div key={i} className="flex items-start gap-2 p-2 rounded-lg hover:bg-muted text-sm">
                <div className={`w-2 h-2 rounded-full mt-1.5 shrink-0 ${
                  d.mode_changed ? 'bg-amber-500' : 'bg-green-500'
                }`} />
                <span className="text-xs text-muted-foreground w-20 shrink-0">
                  {new Date(d.at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </span>
                <Badge variant="outline" className="text-xs shrink-0">
                  {(d.mode_label ?? d.mode).replace('_', ' ')}
                </Badge>
                <span className="text-xs">{d.strategy}</span>
              </div>
            ))}
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  );
}

function mapApiStatus(data: any): SystemStatus {
  // Map snake_case API response to camelCase frontend types,
  // merging with mock data so agents without live stats still render.
  const agents = { ...mockSystemStatus.agents };
  if (data.agents) {
    for (const [key, val] of Object.entries(data.agents as Record<string, any>)) {
      if (agents[key]) {
        agents[key] = { ...agents[key], running: val.running ?? agents[key].running };
      }
    }
  }
  const dms = data.dead_mans_switch ?? data.deadMansSwitch ?? {};
  return {
    running: data.running ?? mockSystemStatus.running,
    agents,
    config: {
      shopify:  data.config?.shopify  ?? false,
      printful: data.config?.printful ?? false,
      openai:   data.config?.openai   ?? false,
    },
    deadMansSwitch: {
      isPaused:       dms.is_paused       ?? dms.isPaused       ?? false,
      lastCheckin:    dms.last_checkin    ?? dms.lastCheckin    ?? new Date().toISOString(),
      timeUntilPause: dms.time_until_pause ?? dms.timeUntilPause ?? 82800,
    },
  };
}

const defaultOrchestrator: OrchestratorStatus = {
  running: false,
  eval_count: 0,
  last_eval_at: null,
  next_eval_in: 300,
  mode: 'design',
  mode_label: 'Design & Build',
  mode_color: 'blue',
  strategy: 'Master Orchestrator connecting…',
  priority_queue: [],
  metrics: {
    total_products: 0, approved_products: 0, pending_designs: 0,
    orders_today: 0, orders_week: 0, revenue: 0,
    fulfillment_backlog: 0, social_posts_today: 0,
  },
  agent_insights: {},
  agent_collaboration: {},
  intelligence_flows: [],
  recent_decisions: [],
};

function App() {
  const [status, setStatus] = useState<SystemStatus>(mockSystemStatus);
  const [analytics, setAnalytics] = useState<Analytics>(mockAnalytics);
  const [orchestrator, setOrchestrator] = useState<OrchestratorStatus>(defaultOrchestrator);
  const [activeTab, setActiveTab] = useState('dashboard');
  const [apiConnected, setApiConnected] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [statusRes, analyticsRes, orchRes] = await Promise.all([
          fetch('/api/status'),
          fetch('/api/analytics'),
          fetch('/api/orchestrator'),
        ]);
        if (statusRes.ok) {
          const data = await statusRes.json();
          setStatus(mapApiStatus(data));
          setApiConnected(true);
        } else {
          setApiConnected(false);
        }
        if (analyticsRes.ok) {
          const data = await analyticsRes.json();
          setAnalytics(prev => ({
            today: { ...prev.today, ...(data.today ?? {}) },
            week:  { ...prev.week,  ...(data.week  ?? {}) },
          }));
        }
        if (orchRes.ok) {
          const data = await orchRes.json();
          if (!data.error) setOrchestrator(data as OrchestratorStatus);
        }
      } catch {
        setApiConnected(false);
      }
    };
    fetchData();
    const interval = setInterval(fetchData, 5000);
    return () => clearInterval(interval);
  }, []);

  const agentKeys = Object.keys(agentConfig);

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b bg-card">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-gradient-to-br from-purple-500 to-pink-500 rounded-xl">
                <Zap className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold">PrintBot AI</h1>
                <p className="text-xs text-muted-foreground">Automated Print-on-Demand System</p>
              </div>
            </div>
            <div className="flex items-center gap-3 flex-wrap">
              {/* Priority mode pill from Master Orchestrator */}
              <span className={`hidden sm:flex items-center gap-1.5 px-3 py-1 rounded-full text-white text-xs font-semibold ${
                { design: 'bg-blue-500', sell: 'bg-green-500', outreach: 'bg-orange-500', fulfillment: 'bg-red-500' }[orchestrator.mode] ?? 'bg-purple-500'
              }`}>
                <Crown className="w-3 h-3" />
                {orchestrator.mode_label ?? orchestrator.mode.replace('_', ' ').toUpperCase()}
              </span>
              <Badge variant={status.running ? "default" : "secondary"} className="gap-1">
                {status.running ? <PlayCircle className="w-3 h-3" /> : <PauseCircle className="w-3 h-3" />}
                {status.running ? 'System Active' : 'System Paused'}
              </Badge>
              <Button variant="outline" size="sm">
                <Settings className="w-4 h-4 mr-2" />
                Settings
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* Backend status banner */}
      {!apiConnected && (
        <div className="bg-red-50 border-b border-red-200 px-4 py-2">
          <div className="container mx-auto flex items-center gap-2 text-red-700 text-sm">
            <AlertCircle className="w-4 h-4 shrink-0" />
            Backend API is unreachable — showing last known data. Start the Python server to connect.
          </div>
        </div>
      )}

      {/* Setup required banner */}
      {apiConnected && !status.config.shopify && (
        <div className="bg-amber-50 border-b border-amber-300 px-4 py-2">
          <div className="container mx-auto flex items-center gap-2 text-amber-800 text-sm">
            <AlertCircle className="w-4 h-4 shrink-0" />
            Shopify is not connected — no products will be created until you add your credentials.{' '}
            <button
              onClick={() => setActiveTab('config')}
              className="font-semibold underline hover:no-underline ml-1"
            >
              Go to Configuration →
            </button>
          </div>
        </div>
      )}

      {/* Main Content */}
      <main className="container mx-auto px-4 py-6">
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="mb-6">
            <TabsTrigger value="dashboard">Dashboard</TabsTrigger>
            <TabsTrigger value="orchestrator" className="gap-1">
              <Crown className="w-3 h-3" /> Orchestrator
            </TabsTrigger>
            <TabsTrigger value="agents">Agents</TabsTrigger>
            <TabsTrigger value="analytics">Analytics</TabsTrigger>
            <TabsTrigger value="config">Configuration</TabsTrigger>
          </TabsList>

          {/* Dashboard Tab */}
          <TabsContent value="dashboard" className="space-y-6">
            {/* Master Orchestrator summary card */}
            <MasterOrchestratorCard orch={orchestrator} />

            {/* Stats Row */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <StatCard
                title="Today's Revenue"
                value={`$${analytics.today.revenue.toFixed(2)}`}
                change="+12% from yesterday"
                icon={DollarSign}
              />
              <StatCard
                title="Today's Orders"
                value={analytics.today.orders.toString()}
                change="+3 new today"
                icon={Package}
              />
              <StatCard
                title="Today's Profit"
                value={`$${analytics.today.profit.toFixed(2)}`}
                icon={TrendingUp}
              />
              <StatCard
                title="Active Agents"
                value={Object.values(status.agents).filter(a => a.running).length.toString()}
                icon={Activity}
              />
            </div>

            {/* Agents Grid — all 11 */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {agentKeys.map((key) => {
                const agent = status.agents[key];
                const cfg = agentConfig[key];
                if (!agent || !cfg) return null;
                return (
                  <AgentCard
                    key={key}
                    agent={agent}
                    icon={cfg.icon}
                    color={cfg.color}
                  />
                );
              })}
            </div>

            {/* Agent Collaboration */}
            <AgentCollaborationPanel orch={orchestrator} />

            {/* Dead Man's Switch */}
            <DeadMansSwitch status={status.deadMansSwitch} />
          </TabsContent>

          {/* Orchestrator Tab */}
          <TabsContent value="orchestrator" className="space-y-6">
            <MasterOrchestratorCard orch={orchestrator} />
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <AgentCollaborationPanel orch={orchestrator} />
              <OrchestratorDecisionsLog decisions={orchestrator.recent_decisions} />
            </div>
            {/* Full agent task breakdown */}
            {Object.keys(orchestrator.agent_collaboration).length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle className="text-base flex items-center gap-2">
                    <Activity className="w-4 h-4" /> All Agent Assignments
                  </CardTitle>
                  <CardDescription>
                    What each agent is doing right now under{' '}
                    <strong>{orchestrator.mode_label}</strong> mode
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                    {Object.entries(orchestrator.agent_collaboration).map(([agent, task]) => (
                      <div key={agent} className="p-3 rounded-lg border bg-muted/30">
                        <p className="font-medium text-sm capitalize mb-1">
                          {agent.replace(/_/g, ' ')}
                        </p>
                        <p className="text-xs text-muted-foreground">{task}</p>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}
          </TabsContent>

          {/* Agents Tab */}
          <TabsContent value="agents" className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {agentKeys.map((key) => {
                const agent = status.agents[key];
                const cfg = agentConfig[key];
                if (!agent || !cfg) return null;
                const Icon = cfg.icon;
                return (
                  <Card key={key}>
                    <CardHeader>
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <div className={`p-2 rounded-lg ${cfg.color}`}>
                            <Icon className="w-4 h-4 text-white" />
                          </div>
                          <CardTitle className="text-base">{agent.name}</CardTitle>
                        </div>
                        <Badge variant={agent.running ? "default" : "secondary"}>
                          {agent.running ? 'Running' : 'Stopped'}
                        </Badge>
                      </div>
                      <CardDescription>{cfg.description}</CardDescription>
                    </CardHeader>
                    <CardContent>
                      <div className="grid grid-cols-2 gap-3 text-sm">
                        {cfg.details.map((d) => (
                          <div key={d.label}>
                            <p className="text-muted-foreground">{d.label}</p>
                            <p className="font-medium">{d.value}</p>
                          </div>
                        ))}
                      </div>
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          </TabsContent>

          {/* Analytics Tab */}
          <TabsContent value="analytics" className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">This Week</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Orders</span>
                      <span className="font-medium">{analytics.week.orders}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Revenue</span>
                      <span className="font-medium">${analytics.week.revenue.toFixed(2)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Profit</span>
                      <span className="font-medium text-green-600">${analytics.week.profit.toFixed(2)}</span>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Today's Activity</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">New Designs</span>
                      <span className="font-medium">{analytics.today.designs}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Social Posts</span>
                      <span className="font-medium">{analytics.today.posts}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Orders</span>
                      <span className="font-medium">{analytics.today.orders}</span>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Key Metrics</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Avg Order Value</span>
                      <span className="font-medium">$49.59</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Profit Margin</span>
                      <span className="font-medium">36%</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Engagement Rate</span>
                      <span className="font-medium">4.2%</span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>

            <Card>
              <CardHeader>
                <CardTitle>Recent Activity Log</CardTitle>
              </CardHeader>
              <CardContent>
                <ScrollArea className="h-64">
                  <div className="space-y-2">
                    {[
                      { time: '2 min ago', agent: 'Design', action: 'Generated design: "Monday Motivation"', status: 'success' },
                      { time: '5 min ago', agent: 'Customer Service', action: 'Resolved ticket #482: shipping inquiry', status: 'success' },
                      { time: '5 min ago', agent: 'Fulfillment', action: 'Order #1024 shipped', status: 'success' },
                      { time: '10 min ago', agent: 'Engagement', action: 'Sent re-engagement campaign to 45 customers', status: 'success' },
                      { time: '15 min ago', agent: 'Pricing', action: 'Updated 12 product prices', status: 'success' },
                      { time: '20 min ago', agent: 'Content Writer', action: 'Wrote descriptions for 14 products', status: 'success' },
                      { time: '45 min ago', agent: 'B2B', action: 'Contacted 8 wholesale leads', status: 'success' },
                      { time: '1 hour ago', agent: 'Social', action: 'Posted to Instagram @printbot_main', status: 'success' },
                      { time: '1 hour ago', agent: 'Affiliate', action: '340 affiliate clicks tracked', status: 'success' },
                      { time: '2 hours ago', agent: 'Competitor Spy', action: '7 competitor price changes detected', status: 'success' },
                      { time: '3 hours ago', agent: 'Inventory', action: '4 restock alerts triggered', status: 'success' },
                    ].map((log, i) => (
                      <div key={i} className="flex items-center gap-3 p-2 rounded-lg hover:bg-muted">
                        <div className={`w-2 h-2 rounded-full ${log.status === 'success' ? 'bg-green-500' : 'bg-red-500'}`} />
                        <span className="text-xs text-muted-foreground w-20 shrink-0">{log.time}</span>
                        <Badge variant="outline" className="text-xs shrink-0">{log.agent}</Badge>
                        <span className="text-sm">{log.action}</span>
                      </div>
                    ))}
                  </div>
                </ScrollArea>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Configuration Tab */}
          <TabsContent value="config" className="space-y-6">
            <SetupForm onSaved={() => {
              // Re-fetch status so the header badges update immediately
              fetch('/api/status').then(r => r.ok ? r.json() : null).then(data => {
                if (data) setStatus(mapApiStatus(data));
              }).catch(() => {});
            }} />

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Quick-trigger card */}
              <Card>
                <CardHeader>
                  <div className="flex items-center gap-3">
                    <Zap className="w-5 h-5" />
                    <CardTitle>Test the Pipeline</CardTitle>
                  </div>
                  <CardDescription>
                    Manually trigger one full design → approve → Shopify product cycle right now.
                    Check your Shopify Products page after ~60 seconds.
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-3">
                  <ConfigStatus name="Shopify Store"  connected={status.config.shopify} />
                  <Separator />
                  <ConfigStatus name="OpenAI"         connected={status.config.openai} />
                  <Separator />
                  <ConfigStatus name="Printful"       connected={status.config.printful} />
                  <Separator />
                  <TriggerDesignButton disabled={!status.config.shopify || !status.config.openai} />
                </CardContent>
              </Card>

              {/* Backup & Security */}
              <Card>
                <CardHeader>
                  <div className="flex items-center gap-3">
                    <Shield className="w-5 h-5" />
                    <CardTitle>Backup & Security</CardTitle>
                  </div>
                  <CardDescription>
                    Automated backups and system protection
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-medium">Weekly Backups</p>
                      <p className="text-sm text-muted-foreground">Every Sunday at 2 AM</p>
                    </div>
                    <Badge>Enabled</Badge>
                  </div>
                  <Separator />
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-medium">Cloud Upload</p>
                      <p className="text-sm text-muted-foreground">Google Drive</p>
                    </div>
                    <Badge variant="secondary">Not Configured</Badge>
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>
        </Tabs>
      </main>
    </div>
  );
}

export default App;
