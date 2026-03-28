const { useState, useEffect, useCallback } = React;

// API base URL
const API_URL = window.location.origin;

// Status Card Component
const StatusCard = ({ title, status, message, icon, color }) => (
    <div className={`bg-white rounded-xl p-6 card-shadow border-l-4 ${color}`}>
        <div className="flex items-center justify-between">
            <div>
                <p className="text-gray-500 text-sm font-medium">{title}</p>
                <p className={`text-2xl font-bold mt-1 ${status === 'error' ? 'text-red-600' : 'text-gray-800'}`}>
                    {message}
                </p>
            </div>
            <div className={`text-3xl ${status === 'active' ? 'animate-pulse-slow' : ''}`}>
                {icon}
            </div>
        </div>
    </div>
);

// Agent Status Component
const AgentStatus = ({ name, status, lastAction, actions }) => (
    <div className="bg-white rounded-lg p-4 card-shadow">
        <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
                <div className={`w-3 h-3 rounded-full ${
                    status === 'working' ? 'bg-yellow-400 animate-pulse' :
                    status === 'ready' ? 'bg-green-400' :
                    status === 'error' ? 'bg-red-400' : 'bg-gray-400'
                }`} />
                <span className="font-medium text-gray-800">{name}</span>
            </div>
            <span className="text-sm text-gray-500">{actions} actions today</span>
        </div>
        {lastAction && (
            <p className="text-xs text-gray-400 mt-2">Last: {lastAction}</p>
        )}
    </div>
);

// Navigation Component
const Navigation = ({ activeTab, setActiveTab }) => {
    const tabs = [
        { id: 'dashboard', label: 'Dashboard', icon: '📊' },
        { id: 'products', label: 'Products', icon: '🎨' },
        { id: 'orders', label: 'Orders', icon: '📦' },
        { id: 'social', label: 'Social', icon: '📱' },
        { id: 'analytics', label: 'Analytics', icon: '📈' },
        { id: 'b2b', label: 'B2B', icon: '🏢' },
        { id: 'settings', label: 'Settings', icon: '⚙️' },
    ];

    return (
        <nav className="bg-white shadow-md">
            <div className="max-w-7xl mx-auto px-4">
                <div className="flex space-x-1 overflow-x-auto">
                    {tabs.map(tab => (
                        <button
                            key={tab.id}
                            onClick={() => setActiveTab(tab.id)}
                            className={`px-4 py-4 font-medium text-sm whitespace-nowrap transition-colors ${
                                activeTab === tab.id
                                    ? 'text-purple-600 border-b-2 border-purple-600'
                                    : 'text-gray-500 hover:text-gray-700'
                            }`}
                        >
                            <span className="mr-2">{tab.icon}</span>
                            {tab.label}
                        </button>
                    ))}
                </div>
            </div>
        </nav>
    );
};

// Dashboard Tab
const DashboardTab = ({ status, onGenerateProduct }) => {
    const [generating, setGenerating] = useState(false);

    const handleGenerate = async () => {
        setGenerating(true);
        await onGenerateProduct();
        setGenerating(false);
    };

    return (
        <div className="space-y-6">
            {/* Status Overview */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <StatusCard
                    title="System Status"
                    status={status?.status === 'running' ? 'active' : 'idle'}
                    message={status?.status === 'running' ? 'Running' : 'Ready'}
                    icon="✅"
                    color="border-green-500"
                />
                <StatusCard
                    title="Active Agents"
                    status="active"
                    message={`${status?.total_agents || 0} Agents`}
                    icon="🤖"
                    color="border-purple-500"
                />
                <StatusCard
                    title="System Health"
                    status={status?.system_health === 'excellent' ? 'active' : 'warning'}
                    message={status?.system_health?.toUpperCase() || 'Unknown'}
                    icon="💚"
                    color={status?.system_health === 'excellent' ? 'border-green-500' : 'border-yellow-500'}
                />
                <StatusCard
                    title="Today's Actions"
                    status="active"
                    message={Object.values(status?.agents || {}).reduce((sum, a) => sum + (a.actions_today || 0), 0)}
                    icon="⚡"
                    color="border-blue-500"
                />
            </div>

            {/* Quick Actions */}
            <div className="bg-white rounded-xl p-6 card-shadow">
                <h3 className="text-lg font-semibold text-gray-800 mb-4">Quick Actions</h3>
                <div className="flex flex-wrap gap-3">
                    <button
                        onClick={handleGenerate}
                        disabled={generating}
                        className="px-6 py-3 bg-purple-600 text-white rounded-lg font-medium hover:bg-purple-700 disabled:opacity-50 transition-colors flex items-center"
                    >
                        {generating ? (
                            <>
                                <span className="animate-spin mr-2">⏳</span>
                                Generating...
                            </>
                        ) : (
                            <>
                                <span className="mr-2">✨</span>
                                Generate New Product
                            </>
                        )}
                    </button>
                    <button className="px-6 py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-colors">
                        📱 Create Social Post
                    </button>
                    <button className="px-6 py-3 bg-green-600 text-white rounded-lg font-medium hover:bg-green-700 transition-colors">
                        📊 View Analytics
                    </button>
                </div>
            </div>

            {/* Agent Status */}
            <div className="bg-white rounded-xl p-6 card-shadow">
                <h3 className="text-lg font-semibold text-gray-800 mb-4">Agent Status</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {Object.entries(status?.agents || {}).map(([name, agent]) => (
                        <AgentStatus
                            key={name}
                            name={name.replace('_', ' ').toUpperCase()}
                            status={agent.status}
                            lastAction={agent.last_action}
                            actions={agent.actions_today}
                        />
                    ))}
                </div>
            </div>
        </div>
    );
};

// Products Tab
const ProductsTab = () => {
    const [products, setProducts] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchProducts();
    }, []);

    const fetchProducts = async () => {
        try {
            const response = await fetch(`${API_URL}/api/products`);
            const data = await response.json();
            setProducts(data.products || []);
        } catch (error) {
            console.error('Error fetching products:', error);
        } finally {
            setLoading(false);
        }
    };

    if (loading) return <div className="text-center py-10">Loading products...</div>;

    return (
        <div className="space-y-6">
            <div className="flex justify-between items-center">
                <h2 className="text-2xl font-bold text-gray-800">Products</h2>
                <button className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700">
                    + Add Product
                </button>
            </div>

            {products.length === 0 ? (
                <div className="bg-white rounded-xl p-10 text-center card-shadow">
                    <p className="text-gray-500 text-lg">No products yet. Generate your first product!</p>
                </div>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {products.map(product => (
                        <div key={product.id} className="bg-white rounded-xl overflow-hidden card-shadow">
                            <img 
                                src={product.design_url || 'https://via.placeholder.com/300'} 
                                alt={product.name}
                                className="w-full h-48 object-cover"
                            />
                            <div className="p-4">
                                <h3 className="font-semibold text-gray-800">{product.name}</h3>
                                <p className="text-sm text-gray-500 mt-1">{product.niche}</p>
                                <div className="flex justify-between items-center mt-3">
                                    <span className="text-lg font-bold text-purple-600">
                                        ${product.sale_price}
                                    </span>
                                    <span className={`px-2 py-1 rounded text-xs ${
                                        product.status === 'active' 
                                            ? 'bg-green-100 text-green-700' 
                                            : 'bg-gray-100 text-gray-600'
                                    }`}>
                                        {product.status}
                                    </span>
                                </div>
                                <div className="mt-3 text-sm text-gray-500">
                                    Sold: {product.times_sold} | Views: {product.views}
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
};

// Orders Tab
const OrdersTab = () => {
    const [orders, setOrders] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchOrders();
    }, []);

    const fetchOrders = async () => {
        try {
            const response = await fetch(`${API_URL}/api/orders`);
            const data = await response.json();
            setOrders(data.orders || []);
        } catch (error) {
            console.error('Error fetching orders:', error);
        } finally {
            setLoading(false);
        }
    };

    const getStatusColor = (status) => {
        const colors = {
            pending: 'bg-yellow-100 text-yellow-700',
            processing: 'bg-blue-100 text-blue-700',
            shipped: 'bg-purple-100 text-purple-700',
            delivered: 'bg-green-100 text-green-700',
            cancelled: 'bg-red-100 text-red-700'
        };
        return colors[status] || 'bg-gray-100 text-gray-600';
    };

    if (loading) return <div className="text-center py-10">Loading orders...</div>;

    return (
        <div className="space-y-6">
            <h2 className="text-2xl font-bold text-gray-800">Orders</h2>

            {orders.length === 0 ? (
                <div className="bg-white rounded-xl p-10 text-center card-shadow">
                    <p className="text-gray-500 text-lg">No orders yet.</p>
                </div>
            ) : (
                <div className="bg-white rounded-xl overflow-hidden card-shadow">
                    <table className="w-full">
                        <thead className="bg-gray-50">
                            <tr>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Order</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Customer</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Amount</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Date</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-200">
                            {orders.map(order => (
                                <tr key={order.id}>
                                    <td className="px-6 py-4 font-medium text-gray-800">{order.order_number}</td>
                                    <td className="px-6 py-4 text-gray-600">{order.customer_name}</td>
                                    <td className="px-6 py-4 font-medium text-gray-800">${order.total_amount}</td>
                                    <td className="px-6 py-4">
                                        <span className={`px-2 py-1 rounded text-xs ${getStatusColor(order.status)}`}>
                                            {order.status}
                                        </span>
                                    </td>
                                    <td className="px-6 py-4 text-gray-500 text-sm">
                                        {new Date(order.created_at).toLocaleDateString()}
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}
        </div>
    );
};

// Analytics Tab
const AnalyticsTab = () => {
    const [analytics, setAnalytics] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchAnalytics();
    }, []);

    const fetchAnalytics = async () => {
        try {
            const response = await fetch(`${API_URL}/api/analytics/profit`);
            const data = await response.json();
            setAnalytics(data.analytics);
        } catch (error) {
            console.error('Error fetching analytics:', error);
        } finally {
            setLoading(false);
        }
    };

    if (loading) return <div className="text-center py-10">Loading analytics...</div>;

    const summary = analytics?.summary || {};

    return (
        <div className="space-y-6">
            <h2 className="text-2xl font-bold text-gray-800">Profit Analytics</h2>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <div className="bg-white rounded-xl p-6 card-shadow">
                    <p className="text-gray-500 text-sm">Total Revenue</p>
                    <p className="text-3xl font-bold text-green-600">${summary.total_revenue?.toFixed(2) || '0.00'}</p>
                </div>
                <div className="bg-white rounded-xl p-6 card-shadow">
                    <p className="text-gray-500 text-sm">Total Profit</p>
                    <p className="text-3xl font-bold text-purple-600">${summary.total_profit?.toFixed(2) || '0.00'}</p>
                </div>
                <div className="bg-white rounded-xl p-6 card-shadow">
                    <p className="text-gray-500 text-sm">Total Orders</p>
                    <p className="text-3xl font-bold text-blue-600">{summary.total_orders || 0}</p>
                </div>
                <div className="bg-white rounded-xl p-6 card-shadow">
                    <p className="text-gray-500 text-sm">Avg Order Value</p>
                    <p className="text-3xl font-bold text-orange-600">${summary.avg_order_value?.toFixed(2) || '0.00'}</p>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div className="bg-white rounded-xl p-6 card-shadow">
                    <h3 className="text-lg font-semibold text-gray-800 mb-4">Fulfillment Stats</h3>
                    <div className="space-y-2">
                        <div className="flex justify-between">
                            <span className="text-gray-600">Pending</span>
                            <span className="font-medium">{analytics?.fulfillment?.pending || 0}</span>
                        </div>
                        <div className="flex justify-between">
                            <span className="text-gray-600">Processing</span>
                            <span className="font-medium">{analytics?.fulfillment?.processing || 0}</span>
                        </div>
                        <div className="flex justify-between">
                            <span className="text-gray-600">Shipped</span>
                            <span className="font-medium">{analytics?.fulfillment?.shipped || 0}</span>
                        </div>
                        <div className="flex justify-between">
                            <span className="text-gray-600">Delivered</span>
                            <span className="font-medium">{analytics?.fulfillment?.delivered || 0}</span>
                        </div>
                    </div>
                </div>

                <div className="bg-white rounded-xl p-6 card-shadow">
                    <h3 className="text-lg font-semibold text-gray-800 mb-4">Social Media</h3>
                    <div className="space-y-2">
                        <div className="flex justify-between">
                            <span className="text-gray-600">Total Reach</span>
                            <span className="font-medium">{analytics?.social?.total_reach?.toLocaleString() || 0}</span>
                        </div>
                        <div className="flex justify-between">
                            <span className="text-gray-600">Engagement Rate</span>
                            <span className="font-medium">{analytics?.social?.engagement_rate || 0}%</span>
                        </div>
                        <div className="flex justify-between">
                            <span className="text-gray-600">Followers Gained</span>
                            <span className="font-medium">{analytics?.social?.followers_gained || 0}</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

// Settings Tab
const SettingsTab = () => {
    const [config, setConfig] = useState({
        store_name: '',
        niche: '',
        platforms: [],
        auto_mode: true
    });
    const [saving, setSaving] = useState(false);
    const [message, setMessage] = useState('');

    const handleSave = async () => {
        setSaving(true);
        try {
            const response = await fetch(`${API_URL}/api/config`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(config)
            });
            if (response.ok) {
                setMessage('Settings saved successfully!');
            } else {
                setMessage('Error saving settings');
            }
        } catch (error) {
            setMessage('Error saving settings');
        } finally {
            setSaving(false);
            setTimeout(() => setMessage(''), 3000);
        }
    };

    return (
        <div className="space-y-6">
            <h2 className="text-2xl font-bold text-gray-800">Settings</h2>

            {message && (
                <div className="bg-green-100 text-green-700 px-4 py-3 rounded-lg">
                    {message}
                </div>
            )}

            <div className="bg-white rounded-xl p-6 card-shadow space-y-4">
                <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Store Name</label>
                    <input
                        type="text"
                        value={config.store_name}
                        onChange={(e) => setConfig({...config, store_name: e.target.value})}
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                        placeholder="My Print Store"
                    />
                </div>

                <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Niche</label>
                    <select
                        value={config.niche}
                        onChange={(e) => setConfig({...config, niche: e.target.value})}
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
                    >
                        <option value="">Select a niche</option>
                        <option value="fitness">Fitness</option>
                        <option value="pets">Pets</option>
                        <option value="travel">Travel</option>
                        <option value="food">Food</option>
                        <option value="gaming">Gaming</option>
                        <option value="music">Music</option>
                        <option value="motivation">Motivation</option>
                        <option value="funny">Funny</option>
                    </select>
                </div>

                <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Platforms</label>
                    <div className="space-x-4">
                        {['shopify', 'etsy', 'amazon'].map(platform => (
                            <label key={platform} className="inline-flex items-center">
                                <input
                                    type="checkbox"
                                    checked={config.platforms.includes(platform)}
                                    onChange={(e) => {
                                        if (e.target.checked) {
                                            setConfig({...config, platforms: [...config.platforms, platform]});
                                        } else {
                                            setConfig({...config, platforms: config.platforms.filter(p => p !== platform)});
                                        }
                                    }}
                                    className="mr-2"
                                />
                                {platform.charAt(0).toUpperCase() + platform.slice(1)}
                            </label>
                        ))}
                    </div>
                </div>

                <div>
                    <label className="inline-flex items-center">
                        <input
                            type="checkbox"
                            checked={config.auto_mode}
                            onChange={(e) => setConfig({...config, auto_mode: e.target.checked})}
                            className="mr-2"
                        />
                        Enable Auto Mode (agents run automatically)
                    </label>
                </div>

                <button
                    onClick={handleSave}
                    disabled={saving}
                    className="px-6 py-2 bg-purple-600 text-white rounded-lg font-medium hover:bg-purple-700 disabled:opacity-50"
                >
                    {saving ? 'Saving...' : 'Save Settings'}
                </button>
            </div>
        </div>
    );
};

// Main App Component
const App = () => {
    const [activeTab, setActiveTab] = useState('dashboard');
    const [status, setStatus] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchStatus();
        const interval = setInterval(fetchStatus, 30000); // Refresh every 30s
        return () => clearInterval(interval);
    }, []);

    const fetchStatus = async () => {
        try {
            const response = await fetch(`${API_URL}/api/status`);
            const data = await response.json();
            setStatus(data);
        } catch (error) {
            console.error('Error fetching status:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleGenerateProduct = async () => {
        try {
            const response = await fetch(`${API_URL}/api/products/generate`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ trending: true })
            });
            const data = await response.json();
            if (data.success) {
                alert('Product generated successfully!');
            }
        } catch (error) {
            console.error('Error generating product:', error);
            alert('Error generating product');
        }
    };

    if (loading) {
        return (
            <div className="min-h-screen flex items-center justify-center">
                <div className="text-center">
                    <div className="text-4xl mb-4">🤖</div>
                    <p className="text-gray-600">Loading PrintBot AI...</p>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gray-50">
            {/* Header */}
            <header className="gradient-bg text-white shadow-lg">
                <div className="max-w-7xl mx-auto px-4 py-6">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-3">
                            <span className="text-4xl">🤖</span>
                            <div>
                                <h1 className="text-2xl font-bold">PrintBot AI</h1>
                                <p className="text-purple-200 text-sm">Automated Print-on-Demand Store</p>
                            </div>
                        </div>
                        <div className="text-right">
                            <p className="text-sm text-purple-200">System Status</p>
                            <p className="font-semibold">{status?.status?.toUpperCase() || 'READY'}</p>
                        </div>
                    </div>
                </div>
            </header>

            {/* Navigation */}
            <Navigation activeTab={activeTab} setActiveTab={setActiveTab} />

            {/* Main Content */}
            <main className="max-w-7xl mx-auto px-4 py-8">
                {activeTab === 'dashboard' && (
                    <DashboardTab 
                        status={status} 
                        onGenerateProduct={handleGenerateProduct}
                    />
                )}
                {activeTab === 'products' && <ProductsTab />}
                {activeTab === 'orders' && <OrdersTab />}
                {activeTab === 'analytics' && <AnalyticsTab />}
                {activeTab === 'settings' && <SettingsTab />}
                {(activeTab === 'social' || activeTab === 'b2b') && (
                    <div className="bg-white rounded-xl p-10 text-center card-shadow">
                        <p className="text-gray-500 text-lg">Coming soon!</p>
                    </div>
                )}
            </main>

            {/* Footer */}
            <footer className="bg-white border-t mt-12">
                <div className="max-w-7xl mx-auto px-4 py-6">
                    <p className="text-center text-gray-500 text-sm">
                        PrintBot AI v2.0 - 11 AI Agents Working for You
                    </p>
                </div>
            </footer>
        </div>
    );
};

// Render the app
const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);
