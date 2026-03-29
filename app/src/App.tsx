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
  Heart
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
            <Button className="w-full" variant="outline">
              <CheckCircle className="w-4 h-4 mr-2" />
              Check In Now
            </Button>
          </>
        )}
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

function App() {
  const [status] = useState<SystemStatus>(mockSystemStatus);
  const [analytics] = useState<Analytics>(mockAnalytics);
  const [activeTab, setActiveTab] = useState('dashboard');

  useEffect(() => {
    const interval = setInterval(() => {
      // Poll /api/status
    }, 5000);
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
