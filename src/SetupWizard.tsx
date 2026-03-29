/**
 * PrintBot AI - Interactive Setup Wizard
 * Step-by-step guide to set up the entire system
 */

import { useState } from 'react';
import { 
  CheckCircle, 
  ChevronRight, 
  ChevronLeft,
  ExternalLink,
  Copy,
  Check,
  AlertCircle,
  Zap,
  ShoppingBag,
  Truck,
  Brain,
  Mail,
  Share2,
  DollarSign,
  Shield,
  Play,
  RefreshCw
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Progress } from '@/components/ui/progress';
import { Alert, AlertDescription } from '@/components/ui/alert';
import './App.css';

// Types
interface SetupStep {
  id: string;
  title: string;
  description: string;
  icon: any;
  isComplete: boolean;
  isOptional: boolean;
}



// Setup steps data
const setupSteps: SetupStep[] = [
  {
    id: 'welcome',
    title: 'Welcome',
    description: 'Introduction to PrintBot AI',
    icon: Zap,
    isComplete: false,
    isOptional: false
  },
  {
    id: 'shopify',
    title: 'Shopify Setup',
    description: 'Create your online store',
    icon: ShoppingBag,
    isComplete: false,
    isOptional: false
  },
  {
    id: 'printful',
    title: 'Printful Setup',
    description: 'Connect fulfillment service',
    icon: Truck,
    isComplete: false,
    isOptional: false
  },
  {
    id: 'openai',
    title: 'OpenAI Setup',
    description: 'Enable AI design generation',
    icon: Brain,
    isComplete: false,
    isOptional: false
  },
  {
    id: 'social',
    title: 'Social Media',
    description: 'Set up Instagram & TikTok',
    icon: Share2,
    isComplete: false,
    isOptional: true
  },
  {
    id: 'email',
    title: 'Email Setup',
    description: 'Configure notifications',
    icon: Mail,
    isComplete: false,
    isOptional: true
  },
  {
    id: 'configure',
    title: 'Configure System',
    description: 'Enter your API keys',
    icon: Shield,
    isComplete: false,
    isOptional: false
  },
  {
    id: 'launch',
    title: 'Launch!',
    description: 'Start your automated business',
    icon: Play,
    isComplete: false,
    isOptional: false
  }
];

// Welcome Step Component
function WelcomeStep({ onNext }: { onNext: () => void }) {
  return (
    <div className="space-y-6">
      <div className="text-center space-y-4">
        <div className="inline-flex items-center justify-center w-20 h-20 bg-gradient-to-br from-purple-500 to-pink-500 rounded-2xl">
          <Zap className="w-10 h-10 text-white" />
        </div>
        <h2 className="text-3xl font-bold">Welcome to PrintBot AI!</h2>
        <p className="text-lg text-muted-foreground max-w-lg mx-auto">
          You're about to set up an automated print-on-demand business that runs 24/7 
          with 6 AI agents working for you.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>What You'll Need</CardTitle>
          <CardDescription>Before we start, make sure you have:</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="flex items-start gap-3 p-3 bg-muted rounded-lg">
              <DollarSign className="w-5 h-5 text-green-500 mt-0.5" />
              <div>
                <p className="font-medium">~$50-80/month</p>
                <p className="text-sm text-muted-foreground">For Shopify, Printful, OpenAI</p>
              </div>
            </div>
            <div className="flex items-start gap-3 p-3 bg-muted rounded-lg">
              <ExternalLink className="w-5 h-5 text-blue-500 mt-0.5" />
              <div>
                <p className="font-medium">30-60 minutes</p>
                <p className="text-sm text-muted-foreground">To complete setup</p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Your 6 AI Agents Will:</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {[
              { icon: '🎨', text: 'Create trending designs every 30 min' },
              { icon: '💰', text: 'Optimize prices every 2 hours' },
              { icon: '📱', text: 'Post to social media every 6 hours' },
              { icon: '📦', text: 'Fulfill orders every 5 minutes' },
              { icon: '🏢', text: 'Handle B2B corporate orders' },
              { icon: '💬', text: 'Engage customers & recover carts' }
            ].map((item, i) => (
              <div key={i} className="flex items-center gap-3 p-3 bg-muted/50 rounded-lg">
                <span className="text-2xl">{item.icon}</span>
                <span className="text-sm">{item.text}</span>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      <div className="flex justify-center">
        <Button size="lg" onClick={onNext} className="gap-2">
          Let's Get Started
          <ChevronRight className="w-5 h-5" />
        </Button>
      </div>
    </div>
  );
}

// Shopify Setup Step
function ShopifyStep({ onNext, onPrev }: { onNext: () => void; onPrev: () => void }) {
  const [hasStore, setHasStore] = useState<boolean | null>(null);
  const [storeUrl, setStoreUrl] = useState('');

  return (
    <div className="space-y-6">
      <div className="text-center">
        <div className="inline-flex items-center justify-center w-16 h-16 bg-green-100 rounded-2xl mb-4">
          <ShoppingBag className="w-8 h-8 text-green-600" />
        </div>
        <h2 className="text-2xl font-bold">Step 1: Shopify Setup</h2>
        <p className="text-muted-foreground">Create your online store</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Do you have a Shopify store?</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex gap-4">
            <Button 
              variant={hasStore === true ? 'default' : 'outline'} 
              className="flex-1"
              onClick={() => setHasStore(true)}
            >
              Yes, I have one
            </Button>
            <Button 
              variant={hasStore === false ? 'default' : 'outline'} 
              className="flex-1"
              onClick={() => setHasStore(false)}
            >
              No, I need to create one
            </Button>
          </div>

          {hasStore === false && (
            <Alert>
              <AlertCircle className="w-4 h-4" />
              <AlertDescription>
                <p className="mb-2">Follow these steps:</p>
                <ol className="list-decimal list-inside space-y-1 text-sm">
                  <li>Go to <a href="https://shopify.com" target="_blank" className="text-blue-500 underline">shopify.com</a></li>
                  <li>Click "Start free trial"</li>
                  <li>Enter your email and create a store name</li>
                  <li>Complete the setup wizard</li>
                  <li>Choose the Basic plan ($29/month)</li>
                </ol>
                <Button 
                  variant="outline" 
                  className="mt-3"
                  onClick={() => window.open('https://shopify.com', '_blank')}
                >
                  <ExternalLink className="w-4 h-4 mr-2" />
                  Open Shopify
                </Button>
              </AlertDescription>
            </Alert>
          )}

          {hasStore === true && (
            <div className="space-y-4">
              <div>
                <Label>Your Shopify Store URL</Label>
                <div className="flex gap-2">
                  <Input 
                    placeholder="your-store.myshopify.com"
                    value={storeUrl}
                    onChange={(e) => setStoreUrl(e.target.value)}
                  />
                </div>
                <p className="text-xs text-muted-foreground mt-1">
                  Example: cooltees.myshopify.com
                </p>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Get Your Shopify API Key</CardTitle>
          <CardDescription>We'll need this to connect PrintBot AI</CardDescription>
        </CardHeader>
        <CardContent>
          <ol className="space-y-3 text-sm">
            <li className="flex gap-3">
              <span className="flex-shrink-0 w-6 h-6 bg-primary text-primary-foreground rounded-full flex items-center justify-center text-xs font-bold">1</span>
              <span>Log into your Shopify admin panel</span>
            </li>
            <li className="flex gap-3">
              <span className="flex-shrink-0 w-6 h-6 bg-primary text-primary-foreground rounded-full flex items-center justify-center text-xs font-bold">2</span>
              <span>Go to <strong>Settings</strong> → <strong>Apps and sales channels</strong></span>
            </li>
            <li className="flex gap-3">
              <span className="flex-shrink-0 w-6 h-6 bg-primary text-primary-foreground rounded-full flex items-center justify-center text-xs font-bold">3</span>
              <span>Click <strong>Develop apps</strong></span>
            </li>
            <li className="flex gap-3">
              <span className="flex-shrink-0 w-6 h-6 bg-primary text-primary-foreground rounded-full flex items-center justify-center text-xs font-bold">4</span>
              <span>Click <strong>Create an app</strong></span>
            </li>
            <li className="flex gap-3">
              <span className="flex-shrink-0 w-6 h-6 bg-primary text-primary-foreground rounded-full flex items-center justify-center text-xs font-bold">5</span>
              <span>Enable these permissions: <code>read_products, write_products, read_orders, write_orders, read_inventory</code></span>
            </li>
            <li className="flex gap-3">
              <span className="flex-shrink-0 w-6 h-6 bg-primary text-primary-foreground rounded-full flex items-center justify-center text-xs font-bold">6</span>
              <span>Click <strong>Install app</strong> and copy the <strong>Admin API access token</strong></span>
            </li>
          </ol>

          <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
            <p className="text-sm text-yellow-800">
              <strong>⚠️ Important:</strong> Save this token somewhere safe! You can only see it once.
            </p>
          </div>
        </CardContent>
      </Card>

      <div className="flex justify-between">
        <Button variant="outline" onClick={onPrev}>
          <ChevronLeft className="w-4 h-4 mr-2" />
          Back
        </Button>
        <Button onClick={onNext}>
          Next Step
          <ChevronRight className="w-4 h-4 ml-2" />
        </Button>
      </div>
    </div>
  );
}

// Printful Setup Step
function PrintfulStep({ onNext, onPrev }: { onNext: () => void; onPrev: () => void }) {
  return (
    <div className="space-y-6">
      <div className="text-center">
        <div className="inline-flex items-center justify-center w-16 h-16 bg-blue-100 rounded-2xl mb-4">
          <Truck className="w-8 h-8 text-blue-600" />
        </div>
        <h2 className="text-2xl font-bold">Step 2: Printful Setup</h2>
        <p className="text-muted-foreground">Connect your fulfillment service</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>What is Printful?</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground mb-4">
            Printful is a print-on-demand fulfillment service. When a customer orders from your store, 
            Printful automatically prints and ships the product. You never handle inventory!
          </p>
          <div className="grid grid-cols-3 gap-3">
            <div className="text-center p-3 bg-muted rounded-lg">
              <p className="text-2xl font-bold text-green-600">$0</p>
              <p className="text-xs text-muted-foreground">Upfront cost</p>
            </div>
            <div className="text-center p-3 bg-muted rounded-lg">
              <p className="text-2xl font-bold text-blue-600">300+</p>
              <p className="text-xs text-muted-foreground">Products</p>
            </div>
            <div className="text-center p-3 bg-muted rounded-lg">
              <p className="text-2xl font-bold text-purple-600">Global</p>
              <p className="text-xs text-muted-foreground">Shipping</p>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Create Your Printful Account</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <ol className="space-y-3 text-sm">
            <li className="flex gap-3">
              <span className="flex-shrink-0 w-6 h-6 bg-primary text-primary-foreground rounded-full flex items-center justify-center text-xs font-bold">1</span>
              <span>Go to <a href="https://printful.com" target="_blank" className="text-blue-500 underline">printful.com</a></span>
            </li>
            <li className="flex gap-3">
              <span className="flex-shrink-0 w-6 h-6 bg-primary text-primary-foreground rounded-full flex items-center justify-center text-xs font-bold">2</span>
              <span>Click <strong>Sign up</strong> and create an account</span>
            </li>
            <li className="flex gap-3">
              <span className="flex-shrink-0 w-6 h-6 bg-primary text-primary-foreground rounded-full flex items-center justify-center text-xs font-bold">3</span>
              <span>Complete your profile and connect to Shopify</span>
            </li>
          </ol>

          <Button 
            variant="outline" 
            onClick={() => window.open('https://printful.com', '_blank')}
          >
            <ExternalLink className="w-4 h-4 mr-2" />
            Open Printful
          </Button>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Get Your Printful API Key</CardTitle>
        </CardHeader>
        <CardContent>
          <ol className="space-y-3 text-sm">
            <li className="flex gap-3">
              <span className="flex-shrink-0 w-6 h-6 bg-primary text-primary-foreground rounded-full flex items-center justify-center text-xs font-bold">1</span>
              <span>Log into your Printful dashboard</span>
            </li>
            <li className="flex gap-3">
              <span className="flex-shrink-0 w-6 h-6 bg-primary text-primary-foreground rounded-full flex items-center justify-center text-xs font-bold">2</span>
              <span>Go to <strong>Settings</strong> → <strong>API</strong></span>
            </li>
            <li className="flex gap-3">
              <span className="flex-shrink-0 w-6 h-6 bg-primary text-primary-foreground rounded-full flex items-center justify-center text-xs font-bold">3</span>
              <span>Click <strong>Generate new key</strong></span>
            </li>
            <li className="flex gap-3">
              <span className="flex-shrink-0 w-6 h-6 bg-primary text-primary-foreground rounded-full flex items-center justify-center text-xs font-bold">4</span>
              <span>Copy the API key (starts with <code>pf_</code>)</span>
            </li>
          </ol>
        </CardContent>
      </Card>

      <div className="flex justify-between">
        <Button variant="outline" onClick={onPrev}>
          <ChevronLeft className="w-4 h-4 mr-2" />
          Back
        </Button>
        <Button onClick={onNext}>
          Next Step
          <ChevronRight className="w-4 h-4 ml-2" />
        </Button>
      </div>
    </div>
  );
}

// OpenAI Setup Step
function OpenAIStep({ onNext, onPrev }: { onNext: () => void; onPrev: () => void }) {
  return (
    <div className="space-y-6">
      <div className="text-center">
        <div className="inline-flex items-center justify-center w-16 h-16 bg-purple-100 rounded-2xl mb-4">
          <Brain className="w-8 h-8 text-purple-600" />
        </div>
        <h2 className="text-2xl font-bold">Step 3: OpenAI Setup</h2>
        <p className="text-muted-foreground">Enable AI-powered design generation</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>What You'll Get</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="p-4 bg-gradient-to-br from-purple-50 to-pink-50 rounded-lg">
              <p className="text-2xl mb-2">🎨</p>
              <p className="font-medium">AI Designs</p>
              <p className="text-xs text-muted-foreground">DALL-E 3 generates unique designs</p>
            </div>
            <div className="p-4 bg-gradient-to-br from-blue-50 to-cyan-50 rounded-lg">
              <p className="text-2xl mb-2">✍️</p>
              <p className="font-medium">Auto Content</p>
              <p className="text-xs text-muted-foreground">GPT-4 writes product descriptions</p>
            </div>
            <div className="p-4 bg-gradient-to-br from-green-50 to-emerald-50 rounded-lg">
              <p className="text-2xl mb-2">💬</p>
              <p className="font-medium">Chatbot</p>
              <p className="text-xs text-muted-foreground">AI handles customer service</p>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Get Your OpenAI API Key</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <ol className="space-y-3 text-sm">
            <li className="flex gap-3">
              <span className="flex-shrink-0 w-6 h-6 bg-primary text-primary-foreground rounded-full flex items-center justify-center text-xs font-bold">1</span>
              <span>Go to <a href="https://platform.openai.com" target="_blank" className="text-blue-500 underline">platform.openai.com</a></span>
            </li>
            <li className="flex gap-3">
              <span className="flex-shrink-0 w-6 h-6 bg-primary text-primary-foreground rounded-full flex items-center justify-center text-xs font-bold">2</span>
              <span>Sign up or log in</span>
            </li>
            <li className="flex gap-3">
              <span className="flex-shrink-0 w-6 h-6 bg-primary text-primary-foreground rounded-full flex items-center justify-center text-xs font-bold">3</span>
              <span>Go to <strong>API keys</strong> in the left sidebar</span>
            </li>
            <li className="flex gap-3">
              <span className="flex-shrink-0 w-6 h-6 bg-primary text-primary-foreground rounded-full flex items-center justify-center text-xs font-bold">4</span>
              <span>Click <strong>Create new secret key</strong></span>
            </li>
            <li className="flex gap-3">
              <span className="flex-shrink-0 w-6 h-6 bg-primary text-primary-foreground rounded-full flex items-center justify-center text-xs font-bold">5</span>
              <span>Copy the key (starts with <code>sk-</code>)</span>
            </li>
          </ol>

          <Button 
            variant="outline" 
            onClick={() => window.open('https://platform.openai.com/api-keys', '_blank')}
          >
            <ExternalLink className="w-4 h-4 mr-2" />
            Open OpenAI
          </Button>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Add Credits</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground mb-4">
            OpenAI charges per use. For a typical month with PrintBot AI:
          </p>
          <div className="space-y-2">
            <div className="flex justify-between p-2 bg-muted rounded">
              <span className="text-sm">~90 designs (DALL-E)</span>
              <span className="text-sm font-medium">~$27</span>
            </div>
            <div className="flex justify-between p-2 bg-muted rounded">
              <span className="text-sm">Content generation (GPT-4)</span>
              <span className="text-sm font-medium">~$10</span>
            </div>
            <div className="flex justify-between p-2 bg-green-50 rounded border border-green-200">
              <span className="text-sm font-medium">Total estimated</span>
              <span className="text-sm font-bold text-green-600">~$20-40/month</span>
            </div>
          </div>
          <p className="text-xs text-muted-foreground mt-3">
            Go to <strong>Billing</strong> → <strong>Add to credit balance</strong> and add at least $20
          </p>
        </CardContent>
      </Card>

      <div className="flex justify-between">
        <Button variant="outline" onClick={onPrev}>
          <ChevronLeft className="w-4 h-4 mr-2" />
          Back
        </Button>
        <Button onClick={onNext}>
          Next Step
          <ChevronRight className="w-4 h-4 ml-2" />
        </Button>
      </div>
    </div>
  );
}

// Configure Step - Enter API Keys
function ConfigureStep({ onNext, onPrev }: { onNext: () => void; onPrev: () => void }) {
  const [apiKeys, setApiKeys] = useState({
    shopifyUrl: '',
    shopifyToken: '',
    printfulKey: '',
    openaiKey: ''
  });
  const [copied, setCopied] = useState<string | null>(null);

  const copyToClipboard = (text: string, label: string) => {
    navigator.clipboard.writeText(text);
    setCopied(label);
    setTimeout(() => setCopied(null), 2000);
  };

  const generateEnvFile = () => {
    return `# PrintBot AI - Environment Configuration
SHOPIFY_SHOP_URL=${apiKeys.shopifyUrl}
SHOPIFY_ACCESS_TOKEN=${apiKeys.shopifyToken}
PRINTFUL_API_KEY=${apiKeys.printfulKey}
OPENAI_API_KEY=${apiKeys.openaiKey}
`;
  };

  return (
    <div className="space-y-6">
      <div className="text-center">
        <div className="inline-flex items-center justify-center w-16 h-16 bg-gray-100 rounded-2xl mb-4">
          <Shield className="w-8 h-8 text-gray-600" />
        </div>
        <h2 className="text-2xl font-bold">Configure Your System</h2>
        <p className="text-muted-foreground">Enter your API keys</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Enter Your API Keys</CardTitle>
          <CardDescription>These are stored locally on your computer</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <Label>Shopify Store URL</Label>
            <Input 
              placeholder="your-store.myshopify.com"
              value={apiKeys.shopifyUrl}
              onChange={(e) => setApiKeys({...apiKeys, shopifyUrl: e.target.value})}
            />
          </div>
          <div>
            <Label>Shopify Admin API Token</Label>
            <Input 
              type="password"
              placeholder="shpat_xxxxxxxxxxxx"
              value={apiKeys.shopifyToken}
              onChange={(e) => setApiKeys({...apiKeys, shopifyToken: e.target.value})}
            />
          </div>
          <div>
            <Label>Printful API Key</Label>
            <Input 
              type="password"
              placeholder="pf_xxxxxxxxxxxx"
              value={apiKeys.printfulKey}
              onChange={(e) => setApiKeys({...apiKeys, printfulKey: e.target.value})}
            />
          </div>
          <div>
            <Label>OpenAI API Key</Label>
            <Input 
              type="password"
              placeholder="sk-xxxxxxxxxxxx"
              value={apiKeys.openaiKey}
              onChange={(e) => setApiKeys({...apiKeys, openaiKey: e.target.value})}
            />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Save Your Configuration</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-sm text-muted-foreground">
            Copy this content and save it as <code>.env</code> in your PrintBot AI folder:
          </p>
          
          <div className="relative">
            <pre className="p-4 bg-muted rounded-lg text-xs overflow-x-auto">
              {generateEnvFile()}
            </pre>
            <Button 
              size="sm" 
              variant="outline"
              className="absolute top-2 right-2"
              onClick={() => copyToClipboard(generateEnvFile(), 'env')}
            >
              {copied === 'env' ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
            </Button>
          </div>

          <Alert>
            <AlertCircle className="w-4 h-4" />
            <AlertDescription>
              Save this file as <code>.env</code> in the same folder as <code>start.py</code>
            </AlertDescription>
          </Alert>
        </CardContent>
      </Card>

      <div className="flex justify-between">
        <Button variant="outline" onClick={onPrev}>
          <ChevronLeft className="w-4 h-4 mr-2" />
          Back
        </Button>
        <Button onClick={onNext} disabled={!apiKeys.shopifyUrl || !apiKeys.shopifyToken || !apiKeys.printfulKey || !apiKeys.openaiKey}>
          Next Step
          <ChevronRight className="w-4 h-4 ml-2" />
        </Button>
      </div>
    </div>
  );
}

// Launch Step
function LaunchStep({ onRestart }: { onRestart: () => void }) {
  return (
    <div className="space-y-6">
      <div className="text-center">
        <div className="inline-flex items-center justify-center w-20 h-20 bg-green-100 rounded-2xl mb-4">
          <Play className="w-10 h-10 text-green-600" />
        </div>
        <h2 className="text-3xl font-bold">You're Ready to Launch!</h2>
        <p className="text-muted-foreground">Your automated business is configured</p>
      </div>

      <Card className="bg-gradient-to-br from-green-50 to-emerald-50 border-green-200">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <CheckCircle className="w-5 h-5 text-green-600" />
            Setup Complete!
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="flex items-center gap-2">
                <CheckCircle className="w-5 h-5 text-green-500" />
                <span className="text-sm">Shopify connected</span>
              </div>
              <div className="flex items-center gap-2">
                <CheckCircle className="w-5 h-5 text-green-500" />
                <span className="text-sm">Printful connected</span>
              </div>
              <div className="flex items-center gap-2">
                <CheckCircle className="w-5 h-5 text-green-500" />
                <span className="text-sm">OpenAI connected</span>
              </div>
              <div className="flex items-center gap-2">
                <CheckCircle className="w-5 h-5 text-green-500" />
                <span className="text-sm">6 AI agents ready</span>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Start PrintBot AI</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-sm text-muted-foreground">
            Open your terminal/command prompt and run:
          </p>
          
          <div className="relative">
            <pre className="p-4 bg-gray-900 text-green-400 rounded-lg font-mono text-sm">
              cd printbot-ai
python start.py --setup
python start.py
            </pre>
            <Button 
              size="sm" 
              variant="outline"
              className="absolute top-2 right-2 bg-gray-800 border-gray-700"
              onClick={() => {
                navigator.clipboard.writeText('cd printbot-ai\npython start.py --setup\npython start.py');
              }}
            >
              <Copy className="w-4 h-4" />
            </Button>
          </div>

          <div className="space-y-2">
            <p className="text-sm font-medium">Then open:</p>
            <div className="flex gap-2">
              <code className="px-3 py-2 bg-muted rounded text-sm flex-1">
                http://localhost:8080
              </code>
              <Button 
                size="sm" 
                variant="outline"
                onClick={() => window.open('http://localhost:8080', '_blank')}
              >
                <ExternalLink className="w-4 h-4" />
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>What's Next?</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            <div className="flex items-start gap-3 p-3 bg-muted rounded-lg">
              <span className="text-xl">1️⃣</span>
              <div>
                <p className="font-medium">Review First Designs</p>
                <p className="text-sm text-muted-foreground">Manually approve the first 10 designs to ensure quality</p>
              </div>
            </div>
            <div className="flex items-start gap-3 p-3 bg-muted rounded-lg">
              <span className="text-xl">2️⃣</span>
              <div>
                <p className="font-medium">Check In Daily</p>
                <p className="text-sm text-muted-foreground">Click "Check In" button every 24 hours</p>
              </div>
            </div>
            <div className="flex items-start gap-3 p-3 bg-muted rounded-lg">
              <span className="text-xl">3️⃣</span>
              <div>
                <p className="font-medium">Monitor Dashboard</p>
                <p className="text-sm text-muted-foreground">Watch revenue, orders, and agent status</p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      <div className="flex justify-center gap-4">
        <Button variant="outline" onClick={onRestart}>
          <RefreshCw className="w-4 h-4 mr-2" />
          Start Over
        </Button>
        <Button onClick={() => window.open('http://localhost:8080', '_blank')}>
          <ExternalLink className="w-4 h-4 mr-2" />
          Open Dashboard
        </Button>
      </div>
    </div>
  );
}

// Main Setup Wizard Component
function SetupWizard() {
  const [currentStep, setCurrentStep] = useState(0);
  const [completedSteps, setCompletedSteps] = useState<Set<string>>(new Set());

  const totalSteps = setupSteps.length;
  const progress = ((currentStep + 1) / totalSteps) * 100;

  const handleNext = () => {
    if (currentStep < totalSteps - 1) {
      setCompletedSteps(prev => new Set([...prev, setupSteps[currentStep].id]));
      setCurrentStep(currentStep + 1);
    }
  };

  const handlePrev = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  const handleRestart = () => {
    setCurrentStep(0);
    setCompletedSteps(new Set());
  };

  const renderStep = () => {
    switch (setupSteps[currentStep].id) {
      case 'welcome':
        return <WelcomeStep onNext={handleNext} />;
      case 'shopify':
        return <ShopifyStep onNext={handleNext} onPrev={handlePrev} />;
      case 'printful':
        return <PrintfulStep onNext={handleNext} onPrev={handlePrev} />;
      case 'openai':
        return <OpenAIStep onNext={handleNext} onPrev={handlePrev} />;
      case 'configure':
        return <ConfigureStep onNext={handleNext} onPrev={handlePrev} />;
      case 'launch':
        return <LaunchStep onRestart={handleRestart} />;
      default:
        return (
          <div className="text-center py-12">
            <p className="text-muted-foreground">This step is coming soon!</p>
            <div className="flex justify-center gap-4 mt-6">
              <Button variant="outline" onClick={handlePrev}>
                <ChevronLeft className="w-4 h-4 mr-2" />
                Back
              </Button>
              <Button onClick={handleNext}>
                Next Step
                <ChevronRight className="w-4 h-4 ml-2" />
              </Button>
            </div>
          </div>
        );
    }
  };

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
                <h1 className="text-xl font-bold">PrintBot AI Setup</h1>
                <p className="text-xs text-muted-foreground">Step {currentStep + 1} of {totalSteps}</p>
              </div>
            </div>
            <div className="w-32">
              <Progress value={progress} className="h-2" />
            </div>
          </div>
        </div>
      </header>

      {/* Progress Steps */}
      <div className="border-b bg-muted/50">
        <div className="container mx-auto px-4 py-4">
          <div className="flex gap-2 overflow-x-auto pb-2">
            {setupSteps.map((step, index) => {
              const Icon = step.icon;
              const isActive = index === currentStep;
              const isCompleted = completedSteps.has(step.id);
              
              return (
                <div 
                  key={step.id}
                  className={`flex items-center gap-2 px-3 py-2 rounded-lg whitespace-nowrap ${
                    isActive ? 'bg-primary text-primary-foreground' : 
                    isCompleted ? 'bg-green-100 text-green-700' : 'bg-muted'
                  }`}
                >
                  {isCompleted ? (
                    <CheckCircle className="w-4 h-4" />
                  ) : (
                    <Icon className="w-4 h-4" />
                  )}
                  <span className="text-sm font-medium">{step.title}</span>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8 max-w-3xl">
        <Card>
          <CardContent className="p-6">
            {renderStep()}
          </CardContent>
        </Card>
      </main>

      {/* Footer */}
      <footer className="border-t bg-card mt-auto">
        <div className="container mx-auto px-4 py-4 text-center text-sm text-muted-foreground">
          Need help? Check the documentation or contact support.
        </div>
      </footer>
    </div>
  );
}

export default SetupWizard;
