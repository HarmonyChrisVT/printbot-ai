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
  Database,
  Shield,
  Zap,
  Briefcase,
  FileText,
  Eye,
  BarChart2,
  MessageSquare,
  Users,
  Heart,
  ShoppingCart,
  Megaphone,
  Star
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
  avgOrderValue: number;
  avgMargin: number;
}

interface LogEntry {
  id: number;
  agent: string;
  action: string;
  status: string;
  details: Record<string, unknown>;
  createdAt: string;
}

// Initial empty state (zeros) — replaced by real API data on load
const emptyStatus: SystemStatus = {
  running: false,
  agents: {
    design:               { name: 'Design Agent',               running: false, lastActivity: '—', stats: { designsToday: 0, designsTotal: 0, pendingApproval: 0, productsCreated: 0 } },
    pricing:              { name: 'Pricing Agent',              running: false, lastActivity: '—', stats: { productsActive: 0, updatedToday: 0, avgMargin: 0 } },
    social:               { name: 'Social Agent',               running: false, lastActivity: '—', stats: { postsToday: 0, postsTotal: 0, actionsToday: 0 } },
    fulfillment:          { name: 'Fulfillment Agent',          running: false, lastActivity: '—', stats: { ordersToday: 0, pendingOrders: 0, shippedToday: 0 } },
    b2b:                  { name: 'B2B Agent',                  running: false, lastActivity: '—', stats: { actionsToday: 0, leadsToday: 0, quotesToday: 0 } },
    content_writer:       { name: 'Content Writer Agent',       running: false, lastActivity: '—', stats: { writtenToday: 0, writtenTotal: 0 } },
    competitor_spy:       { name: 'Competitor Spy Agent',       running: false, lastActivity: '—', stats: { competitorsTracked: 0, priceChangesToday: 0, alertsToday: 0 } },
    inventory_prediction: { name: 'Inventory Prediction Agent', running: false, lastActivity: '—', stats: { productsTracked: 0, alertsToday: 0, alertsTotal: 0 } },
    customer_service:     { name: 'Customer Service Chatbot',   running: false, lastActivity: '—', stats: { handledToday: 0, handledTotal: 0 } },
    affiliate:            { name: 'Affiliate Agent',            running: false, lastActivity: '—', stats: { actionsToday: 0, actionsTotal: 0 } },
    customer_engagement:  { name: 'Customer Engagement Agent',  running: false, lastActivity: '—', stats: { emailsToday: 0, emailsTotal: 0 } },
    conversion:           { name: 'Conversion Agent',           running: false, lastActivity: '—', stats: { emailsToday: 0, emailsTotal: 0 } },
    outreach:             { name: 'Outreach Agent',             running: false, lastActivity: '—', stats: { engagedToday: 0, engagedTotal: 0, subredditsMonitored: 10 } },
    influencer:           { name: 'Influencer Agent',           running: false, lastActivity: '—', stats: { total_identified: 0, queued: 0, contacted: 0, responded: 0, converted: 0 } },
  },
  config: { shopify: false, printful: false, openai: false },
  deadMansSwitch: { isPaused: false, lastCheckin: new Date().toISOString(), timeUntilPause: 86400 },
};

const emptyAnalytics: Analytics = {
  today: { orders: 0, revenue: 0, profit: 0, designs: 0, posts: 0 },
  week:  { orders: 0, revenue: 0, profit: 0 },
  avgOrderValue: 0,
  avgMargin: 0,
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
                {key.replace(/([A-Z])/g, ' $1').replace(/_/g, ' ').trim()}
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

// Agent definitions: icon, color, description, static config values only (no fake stats)
const agentConfig: Record<string, {
  icon: any;
  color: string;
  description: string;
  config: { label: string; value: string }[];
}> = {
  design: {
    icon: Palette,
    color: 'bg-gradient-to-br from-pink-500 to-rose-500',
    description: 'Scans trends and generates AI designs every 30 minutes',
    config: [
      { label: 'Daily Limit', value: '3 designs' },
      { label: 'Trend Sources', value: '4 active' },
      { label: 'Auto-Approve', value: 'Enabled' },
      { label: 'Interval', value: '30 minutes' },
    ],
  },
  pricing: {
    icon: DollarSign,
    color: 'bg-gradient-to-br from-green-500 to-emerald-500',
    description: 'Monitors competitors and adjusts prices every 2 hours',
    config: [
      { label: 'Anchor Margin', value: '40%' },
      { label: 'Floor Margin', value: '25%' },
      { label: 'Charm Pricing', value: 'Enabled' },
      { label: 'Interval', value: 'Every 2 hours' },
    ],
  },
  social: {
    icon: Share2,
    color: 'bg-gradient-to-br from-blue-500 to-cyan-500',
    description: 'Manages Instagram & TikTok presence every 6 hours',
    config: [
      { label: 'Instagram Accounts', value: '3 configured' },
      { label: 'TikTok Accounts', value: '3 configured' },
      { label: 'Auto-Like', value: 'Enabled' },
      { label: 'Daily Action Limit', value: '100 actions' },
    ],
  },
  fulfillment: {
    icon: Package,
    color: 'bg-gradient-to-br from-orange-500 to-amber-500',
    description: 'Processes orders via Printful every 5 minutes',
    config: [
      { label: 'Provider', value: 'Printful' },
      { label: 'Backup', value: 'Printify' },
      { label: 'Auto-Tracking', value: 'Enabled' },
      { label: 'Interval', value: 'Every 5 min' },
    ],
  },
  b2b: {
    icon: Briefcase,
    color: 'bg-gradient-to-br from-violet-500 to-purple-500',
    description: 'Identifies and contacts wholesale & bulk order leads',
    config: [
      { label: 'Min Order Qty', value: '10 units' },
      { label: 'Wholesale Discount', value: '20%' },
      { label: 'Interval', value: 'Every 4 hours' },
    ],
  },
  content_writer: {
    icon: FileText,
    color: 'bg-gradient-to-br from-teal-500 to-green-500',
    description: 'Generates SEO-optimized product titles and descriptions',
    config: [
      { label: 'SEO Optimizer', value: 'Enabled' },
      { label: 'Model', value: 'GPT-4' },
      { label: 'Interval', value: 'Every 5 min' },
    ],
  },
  competitor_spy: {
    icon: Eye,
    color: 'bg-gradient-to-br from-slate-500 to-gray-600',
    description: 'Tracks competitor pricing and product launches',
    config: [
      { label: 'Scan Interval', value: 'Every 2 hours' },
    ],
  },
  inventory_prediction: {
    icon: BarChart2,
    color: 'bg-gradient-to-br from-indigo-500 to-blue-600',
    description: 'Predicts stock needs and triggers restock alerts',
    config: [
      { label: 'Lookback Window', value: '90 days' },
      { label: 'Interval', value: 'Every 6 hours' },
    ],
  },
  customer_service: {
    icon: MessageSquare,
    color: 'bg-gradient-to-br from-sky-500 to-blue-500',
    description: 'Handles customer inquiries and support tickets automatically',
    config: [
      { label: 'Model', value: 'GPT-4' },
      { label: 'Auto-Respond', value: 'Enabled' },
    ],
  },
  affiliate: {
    icon: Users,
    color: 'bg-gradient-to-br from-rose-500 to-pink-600',
    description: 'Manages affiliate partners and tracks commissions',
    config: [
      { label: 'Commission Rate', value: '10%' },
      { label: 'Interval', value: 'Every hour' },
    ],
  },
  customer_engagement: {
    icon: Heart,
    color: 'bg-gradient-to-br from-fuchsia-500 to-pink-500',
    description: 'Runs email campaigns and re-engagement sequences',
    config: [
      { label: 'Auto-Campaigns', value: 'Enabled' },
      { label: 'Unsubscribe Target', value: '< 0.5%' },
    ],
  },
  conversion: {
    icon: ShoppingCart,
    color: 'bg-gradient-to-br from-orange-600 to-red-500',
    description: 'Recovers abandoned carts with escalating discounts (10% → 15% → 20%)',
    config: [
      { label: '1hr Trigger', value: '10% off code' },
      { label: '24hr Trigger', value: '15% off code' },
      { label: '72hr Trigger', value: '20% off — final' },
      { label: 'Check Interval', value: 'Every 15 min' },
    ],
  },
  outreach: {
    icon: Megaphone,
    color: 'bg-gradient-to-br from-cyan-600 to-blue-600',
    description: 'Finds buying-intent posts on Reddit & forums and engages naturally',
    config: [
      { label: 'Subreddits', value: '10 monitored' },
      { label: 'Intent Keywords', value: '18 tracked' },
      { label: 'Max / Cycle', value: '8 engagements' },
      { label: 'Cooldown', value: 'Every 3 hours' },
    ],
  },
  influencer: {
    icon: Star,
    color: 'bg-gradient-to-br from-yellow-500 to-amber-600',
    description: 'Identifies micro-influencers (1K–100K) and queues collab DMs',
    config: [
      { label: 'Follower Range', value: '1K – 100K' },
      { label: 'Min Engagement', value: '2%' },
      { label: 'Offer', value: 'Free product' },
      { label: 'Hashtags Scanned', value: '18 niches' },
    ],
  },
};

function formatLogTime(isoString: string): string {
  const diff = (Date.now() - new Date(isoString).getTime()) / 1000;
  if (diff < 60) return `${Math.floor(diff)}s ago`;
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
  return `${Math.floor(diff / 86400)}d ago`;
}

function App() {
  const [status, setStatus] = useState<SystemStatus>(emptyStatus);
  const [analytics, setAnalytics] = useState<Analytics>(emptyAnalytics);
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [activeTab, setActiveTab] = useState('dashboard');

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [statusRes, analyticsRes, logsRes] = await Promise.all([
          fetch('/api/status'),
          fetch('/api/analytics'),
          fetch('/api/logs?limit=50'),
        ]);
        if (statusRes.ok) setStatus(await statusRes.json());
        if (analyticsRes.ok) setAnalytics(await analyticsRes.json());
        if (logsRes.ok) {
          const data = await logsRes.json();
          setLogs(data.logs || []);
        }
      } catch (e) {
        console.error('Failed to fetch status:', e);
      }
    };
    fetchData();
    const interval = setInterval(fetchData, 30000);
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
            <div className="flex items-center gap-4">
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

      {/* Main Content */}
      <main className="container mx-auto px-4 py-6">
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="mb-6">
            <TabsTrigger value="dashboard">Dashboard</TabsTrigger>
            <TabsTrigger value="agents">Agents</TabsTrigger>
            <TabsTrigger value="analytics">Analytics</TabsTrigger>
            <TabsTrigger value="config">Configuration</TabsTrigger>
          </TabsList>

          {/* Dashboard Tab */}
          <TabsContent value="dashboard" className="space-y-6">
            {/* Stats Row */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <StatCard
                title="Today's Revenue"
                value={`$${analytics.today.revenue.toFixed(2)}`}
                icon={DollarSign}
              />
              <StatCard
                title="Today's Orders"
                value={analytics.today.orders.toString()}
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

            {/* Agents Grid */}
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

            {/* Dead Man's Switch */}
            <DeadMansSwitch status={status.deadMansSwitch} />
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
                    <CardContent className="space-y-4">
                      {/* Live stats from API */}
                      <div>
                        <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-2">Live Stats</p>
                        <div className="grid grid-cols-2 gap-2 text-sm">
                          {Object.entries(agent.stats).map(([key, value]) => (
                            <div key={key}>
                              <p className="text-muted-foreground capitalize">
                                {key.replace(/([A-Z])/g, ' $1').replace(/_/g, ' ').trim()}
                              </p>
                              <p className="font-medium">{value}</p>
                            </div>
                          ))}
                        </div>
                      </div>
                      {/* Static configuration */}
                      {cfg.config.length > 0 && (
                        <>
                          <Separator />
                          <div>
                            <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-2">Configuration</p>
                            <div className="grid grid-cols-2 gap-2 text-sm">
                              {cfg.config.map((d) => (
                                <div key={d.label}>
                                  <p className="text-muted-foreground">{d.label}</p>
                                  <p className="font-medium">{d.value}</p>
                                </div>
                              ))}
                            </div>
                          </div>
                        </>
                      )}
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
                      <span className="font-medium">${analytics.avgOrderValue.toFixed(2)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Avg Profit Margin</span>
                      <span className="font-medium">
                        {analytics.avgMargin > 0 ? `${analytics.avgMargin}%` : '—'}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Week Revenue</span>
                      <span className="font-medium">${analytics.week.revenue.toFixed(2)}</span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>

            <Card>
              <CardHeader>
                <CardTitle>Recent Activity Log</CardTitle>
                <CardDescription>Last {logs.length} events from all agents</CardDescription>
              </CardHeader>
              <CardContent>
                <ScrollArea className="h-64">
                  <div className="space-y-2">
                    {logs.length === 0 ? (
                      <p className="text-sm text-muted-foreground text-center py-8">No activity logged yet.</p>
                    ) : (
                      logs.map((log) => (
                        <div key={log.id} className="flex items-center gap-3 p-2 rounded-lg hover:bg-muted">
                          <div className={`w-2 h-2 rounded-full shrink-0 ${log.status === 'success' ? 'bg-green-500' : log.status === 'error' ? 'bg-red-500' : 'bg-yellow-500'}`} />
                          <span className="text-xs text-muted-foreground w-20 shrink-0">
                            {log.createdAt ? formatLogTime(log.createdAt) : '—'}
                          </span>
                          <Badge variant="outline" className="text-xs shrink-0 capitalize">{log.agent}</Badge>
                          <span className="text-sm truncate">{log.action.replace(/_/g, ' ')}</span>
                        </div>
                      ))
                    )}
                  </div>
                </ScrollArea>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Configuration Tab */}
          <TabsContent value="config" className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <Card>
                <CardHeader>
                  <div className="flex items-center gap-3">
                    <Database className="w-5 h-5" />
                    <CardTitle>Integrations</CardTitle>
                  </div>
                  <CardDescription>
                    Connection status for all integrated services
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <ConfigStatus name="Shopify Store" connected={status.config.shopify} />
                  <Separator />
                  <ConfigStatus name="Printful" connected={status.config.printful} />
                  <Separator />
                  <ConfigStatus name="OpenAI" connected={status.config.openai} />
                  <Separator />
                  <ConfigStatus name="Email SMTP" connected={false} />
                </CardContent>
              </Card>

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
                  <Separator />
                  <Button variant="outline" className="w-full">
                    <Database className="w-4 h-4 mr-2" />
                    Create Manual Backup
                  </Button>
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
